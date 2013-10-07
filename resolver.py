from collections import Counter, OrderedDict, defaultdict
from functools import wraps
from inspect import signature
import expressions
from util import (noop, identity, as_method, is_var_name, params_format,
                  body_format, amp_separated, comma_separated, next_suffix,
                  first_param, second_param)


class UnificationFailed(Exception):
    pass


class Term(expressions.BaseExpression):

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

    def __init__(self, *args):
        self.alias = Counter()
        super().__init__(*args)

    def __str__(self):
        return str(self.deref if self.deref != self else self.name)

    @property
    def deref(self):
        return self.env[self.name]

    @deref.setter
    def ref(self, term):
        self.env[self.name] = term

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


class Wildcard(Term):

    __slots__ = ()

    deref = property(identity)
    ref = deref.setter(noop)

    unify = noop
    unify_variable = noop
    unify_nonvariable = noop


class Structure(Term):

    __slots__ = 'params', 'goals', 'actions'

    def __init__(self, *args, params=(), goals=(), actions=noop, **kwargs):
        self.params = params
        self.goals = goals
        self.actions = actions
        super().__init__(*args, **kwargs)

    @property
    def arity(self):
        return len(self.params)

    @property
    def indicator(self):
        return self.name, self.arity

    def action(self, *args, **kwargs):
        for each in self.actions:
            each(self, *args, **kwargs)

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


class Atom(Structure):
    pass


class DCGStructure(Structure):
    pass


class UnaryOperator(Structure):
    term = property(first_param)

    def __str__(self):
        return '{}{}'.format(self.name, self.term)


class BinaryOperator(Structure):
    left = property(first_param)
    right = property(second_param)

    def __str__(self):
        return '({} {} {})'.format(self.left, self.name, self.right)


class Conjunction(BinaryOperator):

    __slots__ = ()

    def __iter__(self):
        for each in self.params:
            yield from each


class Negation(UnaryOperator):

    __slots__ = ()

    def __call__(self):
        return -self.term.deref()


class Addition(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() + self.right.deref()


class Subtraction(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() - self.right.deref()


class Multiplication(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() * self.right.deref()


class Division(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() / self.right.deref()


class Remainder(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() % self.right.deref()


class Exponentiation(BinaryOperator):

    __slots__ = ()

    def __call__(self):
        return self.left.deref() ** self.right.deref()


class List(Structure):

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

    def __call__(self):
        #return self
        acc = []
        while isinstance(self, List):
            acc.append(self.head.deref())
            self = self.tail.deref
        return acc if isinstance(self, Nil) else acc + [self]


class Nil(Structure):

    __slots__ = ()

    def __str__(self):
        return '[]'

    def __call__(self):
        return []


def unify(left, right, trail):
    left.deref.unify(right.deref, trail)


class Environment(dict):

    def Variable(self, name, **kwargs):
        return self[name]

    Wildcard = as_method(Wildcard)
    Atom = as_method(Atom)
    Relation = as_method(Structure, expressions.Relation)
    Rule = as_method(Structure, expressions.Rule)
    DCGRule = as_method(DCGStructure, expressions.DCGRule)
    Conjunction = as_method(Conjunction)
    Negation = as_method(Negation)
    Addition = as_method(Addition)
    Subtraction = as_method(Subtraction)
    Multiplication = as_method(Multiplication)
    Division = as_method(Division)
    Remainder = as_method(Remainder)
    Exponentiation = as_method(Exponentiation)
    List = as_method(List)
    Nil = as_method(Nil)
    Int = Atom
    Float = Atom

    @property
    @as_method
    class proxy:

        def __init__(self, env):
            self.env = env

        def __getattr__(self, name):
            return self.env.get(name)

        def __call__(self):
            return self.env

    def __missing__(self, name):
        name = str(name)
        if not is_var_name(name):
            raise ValueError('Variable names must start with an upper '
                             'case letter or "_", not {0}'.format(name[0]))
        if name == '_':
            return self.Wildcard('_')
        var = self[name] = Variable(self, name)
        return var


class Cut(Exception):

    def __init__(self, cut_parent):
        self.parent = cut_parent

    def __str__(self):
        return 'Cut(%d)' % self.parent


class Trail(list):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for rollback in reversed(self):
            rollback()

    def __call__(self, undo):
        self.append(undo)
        return undo


Assertable = (
    expressions.Atom,
    expressions.Relation,
    expressions.Rule,
    expressions.DCGRule,
)


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
        clauses = list(clauses)
        for i, clause in enumerate(clauses):
            if callable(clause) and not isinstance(clause, expressions.Expression):
                clauses[i] = expressions.make_pyfunc(clause)
            elif not isinstance(clause, Assertable):
                raise TypeError("{} objects can't be asserted.".format(
                    type(clause).__name__))
        for clause in clauses:
            self.indicators[clause.name].add(clause.indicator)
            self[clause.name, clause.arity].append(clause)
        return self

    def consult(self, prolog_module_function):
        names = iter(signature(prolog_module_function).parameters)
        next(names)
        return prolog_module_function(self, *map(expressions.unit, names))

    @staticmethod
    def compile(expression):
        return expression.direct(Environment())

    def resolve(self, goals):
        def _resolve(goals, cut_parent, db=self):
            try:
                goal, *goals = goals
            except ValueError:
                yield {}
                return
            for clause in map(db.compile, db.get(goal.deref.indicator, ())):
                try:
                    with Trail() as trail:
                        unify(goal, clause, trail)
                        for _ in _resolve(clause.goals, cut_parent + 1):
                            clause.action(clause.env.proxy, self, trail)
                            goal.deref.action(goal.env.proxy, self, trail)
                            for _ in _resolve(goals, cut_parent):
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
        return _resolve(goals, cut_parent=0)

    def query(self, term):
        return self.resolve(self.compile(term))


def hornet(module_function):
    @wraps(module_function)
    def consult_into(db):
        return db.consult(module_function)
    return consult_into

