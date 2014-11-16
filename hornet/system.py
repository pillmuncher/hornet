#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import collections
import copy
import numbers
import pprint

from hornet.util import rpartial, foldr, tabulate
from hornet.expressions import bind_compose, promote, Name
from hornet.operators import rearrange
from hornet.dcg import _C_, expand
from hornet.terms import *


system_names = [
    '_',
    'append',
    'arithmetic_equal',
    'arithmetic_not_equal',
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
    'length',
    'let',
    'listing',
    'lwriteln',
    'maplist',
    'member',
    'nl',
    'nonvar',
    'numeric',
    'once',
    'real',
    'repeat',
    'reverse',
    'select',
    'smaller',
    'throw',
    'transpose',
    'true',
    'unequal',
    'univ',
    'var',
    'write',
    'writeln',
]


__all__ = [
    '_C_',
    'build_term',
    'Database',
    'expand_term',
    'promote',
    'pyfunc',
    'UnificationFailed',
    'unify',
] + system_names


globals().update((each, Name(each)) for each in system_names)


def unify(this, that, trail):
    this.ref.unify(that.ref, trail)


#var_suffixes = tabulate('_{:02X}?'.format)
var_suffix_map = collections.defaultdict(lambda: tabulate('_{:02X}?'.format))


class Environment(dict):

    def __call__(self, name):
        try:
            return self[name]
        except KeyError:
            var = self[name] = Variable(env=self, name=name)
            return var

    def __getattr__(self, name):
        return self[name].ref

    def __deepcopy__(self, memo):
        env = memo[id(self)] = Environment()
        return env

    def rename_vars(self):
        for variable in list(self.values()):
            if isinstance(variable, Variable):
                #variable.name += next(var_suffixes)
                variable.name += next(var_suffix_map[variable.name])
                self[variable.name] = variable

    @property
    class proxy(collections.ChainMap):

        def __getitem__(self, key, _getitem=collections.ChainMap.__getitem__):
            return _getitem(self, str(key))


def build(node):
    return Builder(Environment()).build(node)


expand_term = bind_compose(rearrange, expand, build)
build_term = bind_compose(rearrange, build)


is_atomic = rpartial(isinstance, (Atom, String, Num))
not_assertable = rpartial(
    isinstance, (String, Num, Conjunction, Variable, Wildcard))


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
    return Rule(term) if isinstance(term, Implication) else Fact(term)


class ClauseDict(collections.OrderedDict):

    def __missing__(self, key):
        value = self[key] = []
        return value


def pyfunc(fn):
    def caller(term, env, db, trail):
        fn(*(each.ref for each in term.params))
    return caller


def print_term(term, env, db, trail):
    print(term)


def print_env(term, env, db, trail):
    print(env)


def print_db(term, env, db, trail):
    pprint.pprint(db)


def print_trail(term, env, db, trail):
    pprint.pprint(trail)


def make_list(env, items, tail=NIL):

    def cons(*params):
        return List(env=env, params=params)

    return foldr(cons, items, tail)


class TailPair(Adjunction):
    pass


def flatten(L):
    if not isinstance(L, (List, Nil)):
        raise TypeError('Expected List or Nil, found {}: {}.'
                        .format(type(L), L))
    acc = []
    while isinstance(L, List):
        acc.append(L.car.ref)
        L = L.cdr.ref
    if not is_nil(L):
        acc[-1] = TailPair(env=L.env, name='|', params=[acc[-1], L])
    return acc


def expect(item, expected_type):
    if not isinstance(item, expected_type):
        raise UnificationFailed


def _fail(term, env, db, trail):
    raise UnificationFailed


def _write(term, env, db, trail):
    print(env.X, end='')


def _writeln(term, env, db, trail):
    print(env.X)


def _findall_3(term, env, db, trail):
    results = [copy.deepcopy(env.Object) for _ in env.Goal.resolve(db)]
    unify(env.List, make_list(env, results), trail)


def _findall_4(term, env, db, trail):
    results = [copy.deepcopy(env.Object) for _ in env.Goal.resolve(db)]
    unify(env.List, make_list(env, results, env.Rest), trail)


def _listing_0(term, env, db, trail):
    for each in db.items():
        _listing(*each)


def _listing_1(term, env, db, trail):
    expect(env.Predicate, Atom)
    for indicator in sorted(db.indicators[env.Predicate()]):
        _listing(indicator, db.get(indicator))


def _listing_2(term, env, db, trail):
    expect(env.Predicate, Atom)
    expect(env.Arity, Num)
    indicator = Indicator(env.Predicate(), env.Arity())
    _listing(indicator, db.get(indicator))


def _listing(indicator, clauses):
    print(indicator)
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
    expect(env.X, Num)
    expect(env.X(), int)


def _real(term, env, db, trail):
    expect(env.X, Num)
    expect(env.X(), float)


def _numeric(term, env, db, trail):
    expect(env.X, Num)
    expect(env.X(), numbers.Number)


