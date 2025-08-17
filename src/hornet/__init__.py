# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

import collections
import copy
import numbers
import pprint

import hornet.install_symbols_module
from hornet.symbols import _  # type: ignore
from hornet.symbols import append  # type: ignore
from hornet.symbols import arithmetic_equal  # type: ignore
from hornet.symbols import arithmetic_not_equal  # type: ignore
from hornet.symbols import atomic  # type: ignore
from hornet.symbols import call  # type: ignore
from hornet.symbols import cut  # type: ignore
from hornet.symbols import equal  # type: ignore
from hornet.symbols import fail  # type: ignore
from hornet.symbols import findall  # type: ignore
from hornet.symbols import greater  # type: ignore
from hornet.symbols import ignore  # type: ignore
from hornet.symbols import integer  # type: ignore
from hornet.symbols import join  # type: ignore
from hornet.symbols import length  # type: ignore
from hornet.symbols import let  # type: ignore
from hornet.symbols import listing  # type: ignore
from hornet.symbols import lwriteln  # type: ignore
from hornet.symbols import maplist  # type: ignore
from hornet.symbols import member  # type: ignore
from hornet.symbols import nl  # type: ignore
from hornet.symbols import nonvar  # type: ignore
from hornet.symbols import numeric  # type: ignore
from hornet.symbols import once  # type: ignore
from hornet.symbols import real  # type: ignore
from hornet.symbols import repeat  # type: ignore
from hornet.symbols import reverse  # type: ignore
from hornet.symbols import select  # type: ignore
from hornet.symbols import smaller  # type: ignore
from hornet.symbols import throw  # type: ignore
from hornet.symbols import transpose  # type: ignore
from hornet.symbols import true  # type: ignore
from hornet.symbols import unequal  # type: ignore
from hornet.symbols import univ  # type: ignore
from hornet.symbols import var  # type: ignore
from hornet.symbols import write  # type: ignore
from hornet.symbols import writeln  # type: ignore

from .dcg import _C_, expand
from .expressions import mcompose, promote
from .operators import rearrange
from .terms import (
    EMPTY,
    Addition,
    Adjunction,
    Atom,
    Atomic,
    Conditional,
    Disjunction,
    Division,
    EmptyList,
    Exponentiation,
    FloorDivision,
    Implication,
    Indicator,
    List,
    Multiplication,
    Negation,
    Negative,
    Number,
    Positive,
    Relation,
    Remainder,
    String,
    Structure,
    Subtraction,
    UnificationFailed,
    Variable,
    Wildcard,
    build,
    is_empty,
)
from .util import foldr, rpartial

__all__ = [
    "Database",
    "UnificationFailed",
    "_C_",
    "build_term",
    "expand_term",
    "promote",
    "pyfunc",
    "unify",
    "_",  # type: ignore
    "append",  # type: ignore
    "arithmetic_equal",  # type: ignore
    "arithmetic_not_equal",  # type: ignore
    "atomic",  # type: ignore
    "call",  # type: ignore
    "cut",  # type: ignore
    "equal",  # type: ignore
    "fail",  # type: ignore
    "findall",  # type: ignore
    "greater",  # type: ignore
    "ignore",  # type: ignore
    "integer",  # type: ignore
    "join",  # type: ignore
    "length",  # type: ignore
    "let",  # type: ignore
    "listing",  # type: ignore
    "lwriteln",  # type: ignore
    "maplist",  # type: ignore
    "member",  # type: ignore
    "nl",  # type: ignore
    "nonvar",  # type: ignore
    "numeric",  # type: ignore
    "once",  # type: ignore
    "real",  # type: ignore
    "repeat",  # type: ignore
    "reverse",  # type: ignore
    "select",  # type: ignore
    "smaller",  # type: ignore
    "throw",  # type: ignore
    "transpose",  # type: ignore
    "true",  # type: ignore
    "unequal",  # type: ignore
    "univ",  # type: ignore
    "var",  # type: ignore
    "write",  # type: ignore
    "writeln",  # type: ignore
]

ASSERTABLE = (
    Addition,
    Adjunction,
    Atom,
    Conditional,
    Disjunction,
    Division,
    Exponentiation,
    FloorDivision,
    Implication,
    List,
    Multiplication,
    Negation,
    Negative,
    EmptyList,
    Positive,
    Relation,
    Remainder,
    Subtraction,
)


def unify(this, that, trail):
    this.ref.unify(that.ref, trail)


expand_term = mcompose(build, expand, rearrange)
build_term = mcompose(build, rearrange)


is_atomic = rpartial(isinstance, Atomic)


class Clause:
    def __init__(self, term):
        self.term = term

    def __str__(self):
        return str(self.term)

    def __repr__(self):
        return repr(self.term)


class Fact(Clause):
    @property
    def name(self):
        return self.term.name

    @property
    def indicator(self):
        return self.term.indicator

    @property
    def is_assertable(self):
        return isinstance(self.term, ASSERTABLE)


