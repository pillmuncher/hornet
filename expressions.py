from functools import wraps, reduce
from inspect import signature
from operator import xor
from util import (params_format, body_format, comma_separated, amp_separated,
                  is_var_name, flip, identity, compose, next_suffix, as_method,
                  first_param, second_param)


def invoke(fn, Type=type):
    @wraps(fn)
    def wrapper(term, *args):
        return term.bind(fn(Type(term), *args))
    return wrapper


def unit(name, *, Type=None, **kwargs):
    if Type:
        return Type(name, Type=Type, **kwargs)
    elif is_var_name(name):
        return Variable(name, **kwargs)
    else:
        return Atom(name, **kwargs)


def add_params(NewType, *newparams):
    if not newparams:
        raise ValueError
    def new(params, **kwargs):
        return NewType(params=params + list(newparams), **kwargs)
    return new


def add_goal(NewType, goal):
    def new(goals, **kwargs):
        return NewType(goals=goals + [goal], **kwargs)
    return new


def add_action(NewType, action):
    def new(actions, **kwargs):
        return NewType(actions=actions + [action], **kwargs)
    return new


def add_dcg_params(NewType, goal):
    def new(params, **kwargs):
        v = Variable(next_suffix())
        return NewType(params=params + [v, v], **kwargs
                      ).bind(add_dcg_goal(NewType, wrap(goal)))
    return new


def add_dcg_goal(NewType, goal):
    if isinstance(goal, ExplicitDCGGoal):
        def new(goals, **kwargs):
            return NewType(goals=goals + list(goal.params), **kwargs)
    elif isinstance(goal, List):
        def new(params, goals, **kwargs):
            for each in goal:
                v1 = params[-1]
                v2 = params[-1] = Variable(next_suffix())
            return NewType(
                params=params,
                goals=goals + [_C_(v1, each, v2)],
                **kwargs)
    else:
        def new(params, goals, **kwargs):
            v1 = params[-1]
            v2 = params[-1] = Variable(next_suffix())
            return NewType(
                params=params,
                goals=goals + [goal.bind(add_params(Relation, v1, v2))],
                **kwargs)
    return new


def make_conjunction(left, right):
    return Conjunction(params=(left, right))


def make_subtraction(left, right):
    return Subtraction(params=(left, right))


def make_list(head, tail):
    return List(params=(head, tail))


def make_tail_pair(head, tail=None):
    return TailPair(params=(head, nil if tail is None else tail))


class Consequence(object):

    def __init__(self, term):
        self.term = term

    def __and__(self, term):
        return Consequence(self.term & term)

    def __ror__(self, db):
        return db.resolve(db.compile(self.term))


class BaseTerm:
    pass


class Term(BaseTerm):

    def __init__(self, name, *, Type=None, params=(), goals=(), actions=()):
        self.name = name
        self.params = tuple(map(wrap, params))
        self.goals = tuple(map(wrap, goals))
        self.actions = tuple(actions)

    @property
    def arity(self):
        return len(self.params)

    @property
    def indicator(self):
        return self.name, self.arity

    def bind(self, fn):
        return fn(
            name=self.name,
            Type=type(self),
            params=list(self.params),
            goals=list(self.goals),
            actions=list(self.actions))

    def direct(self, compiler):
        return getattr(compiler, type(self).__name__)(
            self.name,
            params=[term.direct(compiler) for term in self.params],
            goals=[term.direct(compiler) for term in self.goals],
            actions=list(self.actions))

    __and__ = make_conjunction
    __or__ = make_tail_pair
    __ror__ = flip(make_tail_pair)
    __sub__ = make_subtraction
    __rsub__ = flip(make_subtraction)
    __neg__ = as_method(Consequence)
    __getitem__ = invoke(add_action)

    def __iter__(self):
        yield self

    def __eq__(self, other):
        return (
            type(self) is type(other) and
            self.name == other.name and
            self.params == other.params and
            self.goals == other.goals)

    def __hash__(self):
        return (
            reduce(xor, map(hash, self.params), hash(type(self))) ^
            reduce(xor, map(hash, self.goals), hash(self.name)))

    def __repr__(self):
        return str(self)

    def __str__(self):
        return ''.join((
            str(self.name),
            params_format(map(str, self.params)),
            body_format(map(str, self.goals)),
            '[{}]'.format(comma_separated(self.actions)) if self.actions else ''))


class Variable(Term):

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))


class Atom(Term):
    __call__ = invoke(add_params, lambda _: Relation)
    __lshift__ = invoke(add_goal, lambda _: Rule)
    __rshift__ = invoke(add_dcg_params, lambda _: DCGRule)


class Relation(Term):
    __lshift__ = invoke(add_goal, lambda _: Rule)
    __rshift__ = invoke(add_dcg_params, lambda _: DCGRule)


class Rule(Term):
    __and__ = invoke(add_goal)


class DCGRule(Term):
    __and__ = invoke(add_dcg_goal)


class ExplicitDCGGoal(Term):
    def __init__(self, name='unused', **kwargs):
        super().__init__('.explicit.', **kwargs)


class BinaryOperator(Term):

    _name = ''

    left = property(first_param)
    right = property(second_param)

    def __init__(self, name=None, **kwargs):
        super().__init__(name=self._name, **kwargs)

    def __iter__(self):
        for each in self.params:
            yield from each

    def __str__(self):
        return ' {} '.format(self.name).join(map(str, self.params))


class Conjunction(BinaryOperator):
    _name = '&'
    __and__ = invoke(add_params)


class Subtraction(BinaryOperator):
    _name = '-'
    __sub__ = make_subtraction
    __rsub__ = flip(make_subtraction)


