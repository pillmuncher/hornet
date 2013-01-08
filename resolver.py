from collections import Counter, OrderedDict, defaultdict
from copy import deepcopy
from inspect import signature
import expressions
from util import (noop, identity, as_method, is_var_name, params_format,
                  body_format, amp_separated, comma_separated, next_suffix,
                  first_param, second_param, first_goal, second_goal)


class UnificationFailed(Exception):
    pass


class Term:

    __slots__ = 'env', 'name'

    def __init__(self, env, name):
        self.env = env
        self.name = name

    def __iter__(self):
        yield self

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self)

    def __call__(self):
        return self.name

    def direct(self, compiler):
        return self

    deref = property(identity)


class Variable(Term):

    __slots__ = 'alias'

    def __init__(self, env, name):
        self.alias = Counter()
        super().__init__(env, name)

    def __str__(self):
        return str(self.deref if self.deref != self else self.name)

    @property
    def deref(self):
        return self.env[self.name]

    @deref.setter
    def ref(self, term):
        self.env[self.name] = term

    def __deepcopy__(self, memo):
        env = deepcopy(self.env, memo)
        for i in range(1000):
            suffix = next_suffix()
            if self.name + suffix not in env:
                new = env[self.name + suffix]
                break
        else:
            raise ValueError('Couldn\'t create new unique name for Variable.')
        if isinstance(self.deref, NonVariable):
            new.ref = deepcopy(self.deref)
        return new

    def __call__(self):
        raise TypeError('Unbound Variables can\'t be evaluated.')

    def unify(self, other, trail):
        other.unify_variable(self, trail)

    def unify_variable(self, other, trail):
        @trail
        def rollback(self=self, other=other, deref=other.deref):
            self.alias[other] -= 1
            other.alias[self] -= 1
            other.ref = deref
        self.alias[other] += 1
        other.alias[self] += 1
        other.ref = self

    def unify_nonvariable(self, nonvariable, trail):
        variables = []
        seen = set()
        todo = set(self)
        while todo:
            variable = todo.pop()
            seen.add(variable)
            todo |= (+variable.alias).keys() - seen
            variable.ref = nonvariable
            variables.append(variable)
        @trail
        def rollback(variables=variables):
            for variable in reversed(variables):
                variable.ref = variable


class AnonymousVariable(Term):

    __slots__ = ()

    deref = property(identity)
    ref = deref.setter(noop)
    __deepcopy__ = lambda self, memo: self

    unify = noop
    unify_variable = noop
    unify_nonvariable = noop


class NonVariable(Term):

    __slots__ = 'params', 'goals', 'actions'

    def __init__(self, *args, **kwargs):
        self.params = kwargs.pop('params', ())
        self.goals = kwargs.pop('goals', ())
        self.actions = kwargs.pop('actions', noop)
        super().__init__(*args, **kwargs)

    @property
    def arity(self):
        return len(self.params)

    @property
    def indicator(self):
        return self.name, self.arity

    def __neg__(self):
        return expressions.Consequence(self)

    def __deepcopy__(self, memo):
        return NonVariable(
            deepcopy(self.env, memo),
            self.name,
            params=tuple(deepcopy(param, memo) for param in self.params),
            goals=tuple(deepcopy(goal, memo) for goal in self.goals))


    def action(self, *args, **kwargs):
        for each in self.actions:
            each(*args, **kwargs)

    def unify(self, other, trail):
        other.unify_nonvariable(self, trail)

    def unify_variable(self, variable, trail):
        variable.unify_nonvariable(self, trail)

    def unify_nonvariable(self, other, trail):
        if self.name != other.name or self.arity != other.arity:
            raise UnificationFailed
        for left, right in zip(self.params, other.params):
            unify(left, right, trail)

    def __str__(self):
        return ''.join((
            str(self.name),
            params_format(each.deref for each in self.params),
            body_format(self.goals)))


class BinaryOperator(NonVariable):
    left = property(first_param)
    right = property(second_param)

    def __str__(self):
        return ' {} '.format(self.name).join(map(str, self.params))