class Rule(Clause):
    @property
    def name(self):
        return self.term.left.name

    @property
    def indicator(self):
        return self.term.left.indicator

    @property
    def is_assertable(self):
        return True


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


def make_list(env, items, tail=EMPTY):
    def cons(*params):
        return List(env=env, params=params)

    return foldr(cons, items, tail)


class TailPair(Adjunction):
    pass


def expect(item, expected_type):
    if not isinstance(item, expected_type):
        raise UnificationFailed


def _fail(term, env, db, trail):
    raise UnificationFailed


def _write(term, env, db, trail):
    print(env.X, end="")


def _writeln(term, env, db, trail):
    print(env.X)


def _findall_3(term, env, db, trail):
    results = [copy.deepcopy(env.Object.ref) for _ in env.Goal.resolve(db)]
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
    expect(env.Arity, Number)
    indicator = Indicator(env.Predicate(), env.Arity())
    _listing(indicator, db.get(indicator))


def _listing(indicator, clauses):
    print(indicator)
    for clause in clauses:
        print(f"    {clause}.")
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
    expect(env.X, Number)
    expect(env.X(), int)


def _real(term, env, db, trail):
    expect(env.X, Number)
    expect(env.X(), float)


def _numeric(term, env, db, trail):
    expect(env.X, Number)
    expect(env.X(), numbers.Number)


def flatten(L):
    if isinstance(L, EmptyList):
        return []
    elif isinstance(L, List):
        acc = []
        while isinstance(L, List):
            acc.append(L.car.ref)
            L = L.cdr.ref
        if not is_empty(L):
            acc[-1] = TailPair(env=L.env, name="|", params=[acc[-1], L])
        return acc
    else:
        raise TypeError(f"Expected List or EmptyList, found {type(L)}: {L}.")


def flatten_strs(L):
    for each in flatten(L):
        try:
            expect(each, String)
            yield each.ref()
        except UnificationFailed:
            raise TypeError(f"Expected String, found {type(each)}: {each}")


def _join_2(term, env, db, trail):
    unify(env.S, build_term(promote("".join(flatten_strs(env.L)))), trail)


def _join_3(term, env, db, trail):
    unify(env.S, build_term(promote(env.T().join(flatten_strs(env.L)))), trail)


def _var(term, env, db, trail):
    expect(env.X, (Variable, Wildcard))


def _nonvar(term, env, db, trail):
    expect(env.X, Structure)


def _univ(term, env, db, trail):
    if isinstance(env.T, Relation):
        params = make_list(env, env.T.params)
        # pyright: ignore[reportGeneralTypeIssues]
        result = make_list(env, [Atom(env=env, name=env.T.name)], params)  # type: ignore

        unify(env.L, result, trail)

    elif isinstance(env.T, Atom):
        result = make_list(env, [Atom(env=env, name=env.T.name)])
        unify(env.L, result, trail)

    elif isinstance(env.L, List):
        functor = env.L.car.ref
        if not isinstance(functor, Atom):
            raise TypeError(
                f"First Element of List must be Atom, not {type(functor)}: {functor}"
            )
        if isinstance(env.L.cdr.ref, EmptyList):
            unify(env.T, Atom(env=env, name=functor.name), trail)
        else:
            params = flatten(env.L.cdr.ref)
            if isinstance(params[-1], TailPair):
                raise TypeError(f"Proper List expected, found {env.L}")
            result = Relation(env=env, name=functor.name, params=params)
            unify(env.T, result, trail)

    else:
        raise UnificationFailed


def _transpose(term, env, db, trail):
    L0 = flatten(env.L)
    Ls = [flatten(each.ref) for each in L0]
    if len(set(map(len, Ls))) > 1:
        raise ValueError(
            f"Cannot transpose a List of Lists of different lengths: {env.L}"
        )
    Lt = list(zip(*Ls))
    L1 = [make_list(env, each) for each in Lt]
    unify(env.T, make_list(env, L1), trail)


def _throw(term, env, db, trail):
    raise Exception


