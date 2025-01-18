# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = "0.2.5a"
__date__ = "2014-09-27"
__author__ = "Mick Krippendorf <m.krippendorf@freenet.de>"
__license__ = "MIT"


import collections
import copy
import numbers
import pprint

from .dcg import _C_, expand
from .expressions import Name, mcompose, promote
from .operators import rearrange
from .terms import (EMPTY, Addition, Adjunction, Atom, Atomic, Conditional,
                    Disjunction, Division, EmptyList, Environment,
                    Exponentiation, FloorDivision, Implication, Indicator,
                    List, Multiplication, Negation, Negative, Number, Positive,
                    Relation, Remainder, String, Structure, Subtraction,
                    UnificationFailed, Variable, Wildcard, build, is_empty)
from .util import foldr, install_symbols_module, rpartial

system_names = [
    "_",
    "append",
    "arithmetic_equal",
    "arithmetic_not_equal",
    "atomic",
    "call",
    "cut",
    "equal",
    "fail",
    "findall",
    "greater",
    "ignore",
    "integer",
    "join",
    "length",
    "let",
    "listing",
    "lwriteln",
    "maplist",
    "member",
    "nl",
    "nonvar",
    "numeric",
    "once",
    "real",
    "repeat",
    "reverse",
    "select",
    "smaller",
    "throw",
    "transpose",
    "true",
    "unequal",
    "univ",
    "var",
    "write",
    "writeln",
]


__all__ = [
    "Database",
    "UnificationFailed",
    "_C_",
    "build_term",
    "expand_term",
    "promote",
    "pyfunc",
    "unify",
] + system_names


globals().update((each, Name(each)) for each in system_names)


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