class List(BinaryOperator):

    _name = '.'

    head = BinaryOperator.left
    tail = BinaryOperator.right

    def __str__(self):
        acc = []
        while isinstance(self, List):
            acc.append(str(self.head))
            self = self.tail
        if isinstance(self, Nil):
            return '[{}]'.format(comma_separated(map(str, acc)))
        return '[{}|{}]'.format(comma_separated(map(str, acc)), str(self))


class TailPair(List):

    def __or__(self, other):
        raise TypeError

    def __str__(self):
        return ' | '.join(map(str, self.params))


class Nil(Term):

    def __init__(self):
        super().__init__('[]')

    def __iter__(self):
        return
        yield

    def __str__(self):
        return '[]'


def new_list(alist, tail=None):
    alist = list(alist)
    if not alist:
        return nil
    last = alist[-1]
    if isinstance(last, TailPair):
        if tail is not None:
            raise TypeError('List objects can\'t have two tails.')
        tail = last.tail
        alist[-1] = last.head
    elif tail is None:
        tail = nil
    return reduce(flip(make_list), reversed(alist), tail)


class Int(Atom):
    pass


class Float(Atom):
    pass


def byte_array(astring):
    return new_list(map(ord, astring))


def explicit_dcg_goal(aset):
    if len(aset) != 1:
        raise ValueError
    return ExplicitDCGGoal(params=list(aset))


def raiser(error):
    def _(*args, **kwargs):
        raise error
    return _


typemap = {
    int: Int,
    float: Float,
    #str: byte_array,
    str: Atom,
    list: new_list,
    set: explicit_dcg_goal,
    dict: raiser(TypeError),
    tuple: raiser(TypeError),
}


def wrap(item):
    if not isinstance(item, BaseTerm) and callable(item):
        return make_pyfunc(item)
    return typemap.get(type(item), identity)(item)


def make_pyfunc(fn):
    def caller(term, env, db, trail):
        fn(*(each.deref() for each in term.params))
    return (Atom(fn.__name__)
            .bind(add_params(Atom, *(Variable(next_suffix())
                                        for each in signature(fn).parameters)))
            .bind(add_action(Atom, caller)))


nil = Nil()
_C_ = Atom("'C'")


if __name__ == '__main__':

    import unittest

    class Test(unittest.TestCase):

        def test_monad_laws(self):
            self.assertEqual(unit('a').bind(Rule), Rule('a'))
            self.assertEqual(Rule('a').bind(unit), Rule('a'))
            self.assertEqual((unit('a').bind(Relation)).bind(Rule),
                              unit('a').bind(
                                  lambda *args, **kwargs:
                                  Relation(*args, **kwargs).bind(Rule)))

        def test_types(self):
            def test(atom, name, params, goals, actions, Type):
                self.assertTrue(type(atom) is Type)
                self.assertEqual(atom.name, name)
                self.assertEqual(atom.params, tuple(params))
                self.assertEqual(atom.goals, tuple(goals))
                self.assertEqual(atom.actions, tuple(actions))

            def foo():
                pass

            def bar():
                pass

            A = unit('A')
            a = unit('a')
            b = unit('b')
            c = unit('c')
            d = unit('d')
            self.assertEqual(nil, Nil())
            test(A, 'A', [], [], [], Variable)
            test(a, 'a', [], [], [], Atom)
            test(a(b), 'a', [b], [], [], Relation)
            test(a(b), 'a', [b], [], [], Relation)
            test(a << b, 'a', [], [b], [], Rule)
            test(a(b) << c, 'a', [b], [c], [], Rule)
            test(a & b, '&', [a, b], [], [], Conjunction)
            test(a << b & c, 'a', [], [b, c], [], Rule)
            test(a(b) << c & d, 'a', [b], [c, d], [], Rule)
            test(a[foo], 'a', [], [], [foo], Atom)
            test(a[foo][bar], 'a', [], [], [foo, bar], Atom)
            test(a(b)[foo], 'a', [b], [], [foo], Relation)
            test(a[foo](b)[bar], 'a', [b], [], [foo, bar], Relation)
            test((a << b)[foo], 'a', [], [b], [foo], Rule)
            test((a[foo] << b)[bar], 'a', [], [b], [foo, bar], Rule)
            test((a << b[foo])[bar], 'a', [], [b], [bar], Rule)
            test((a(b) << c)[foo], 'a', [b], [c], [foo], Rule)
            test((a(b)[foo] << c)[bar], 'a', [b], [c], [foo, bar], Rule)
            test((a[foo](b) << c)[bar], 'a', [b], [c], [foo, bar], Rule)
            test((a & b)[foo], '&', [a, b], [], [foo], Conjunction)
            test((a[foo] & b)[bar], '&', [a, b], [], [bar], Conjunction)
            test((a << b & c)[foo], 'a', [], [b, c], [foo], Rule)
            test((a(b) << c & d)[foo], 'a', [b], [c, d], [foo], Rule)
            test(a[foo] << b, 'a', [], [b], [foo], Rule)
            test(a(b)[foo] << c, 'a', [b], [c], [foo], Rule)
            test(a[foo] << b & c, 'a', [], [b, c], [foo], Rule)
            test(a(b)[foo] << c & d, 'a', [b], [c, d], [foo], Rule)
            test(a([1, 2]), 'a', [new_list([Int(1), Int(2)])], [], [], Relation)
            test(a([1]), 'a', [new_list([Int(1)])], [], [], Relation)
            #test(a >> b, 'a', [], [b], [], DCGRule)
            #test(a(b) >> c, 'a', [b], [c], [], DCGRule)

    suite = unittest.TestLoader().loadTestsFromTestCase(Test)

    unittest.main()