def _bootstrap():
    from .symbols import G1  # type: ignore
    from .symbols import A  # type: ignore
    from .symbols import Arity  # type: ignore
    from .symbols import B  # type: ignore
    from .symbols import C  # type: ignore
    from .symbols import D  # type: ignore
    from .symbols import G  # type: ignore
    from .symbols import Goal  # type: ignore
    from .symbols import H  # type: ignore
    from .symbols import L  # type: ignore
    from .symbols import List  # type: ignore
    from .symbols import M  # type: ignore
    from .symbols import N  # type: ignore
    from .symbols import Object  # type: ignore
    from .symbols import P  # type: ignore
    from .symbols import Predicate  # type: ignore
    from .symbols import Q  # type: ignore
    from .symbols import Rest  # type: ignore
    from .symbols import S  # type: ignore
    from .symbols import T  # type: ignore
    from .symbols import X  # type: ignore
    from .symbols import Y  # type: ignore
    from .symbols import Z  # type: ignore
    from .symbols import length_is_N  # type: ignore

    expressions = (
        cut,  # type: ignore
        true,  # type: ignore
        fail[_fail],  # type: ignore
        # not:
        ~X << X & cut[_fail],  # type: ignore
        ~_,  # type: ignore
        # or:
        X | _ << X,  # type: ignore
        _ | Y << Y,  # type: ignore
        # xor:
        X ^ Y << X & ~Y,  # type: ignore
        X ^ Y << ~X & Y,  # type: ignore
        # if-then-else:
        X >> Y | _ << X & Y,  # type: ignore
        X >> _ | Z << ~X & Z,  # type: ignore
        repeat,  # type: ignore
        repeat << repeat,  # type: ignore
        let(X, Y)[_let],  # type: ignore
        call(Goal) << Goal,  # type: ignore
        once(Goal) << Goal & cut,  # type: ignore
        ignore(Goal) << Goal & cut,  # type: ignore
        ignore(_),  # type: ignore
        equal(P, P),  # type: ignore
        unequal(P, P) << cut[_fail],  # type: ignore
        unequal(_, _),  # type: ignore
        greater(X, Y)[_greater],  # type: ignore
        smaller(X, Y)[_smaller],  # type: ignore
        throw[_throw],  # type: ignore
        findall(Object, Goal, List)[_findall_3],  # type: ignore
        findall(Object, Goal, List, Rest)[_findall_4],  # type: ignore
        member(H, [H | T]),  # type: ignore
        member(G, [H | T]) << member(G, T),  # type: ignore
        append([], A, A),  # type: ignore
        append([A | B], C, [A | D]) << append(B, C, D),  # type: ignore
        reverse(X, Y) << reverse(X, [], Y),  # type: ignore
        reverse([], Y, Y),  # type: ignore
        reverse([X | P], Q, Y) << reverse(P, [X | Q], Y),  # type: ignore
        select(X, [X | T], T),  # type: ignore
        select(X, [H | T], [H | Rest]) << select(X, T, Rest),  # type: ignore
        write(X)[_write],  # type: ignore
        writeln(X)[_writeln],  # type: ignore
        lwriteln([H | T]) << writeln(H) & lwriteln(T),  # type: ignore
        lwriteln([]) << nl,  # type: ignore
        nl[lambda *a: print()],  # type: ignore
        listing[_listing_0],  # type: ignore
        listing(Predicate)[_listing_1],  # type: ignore
        listing(Predicate, Arity)[_listing_2],  # type: ignore
        _C_([X | L], X, L),  # type: ignore
        atomic(X)[_atomic],  # type: ignore
        integer(X)[_integer],  # type: ignore
        real(X)[_real],  # type: ignore
        numeric(X)[_numeric],  # type: ignore
        join(L, S)[_join_2],  # type: ignore
        join(L, S, T)[_join_3],  # type: ignore
        var(X)[_var],  # type: ignore
        nonvar(X)[_nonvar],  # type: ignore
        univ(T, L)[_univ],  # type: ignore
        arithmetic_equal(X, Y) << let(Z, X) & let(Z, Y),  # type: ignore
        arithmetic_not_equal(X, Y) << let(Z, X) & let(Z, Y) & cut[_fail],  # type: ignore
        arithmetic_not_equal(_, _),  # type: ignore
        transpose(L, T)[_transpose],  # type: ignore
        maplist(G, [H | T]) << cut & univ(G1, [G, H]) & G1 & maplist(G, T),  # type: ignore
        maplist(_, []),  # type: ignore
        length(L, N) << nonvar(N) & cut & ~smaller(N, 0) & length_is_N(L, N),  # type: ignore
        length([], 0),  # type: ignore
        length([H | T], N) << length(T, M) & let(N, M + 1),  # type: ignore
        length_is_N([], 0) << cut,  # type: ignore
        length_is_N([H | T], N) << let(M, N - 1) & length_is_N(T, M),  # type: ignore
    )

    db = ClauseDict()
    indicators = collections.defaultdict(set)

    for expression in expressions:
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
        super().__init__(_system_db)
        self.indicators = collections.defaultdict(set, _indicators)

    def tell(self, *expressions):
        clauses = []
        for expression in expressions:
            clause = make_clause(expand_term(expression))
            if not clause.is_assertable:
                raise TypeError(
                    f"""Clause '{clause}' of type {
                        type(clause.term)
                    } cannot be asserted into database."""
                )
            clauses.append(clause)
        for clause in clauses:
            self[clause.indicator].append(clause)
            # pyright: ignore[reportGeneralTypeIssues]
            self.indicators[clause.name].add(clause.indicator)  # type: ignore

    def ask(self, expression):
        return build_term(expression).resolve(self)  # type: ignore

    def find_all(self, indicator):
        return self.get(indicator, ())