class Conjunction(BinaryOperator):

    __slots__ = ()

    def __iter__(self):
        for each in self.params:
            yield from each


class Subtraction(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() - self.right.deref()


class List(NonVariable):

    head = property(first_param)
    tail = property(second_param)

    __slots__ = ()

    def __str__(self):
        acc = []
        while isinstance(self, List):
            acc.append(str(self.head.deref))
            self = self.tail.deref
        if isinstance(self, Nil):
            return '[{}]'.format(comma_separated(acc))
        return '[{}|{}]'.format(comma_separated(acc), self)


class Nil(NonVariable):

    __slots__ = ()

    def __str__(self):
        return '[]'


def unify(left, right, trail):
    left.deref.unify(right.deref, trail)


class Environment(dict):

    def Variable(self, name, *, Type=None, params=(), goals=(), actions=()):
        return self[name]

    Atom = as_method(NonVariable, expressions.Atom)
    Relation = as_method(NonVariable, expressions.Relation)
    Rule = as_method(NonVariable, expressions.Rule)
    Conjunction = as_method(Conjunction)
    Subtraction = as_method(Subtraction)
    List = as_method(List)
    Nil = as_method(Nil)
    Int = Atom
    Float = Atom
    DCGRule = Rule

    @property
    @as_method
    class proxy:

        def __init__(self, env):
            self.env = env

        def __getattr__(self, name):
            return self.env.get(name)

    def __missing__(self, name):
        name = str(name)
        if not is_var_name(name):
            raise ValueError('Variable names must start with an upper '
                             'case letter or "_", not {0}'.format(name[0]))
        if name == '_':
            return AnonymousVariable(self, '_')
        var = self[name] = Variable(self, name)
        return var

    def __deepcopy__(self, memo):
        return Environment()

    def __call__(self, name, Type, params, goals, actions):
        return getattr(self, Type.__name__)(
            name=name,
            Type=Type,
            params=params,
            goals=goals,
            actions=actions)

class Cut(Exception):

    def __init__(self, cut_parent):
        self.parent = cut_parent

    def __str__(self):
        return 'Cut(%d)' % self.parent


class Trail(list):

    def __enter__(self):
        self.append([])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for rollback in reversed(self.pop()):
            rollback()

    def __call__(self, item):
        self[-1].append(item)


Assertable = expressions.Atom, expressions.Relation, expressions.Rule, expressions.DCGRule


class Database(OrderedDict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indicators = defaultdict(set)
        import system
        self.consult(system.predicates)

    def __missing__(self, indicator):
        predicate = self[indicator] = []
        return predicate

    def assertz(self, *clauses):
        for clause in clauses:
            if not isinstance(clause, Assertable):
                raise TypeError('{} objects can\'t be asserted.'.format(
                    type(clause).__name__))
        for clause in clauses:
            self.indicators[clause.name].add(clause.indicator)
            self[clause.name, clause.arity].append(clause)
        return self

    def compile(self, expression):
        return expression.direct(Environment())

    def consult(self, module):
        names = iter(signature(module).parameters)
        next(names)
        return module(self, *map(expressions.unit, names))

    def resolve(self, goals, cut_parent=0, trail=Trail()):
        try:
            goal, *goals = goals
        except ValueError:
            yield {}
            return
        for clause in map(self.compile, self.get(goal.deref.indicator, ())):
            try:
                with trail:
                    unify(goal, clause, trail)
                    for each in self.resolve(clause.goals, cut_parent + 1):
                        clause.action(clause, clause.env.proxy, self, trail)
                        goal.deref.action(goal.deref, goal.env.proxy, self, trail)
                        for each in self.resolve(goals, cut_parent):
                            yield goal.env
            except UnificationFailed:
                continue
            except Cut as cut:
                if cut.parent == cut_parent:
                    raise
                break
            finally:
                clause.env.clear()
        if goal.deref.name == 'cut':
            raise Cut(cut_parent)