def flatten_strs(L):
    try:
        for each in flatten(L):
            expect(each, String)
            yield each.ref()
    except UnificationFailed:
        raise TypeError('Expected String, found {}: {}'
                        .format(type(each), each))


def _join_2(term, env, db, trail):
    unify(env.S, build_term(promote(''.join(flatten_strs(env.L)))), trail)


def _join_3(term, env, db, trail):
    unify(env.S, build_term(promote(env.T().join(flatten_strs(env.L)))), trail)


def _var(term, env, db, trail):
    expect(env.X, (Variable, Wildcard))


def _nonvar(term, env, db, trail):
    expect(env.X, Structure)


def _univ(term, env, db, trail):

    if isinstance(env.T, Relation):
        params = make_list(env, env.T.params)
        result = make_list(env, [Atom(env=env, name=env.T.name)], params)
        unify(env.L, result, trail)

    elif isinstance(env.T, Atom):
        result = make_list(env, [Atom(env=env, name=env.T.name)])
        unify(env.L, result, trail)

    elif isinstance(env.L, List):
        functor = env.L.car.ref
        if not isinstance(functor, Atom):
            raise TypeError('First Element of List must be Atom, not {}: {}'
                            .format(type(functor), functor))
        if isinstance(env.L.cdr.ref, Nil):
            unify(env.T, Atom(env=env, name=functor.name), trail)
        else:
            params = flatten(env.L.cdr.ref)
            if isinstance(params[-1], TailPair):
                raise TypeError('Proper List expected, found {}'.format(env.L))
            result = Relation(env=env, name=functor.name, params=params)
            unify(env.T, result, trail)

    else:
        raise UnificationFailed


def _transpose(term, env, db, trail):
    L0 = flatten(env.L)
    Ls = [flatten(each.ref) for each in L0]
    if len(set(map(len, Ls))) > 1:
        raise ValueError(
            'Cannot transpose a List of Lists of different lengths: {}'
            .format(env.L)
        )
    Lt = list(zip(*Ls))
    L1 = [make_list(env, each) for each in Lt]
    unify(env.T, make_list(env, L1), trail)


def _throw(term, env, db, trail):
    raise Exception


def _bootstrap():

    from hornet.symbols import P, Q, X, Y, Z, Tail, Object, Goal, List, Rest
    from hornet.symbols import Predicate, A, B, C, D, H, L, T, S, Arity, G, G1
    from hornet.symbols import M, N, length_given_N_

    exprs = (

        cut,

        true,

        fail[_fail],

        # not:
        ~X << X & cut[_fail],
        ~_,

        # or:
        X | _ << X,
        _ | Y << Y,

        # xor:
        X ^ Y << X & ~Y,
        X ^ Y << ~X & Y,

        # if-then-else:
        X >> Y | _ << X & Y,
        X >> _ | Z << ~X & Z,

        repeat,
        repeat << repeat,

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

        member(H, [H|T]),
        member(G, [H|T]) <<
            member(G, T),

        append([], A, A),
        append([A|B], C, [A|D]) <<
                append(B, C, D),

        reverse(X, Y) <<
            reverse(X, [], Y),

        reverse([], Y, Y),
        reverse([X|P], Q, Y) <<
            reverse(P, [X|Q], Y),

        select(X, [X|T], T),
        select(X, [H|T], [H|Rest]) <<
            select(X, T, Rest),

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

        nonvar(X)[_nonvar],

        univ(T, L)[_univ],

        arithmetic_equal(X, Y) <<
            let(Z, X) &
            let(Z, Y),

        arithmetic_not_equal(X, Y) <<
            let(Z, X) &
            let(Z, Y) & cut[_fail],
        arithmetic_not_equal(_, _),

        transpose(L, T)[_transpose],

        maplist(G, [H|T]) <<
            cut & univ(G1, [G, H]) & G1 &
            maplist(G, T),
        maplist(_, []),

        length(L, N) <<
            nonvar(N) & cut & ~smaller(N, 0) & length_given_N_(L, N),
        length([], 0),
        length([H|T], N) <<
            length(T, M) &
            let(N, M + 1),

        length_given_N_([], 0) << cut,
        length_given_N_([H|T], N) <<
            let(M, N - 1) &
            length_given_N_(T, M),

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

    def tell(self, *exprs):
        clauses = []
        for expression in exprs:
            clause = make_clause(expand_term(expression))
            if not_assertable(clause.head):
                raise TypeError("Clause '{}' cannot be asserted into database."
                                .format(clause))
            clauses.append(clause)
        for clause in clauses:
            self[clause.indicator].append(clause)
            self.indicators[clause.name].add(clause.indicator)

    def ask(self, expression):
        term = build_term(expression)
        for _ in term.resolve(self):
            yield term.env.proxy

    def find_all(self, indicator):
        for clause in self.get(indicator, ()):
            head, body, term = clause.fresh(Environment())
            term.env.rename_vars()
            yield head, body