install_symbols_module("hornet.symbols", Name)


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
    try:
        for each in flatten(L):
            expect(each, String)
            yield each.ref()
    except UnificationFailed:
        # pyright: ignore[reportUnboundVariable]
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
        result = make_list(env, [Atom(env=env, name=env.T.name)], params)

        unify(env.L, result, trail)

    elif isinstance(env.T, Atom):
        result = make_list(env, [Atom(env=env, name=env.T.name)])
        unify(env.L, result, trail)

    elif isinstance(env.L, List):
        functor = env.L.car.ref
        if not isinstance(functor, Atom):
            raise TypeError(
                f"First Element of List must be Atom, not {type(functor)}: {
                    functor}"
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
    # pyright: ignore[reportMissingImports]
    # pyright: ignore[reportMissingImports]
    # pyright: ignore[reportMissingImports]
    from .symbols import (G1, A, Arity, B, C, D, G, Goal, H, L, List, M, N,
                          Object, P, Predicate, Q, Rest, S, T, X, Y, Z,
                          length_is_N)

    expressions = (
        cut,  # pyright: ignore[reportUndefinedVariable]
        true,  # pyright: ignore[reportUndefinedVariable]
        fail[_fail],  # pyright: ignore[reportUndefinedVariable]
        # not:
        ~X << X & cut[_fail],  # pyright: ignore[reportUndefinedVariable]
        ~_,  # pyright: ignore[reportUndefinedVariable]
        # or:
        X | _ << X,  # pyright: ignore[reportUndefinedVariable]
        _ | Y << Y,  # pyright: ignore[reportUndefinedVariable]
        # xor:
        X ^ Y << X & ~Y,  # pyright: ignore[reportUndefinedVariable]
        X ^ Y << ~X & Y,  # pyright: ignore[reportUndefinedVariable]
        # if-then-else:
        X >> Y | _ << X & Y,  # pyright: ignore[reportUndefinedVariable]
        X >> _ | Z << ~X & Z,  # pyright: ignore[reportUndefinedVariable]
        repeat,  # pyright: ignore[reportUndefinedVariable]
        repeat << repeat,  # pyright: ignore[reportUndefinedVariable]
        let(X, Y)[_let],  # pyright: ignore[reportUndefinedVariable]
        call(Goal) << Goal,  # pyright: ignore[reportUndefinedVariable]
        once(Goal) << Goal & cut,  # pyright: ignore[reportUndefinedVariable]
        ignore(Goal) << Goal & cut,  # pyright: ignore[reportUndefinedVariable]
        ignore(_),  # pyright: ignore[reportUndefinedVariable]
        equal(P, P),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        unequal(P, P) << cut[_fail],
        unequal(_, _),  # pyright: ignore[reportUndefinedVariable]
        greater(X, Y)[_greater],  # pyright: ignore[reportUndefinedVariable]
        smaller(X, Y)[_smaller],  # pyright: ignore[reportUndefinedVariable]
        throw[_throw],  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        findall(Object, Goal, List)[_findall_3],
        # pyright: ignore[reportUndefinedVariable]
        findall(Object, Goal, List, Rest)[_findall_4],
        member(H, [H | T]),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        member(G, [H | T]) << member(G, T),
        append([], A, A),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        append([A | B], C, [A | D]) << append(B, C, D),
        # pyright: ignore[reportUndefinedVariable]
        reverse(X, Y) << reverse(X, [], Y),
        reverse([], Y, Y),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        reverse([X | P], Q, Y) << reverse(P, [X | Q], Y),
        select(X, [X | T], T),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        select(X, [H | T], [H | Rest]) << select(X, T, Rest),
        write(X)[_write],  # pyright: ignore[reportUndefinedVariable]
        writeln(X)[_writeln],  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        lwriteln([H | T]) << writeln(H) & lwriteln(T),
        lwriteln([]) << nl,  # pyright: ignore[reportUndefinedVariable]
        nl[lambda *a: print()],  # pyright: ignore[reportUndefinedVariable]
        listing[_listing_0],
        # pyright: ignore[reportUndefinedVariable]
        listing(Predicate)[_listing_1],
        # pyright: ignore[reportUndefinedVariable]
        listing(Predicate, Arity)[_listing_2],
        _C_([X | L], X, L),  # pyright: ignore[reportUndefinedVariable]
        atomic(X)[_atomic],  # pyright: ignore[reportUndefinedVariable]
        integer(X)[_integer],  # pyright: ignore[reportUndefinedVariable]
        real(X)[_real],  # pyright: ignore[reportUndefinedVariable]
        numeric(X)[_numeric],  # pyright: ignore[reportUndefinedVariable]
        join(L, S)[_join_2],  # pyright: ignore[reportUndefinedVariable]
        join(L, S, T)[_join_3],  # pyright: ignore[reportUndefinedVariable]
        var(X)[_var],  # pyright: ignore[reportUndefinedVariable]
        nonvar(X)[_nonvar],  # pyright: ignore[reportUndefinedVariable]
        univ(T, L)[_univ],  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        arithmetic_equal(X, Y) << let(Z, X) & let(Z, Y),
        arithmetic_not_equal(X, Y) << let(Z, X) & let(
            Z, Y) & cut[_fail],  # pyright: ignore[reportUndefinedVariable]
        arithmetic_not_equal(_, _),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        transpose(L, T)[_transpose],
        maplist(G, [H | T]) << cut & univ(G1, [G, H]) & G1 & maplist(
            G, T),  # pyright: ignore[reportUndefinedVariable]
        maplist(_, []),  # pyright: ignore[reportUndefinedVariable]
        length(L, N) << nonvar(N) & cut & ~smaller(N, 0) & length_is_N(
            L, N),  # pyright: ignore[reportUndefinedVariable]
        length([], 0),  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        length([H | T], N) << length(T, M) & let(N, M + 1),
        length_is_N([], 0) << cut,  # pyright: ignore[reportUndefinedVariable]
        # pyright: ignore[reportUndefinedVariable]
        length_is_N([H | T], N) << let(M, N - 1) & length_is_N(T, M),
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
                    f"Clause '{clause}' of type {
                        type(clause.term)} cannot be asserted into database."
                )
            clauses.append(clause)
        for clause in clauses:
            self[clause.indicator].append(clause)
            # pyright: ignore[reportGeneralTypeIssues]
            self.indicators[clause.name].add(clause.indicator)

    def ask(self, expression):
        return build_term(expression).resolve(self)

    def find_all(self, indicator):
        return self.get(indicator, ())
