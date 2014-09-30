#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


def __init__():

    import sys
    import types
    from functools import lru_cache
    from importlib.abc import MetaPathFinder, Loader
    from importlib.machinery import ModuleSpec
    from .expressions import Name

    SYMBOLS_NAME = 'hornet.symbols'

    class SymbolsFactory(types.ModuleType):
        __all__ = []
        __file__ = __file__
        __getattr__ = staticmethod(lru_cache()(Name))

    class SymbolsImporter(MetaPathFinder, Loader):

        def find_spec(self, fullname, path=None, target=None):
            if fullname == SYMBOLS_NAME:
                return ModuleSpec(fullname, self)

        def create_module(self, spec):
            return sys.modules.setdefault(spec.name, SymbolsFactory(spec.name))

        def exec_module(self, module):
            pass

    sys.meta_path.insert(0, SymbolsImporter())

__init__()

del __init__


import collections
import copy
import numbers
import pprint

from .expressions import unit, bind, lift, mapply, mcompose, promote
from .expressions import Name
from .dcg import _C_
from .terms import UnificationFailed, make_list, is_atomic, Num, Indicator, Cut
from .terms import unify, build_term, expand_term, is_assertable, cut_parent
from .terms import Variable, List, Atom, Relation, Nil, NIL, Adjunction
from .terms import Environment, Implication


system_names = [
    '_',
    'append',
    'atomic',
    'call',
    'cut',
    'equal',
    'fail',
    'findall',
    'greater',
    'ignore',
    'integer',
    'join',
    'let',
    'listing',
    'lwriteln',
    'member',
    'nl',
    'numeric',
    'once',
    'real',
    'reverse',
    'smaller',
    'throw',
    'true',
    'unequal',
    'univ',
    'var',
    'write',
    'writeln',
]


__all__ = [
    'Database',
    'build_term',
    'expand_term',
    'pyfunc',
    'UnificationFailed',
    '_C_',
    'unit',
    'bind',
    'lift',
    'mapply',
    'mcompose',
    'promote'
] + system_names


globals().update((each, Name(each)) for each in system_names)


def pyfunc(fn):
    def caller(term, env, db, trail):
        fn(*(each.deref for each in term.params))
    return caller


def print_term(term, env, db, trail):
    print(term)


def print_env(term, env, db, trail):
    print(env)


def print_db(term, env, db, trail):
    pprint.pprint(db)


def print_trail(term, env, db, trail):
    pprint.pprint(trail)


def _fail(term, env, db, trail):
    raise UnificationFailed


def _write(term, env, db, trail):
    print(env.X, end='')


def _writeln(term, env, db, trail):
    print(env.X)


def _findall_3(term, env, db, trail):
    results = [copy.deepcopy(env.Object.deref) for _ in env.Goal.resolve(db)]
    unify(env.List, make_list(env, results), trail)


def _findall_4(term, env, db, trail):
    results = [copy.deepcopy(env.Object.deref) for _ in env.Goal.resolve(db)]
    unify(env.List, make_list(env, results, env.Rest), trail)


def _listing_0(term, env, db, trail):
    for each in db.items():
        _listing(*each)


def _listing_1(term, env, db, trail):
    for indicator in sorted(db.indicators[env.Predicate()]):
        _listing(indicator, db.get(indicator))


def _listing_2(term, env, db, trail):
    indicator = Indicator(env.Predicate(), env.Arity())
    _listing(indicator, db.get(indicator))


def _listing(indicator, clauses):
    print(str(indicator))
    for clause in clauses:
        print('    {}.'.format(clause))
    print()


def _smaller(term, env, db, trail):
    if not env.X() < env.Y():
        raise UnificationFailed


def _greater(term, env, db, trail):
    if not env.X() > env.Y():
        raise UnificationFailed


def _let(term, env, db, trail):
    unify(env.X, build_term(promote(env.Y())), trail)


def _atomic(term, env, db, trail):
    if not is_atomic(env.X):
        raise UnificationFailed


def _integer(term, env, db, trail):
    if not isinstance(env.X, Num):
        raise UnificationFailed
    if not isinstance(env.X(), int):
        raise UnificationFailed


def _real(term, env, db, trail):
    if not isinstance(env.X, Num):
        raise UnificationFailed
    if not isinstance(env.X(), float):
        raise UnificationFailed


def _numeric(term, env, db, trail):
    if not isinstance(env.X, Num):
        raise UnificationFailed
    if not isinstance(env.X(), numbers.Number):
        raise UnificationFailed


def _join_2(term, env, db, trail):
    unify(env.S, build_term(promote(''.join(env.L()))), trail)


def _join_3(term, env, db, trail):
    unify(env.S, build_term(promote(env.T().join(env.L()))), trail)


def _var(term, env, db, trail):
    if not isinstance(env.X, Variable):
        raise UnificationFailed


def flatten(L):
    if isinstance(L, Nil):
        return []
    acc = []
    while True:
        car = L.car.deref
        cdr = L.cdr.deref
        if isinstance(cdr, List):
            acc.append(car)
            L = cdr
        elif isinstance(cdr, Nil):
            acc.append(car)
            return acc
        else:
            acc.append(Adjunction(env=L.env, name='|', params=[car, cdr]))
            return acc


def _univ(term, env, db, trail):

    if isinstance(env.T, Relation):
        params = make_list(env, env.T.params)
        result = make_list(env, [Atom(env=env, name=env.T.name)], params)
        unify(env.L, result, trail)

    elif isinstance(env.T, Atom):
        result = make_list(env, [Atom(env=env, name=env.T.name)])
        unify(env.L, result, trail)

    elif isinstance(env.L, List):
        functor, *params = flatten(env.L)
        if not isinstance(functor, Atom):
            raise UnificationFailed
        if params:
            if isinstance(params[-1], Adjunction):
                raise TypeError('List expected, found {}'.format(env.L))
            result = Relation(env=env, name=functor.name, params=params)
            unify(env.T, result, trail)
        else:
            unify(env.T, Atom(env=env, name=functor.name), trail)

    else:
        raise UnificationFailed


def _throw(term, env, db, trail):
    raise Exception


class Clause(collections.namedtuple('BaseClause', 'head body term')):

    __slots__ = ()

    def fresh(self, env):
        return type(self)(self.term.fresh(env))

    @property
    def name(self):
        return self.head.name

    @property
    def indicator(self):
        return self.head.indicator

    def __str__(self):
        return str(self.term)

    def __repr__(self):
        return repr(self.term)


class Fact(Clause):

    __slots__ = ()

    def __new__(cls, term):
        return Clause.__new__(cls, head=term, body=None, term=term)


class Rule(Clause):

    __slots__ = ()

    def __new__(cls, term):
        return Clause.__new__(cls, head=term.left, body=term.right, term=term)


def make_clause(term):
    if isinstance(term, Implication):
        return Rule(term)
    else:
        return Fact(term)

class ClauseDict(collections.OrderedDict):

    def __missing__(self, key):
        value = self[key] = []
        return value


def _bootstrap():

    from .symbols import P, Q, X, Y, Z, Tail, Object, Goal, List, Rest
    from .symbols import Predicate, A, B, C, D, H, L, T, S, Arity

    exprs = (

        cut,

        true,

        fail[_fail],

        ~X << X & cut[_fail],
        ~_,

        X | _ << X,
        _ | Y << Y,

        X ^ Y << X & ~Y,
        X ^ Y << ~X & Y,

        X >> _ | Z << ~X & Z,
        X >> Y | _ << X & Y,

        let(X, Y)[_let],

        call(Goal) << Goal,

        once(Goal) << Goal & cut,

        ignore(Goal) << Goal & cut,
        ignore(_),

        equal(P, P),

        unequal(P, P) << cut[_fail],
        unequal(_, _),

        greater(X, Y)[_greater],

        smaller(X, Y)[_smaller],

        throw[_throw],

        findall(Object, Goal, List)[_findall_3],
        findall(Object, Goal, List, Rest)[_findall_4],

        member(H, [H|_]),
        member(H, [_|T]) <<
            member(H, T),

        append([], A, A),
        append([A|B], C, [A|D]) <<
                append(B, C, D),

        reverse(X, Y) <<
            reverse(X, [], Y),

        reverse([], Y, Y),
        reverse([X|P], Q, Y) <<
            reverse(P, [X|Q], Y),

        write(X)[_write],

        writeln(X)[_writeln],

        lwriteln([H|T]) << writeln(H) & lwriteln(T),
        lwriteln([]) << nl,

        nl[lambda *a: print()],

        listing[_listing_0],

        listing(Predicate)[_listing_1],

        listing(Predicate, Arity)[_listing_2],

        _C_([X|L], X, L),

        atomic(X)[_atomic],

        integer(X)[_integer],

        real(X)[_real],

        numeric(X)[_numeric],

        join(L, S)[_join_2],

        join(L, S, T)[_join_3],

        var(X)[_var],

        univ(T, L)[_univ],

    )

    db = ClauseDict()
    indicators = collections.defaultdict(set)

    for expression in exprs:
        clause = make_clause(build_term(expression))
        db[clause.indicator].append(clause)
        indicators[clause.name].add(clause.indicator)

    return (
        tuple((k, tuple(v)) for k, v in db.items()),
        tuple((k, frozenset(v)) for k, v in indicators.items()),
    )


_system_db, _indicators = _bootstrap()


class Database(ClauseDict):

    def __init__(self):
        collections.OrderedDict.__init__(self, _system_db)
        self.indicators = collections.defaultdict(set, _indicators)

    def ask(self, expression):
        term = build_term(expression)
        goal = Relation(env=term.env, name='call', params=[term])
        for _ in goal.resolve(self):
            yield goal.env

    def tell(self, *exprs):
        clauses = []
        for expression in exprs:
            clause = make_clause(expand_term(expression))
            if is_assertable(clause.head):
                clauses.append(clause)
            else:
                raise TypeError('clause {} cannot be asserted into database.'
                                .format(clause))
        for clause in clauses:
            self[clause.indicator].append(clause)
            self.indicators[clause.name].add(clause.indicator)

    def find_all(self, indicator):
        for rule in self.get(indicator, ()):
            yield rule.fresh(Environment())[:2]
