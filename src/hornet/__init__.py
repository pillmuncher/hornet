# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Callable

from hornet.clauses import Database, Environment, predicate
from hornet.combinators import Step, Subst, unit
from hornet.terms import DCG

from . import combinators, symbols, terms
from .symbols import (
    append,
    arithmetic_equal,
    call,
    cut,
    equal,
    fail,
    findall,
    greater,
    ifelse,
    ignore,
    is_atom,
    is_atomic,
    is_bool,
    is_bytes,
    is_complex,
    is_constant,
    is_float,
    is_int,
    is_numeric,
    is_str,
    is_var,
    join,
    length,
    let,
    lwriteln,
    maplist,
    member,
    nl,
    nonvar,
    once,
    phrase,
    repeat,
    reverse,
    select,
    smaller,
    throw,
    true,
    unequal,
    univ,
    write,
    writeln,
)

__all__ = (
    "unit",
    "combinators",
    "symbols",
    "terms",
    "DCG",
    "database",
    "append",
    "arithmetic_equal",
    "call",
    "cut",
    "equal",
    "fail",
    "findall",
    "greater",
    "ifelse",
    "ignore",
    "is_atom",
    "is_atomic",
    "is_bool",
    "is_bytes",
    "is_complex",
    "is_constant",
    "is_float",
    "is_int",
    "is_numeric",
    "is_str",
    "is_var",
    "join",
    "length",
    "let",
    "lwriteln",
    "maplist",
    "member",
    "nl",
    "nonvar",
    "once",
    "phrase",
    "predicate",
    "repeat",
    "reverse",
    "select",
    "smaller",
    "throw",
    "true",
    "unequal",
    "univ",
    "write",
    "writeln",
)


def _bootstrap_database() -> Callable[[], Database]:
    from numbers import Number

    from toolz import flip, reduce

    from hornet.clauses import predicate, resolve
    from hornet.combinators import cut as _cut
    from hornet.combinators import fail as _fail
    from hornet.combinators import then
    from hornet.combinators import unify as _unify
    from hornet.combinators import unit as _unit
    from hornet.terms import (
        EMPTY,
        Add,
        Atom,
        Atomic,
        BitAnd,
        BitOr,
        BitXor,
        Cons,
        Div,
        Empty,
        FloorDiv,
        Functor,
        Invert,
        LShift,
        Mod,
        Mul,
        NonVariable,
        Pow,
        Primitive,
        RShift,
        Sub,
        Term,
        UAdd,
        USub,
        Variable,
        promote,
    )

    from . import symbols
    from .symbols import (
        G0,
        G1,
        L0,
        L1,
        A,
        B,
        C,
        D,
        E,
        F,
        G,
        H,
        L,
        N,
        O,
        P,
        Q,
        R,
        S,
        T,
        V,
        X,
        Y,
    )

    def to_python_list(cons_list: Term, subst: Subst) -> list[Term]:
        assert isinstance(cons_list, Cons | Empty)
        result = []
        while True:
            match subst.actualize(cons_list):
                case Cons(head=head, tail=tail):
                    result.append(head)
                    cons_list = tail
                case Empty():
                    return result
                case other:
                    raise TypeError(f"Expected Cons list, got {other!r}")

    def eval_term(val: Term, subst: Subst) -> int | float | complex | bool:
        """Evaluate a Hornet arithmetic term directly from Terms."""

        val = subst.actualize(val)

        match val:
            case int() | bool() | float() | complex():
                return val

            # Unary operators
            case Invert(a):
                v = eval_term(a, subst)
                assert not isinstance(v, bool | float | complex)
                return ~v
            case UAdd(a):
                return +eval_term(a, subst)
            case USub(a):
                return -eval_term(a, subst)

            # Binary operators
            case Add((l, r)):
                return eval_term(l, subst) + eval_term(r, subst)
            case Sub((l, r)):
                return eval_term(l, subst) - eval_term(r, subst)

            case Mul((l, r)):
                return eval_term(l, subst) * eval_term(r, subst)
            case Div((l, r)):
                return eval_term(l, subst) / eval_term(r, subst)
            case FloorDiv((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, complex)
                return vl // vr
            case Mod((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, complex)
                return vl % vr

            case Pow((l, r)):
                return eval_term(l, subst) ** eval_term(r, subst)

            case BitAnd((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, float | complex)
                return vl & vr
            case BitOr((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, float | complex)
                return vl | vr
            case BitXor((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, float | complex)
                return vl ^ vr

            case LShift((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, float | complex)
                return vl << vr
            case RShift((l, r)):
                vl = eval_term(l, subst)
                assert not isinstance(vl, float | complex)
                vr = eval_term(r, subst)
                assert not isinstance(vr, float | complex)
                return vl >> vr

            # Unbound variable
            case Variable():
                raise ValueError(f"Cannot evaluate unbound variable: {val!r}")

            case _:
                raise TypeError(f"Cannot evaluate non-arithmetic Term: {val!r}")

    db = Database()

    @db.tell
    @predicate(let(R, F))
    def _let(db: Database, subst: Subst, env: Environment) -> Step:
        r = subst.actualize(env[R])
        assert isinstance(r, Variable)
        f = subst.actualize(env[F])
        f1 = eval_term(f, subst=subst)
        return then(_unify(r, f1), _cut)(db, subst)

    # Type checking predicates
    def check(
        db: Database,
        term: Term,
        var: NonVariable,
        match: Callable[[Term], bool],
    ) -> None:
        @db.tell
        @predicate(term)
        def _check(db: Database, subst: Subst, env: Environment) -> Step:
            if match(subst.actualize(env[var])):
                return _unit(db, subst)
            else:
                return _fail(db, subst)

    check(db, is_var(V), V, lambda term: isinstance(term, Variable))
    check(db, nonvar(V), V, lambda term: not isinstance(term, Variable))
    check(db, is_atom(V), V, lambda term: isinstance(term, Atom))
    check(db, is_atomic(V), V, lambda term: isinstance(term, Atomic))
    check(db, is_constant(V), V, lambda term: isinstance(term, Primitive))
    check(db, is_bool(V), V, lambda term: isinstance(term, bool))
    check(db, is_bytes(V), V, lambda term: isinstance(term, bytes))
    check(db, is_complex(V), V, lambda term: isinstance(term, complex))
    check(db, is_float(V), V, lambda term: isinstance(term, float))
    check(db, is_int(V), V, lambda term: isinstance(term, int))
    check(db, is_numeric(V), V, lambda term: isinstance(term, Number))
    check(db, is_str(V), V, lambda term: isinstance(term, str))

    @db.tell
    @predicate(univ(P, L))
    def _univ(db: Database, subst: Subst, env: Environment) -> Step:
        match subst.actualize(env[P]):
            case Atom(name=name) as res:
                left = promote([res])
            case Functor(name=name, args=args):
                actual_args = tuple(subst.actualize(a) for a in args)
                left = promote([Atom(name), *actual_args])
            case v:
                left = v
        match subst.actualize(env[L]):
            case Cons(head=Atom() as head, tail=Empty()):
                right = head
            case Cons(head=Atom(name=name) as head, tail=tail):
                args = to_python_list(tail, subst)
                right = Functor(name, *(promote(item) for item in args))
            case v:
                right = v
        assert not (isinstance(left, Variable) and isinstance(right, Variable))
        return _unify(left, right)(db, subst)

    @db.tell
    @predicate(call(G))
    def _call(db: Database, subst: Subst, env: Environment) -> Step:
        return resolve(subst.actualize(env[G]))(db, subst)

    @db.tell
    @predicate(throw(E))
    def _throw(db: Database, subst: Subst, env: Environment) -> Step:
        raise Exception(subst.actualize(env[E]))

    @db.tell
    @predicate(ifelse(T, Y, N))
    def _ifelse(db: Database, subst: Subst, env: Environment) -> Step:
        for new_subst in db.run_query(subst.actualize(env[T]), subst):
            return resolve(new_subst.actualize(env[Y]))(db, new_subst)
        else:
            return resolve(subst.actualize(env[N]))(db, subst)

    @db.tell
    @predicate(smaller(A, B))
    def _smaller(db: Database, subst: Subst, env: Environment) -> Step:
        match subst.actualize(env[A]), subst.actualize(env[B]):
            case int() | float() as a, int() | float() as b:
                if a < b:
                    return _unit(db, subst)
        return _fail(db, subst)

    @db.tell
    @predicate(greater(A, B))
    def _greater(db: Database, subst: Subst, env: Environment) -> Step:
        match subst.actualize(env[A]), subst.actualize(env[B]):
            case int() | float() as a, int() | float() as b:
                if a > b:
                    return _unit(db, subst)
        return _fail(db, subst)

    @db.tell
    @predicate(length(L, N))
    def _length(db: Database, subst: Subst, env: Environment) -> Step:
        count = 0
        tail = subst.actualize(env[L])
        length = subst.actualize(env[N])
        while True:
            match tail:
                case Empty():
                    return _unify(count, length)(db, subst)
                case Cons(tail=tail):
                    count += 1
                case _:
                    raise TypeError(f"list must end with [], not {tail}")

    @db.tell
    @predicate(join(L, S))
    def _join(db: Database, subst: Subst, env: Environment) -> Step:
        items = subst.actualize(env[L])
        assert isinstance(items, Cons | Empty)

        result = to_python_list(items, subst)
        assert all(isinstance(each, str) for each in result)

        return _unify(env[S], "".join(map(str, result)))(db, subst)

    def list_to_cons(items: list[Term]) -> Cons | Empty:
        return reduce(flip(Cons), reversed(items), EMPTY)  # pyright: ignore

    @db.tell
    @predicate(findall(O, G, L))
    def _findall(db: Database, subst: Subst, env: Environment) -> Step:
        obj = subst.actualize(dict(env)[O])
        assert isinstance(obj, Variable)

        goal = subst.actualize(env[G])
        assert isinstance(goal, NonVariable)

        items = [s.actualize(obj) for s in db.run_query(goal, subst=subst)]

        return _unify(env[L], list_to_cons(items))(db, subst)

    # Printing predicates
    @db.tell
    @predicate(write(V))
    def _write(db: Database, subst: Subst, env: Environment) -> Step:
        print(subst.actualize(env[V]), end="")
        return _unit(db, subst)

    @db.tell
    @predicate(writeln(V))
    def _writeln(db: Database, subst: Subst, env: Environment) -> Step:
        print(subst.actualize(env[V]))
        return _unit(db, subst)

    db.tell(
        #
        # call a goal G but never backtrack:
        once(G).when(
            call(G),
            cut,
        ),
        #
        # call goal G but ignore if it succeeds:
        ignore(G).when(
            call(G),
            cut,
        ),
        #
        # always succeed:
        ignore(symbols._),
        #
        # test if two terms can be unified:
        equal(X, X),
        #
        # test if two terms cannot be unified:
        unequal(X, Y).when(
            ~equal(X, Y),
        ),
        #
        # repeat infinitely:
        repeat,
        repeat.when(
            repeat,
        ),
        append([A | B], C, [A | D]).when(
            append(B, C, D),
        ),
        append([], A, A),
        #
        # reverse a list:
        reverse([X | P], Q, Y).when(
            reverse(P, [X | Q], Y),
        ),
        reverse(X, Y).when(
            reverse(X, [], Y),
        ),
        reverse([], Y, Y),
        #
        # test if an item occurs in a list:
        member(H, [H | T]),
        member(G, [H | T]).when(
            member(G, T),
        ),
        #
        # select an item from a list:
        select(X, [X | T], T),
        select(X, [H | T], [H | R]).when(
            select(X, T, R),
        ),
        #
        # call goal G on every element of a list and collect the results:
        maplist(G, [H | T]).when(
            univ(G1, [G, H]),
            call(G1),
            maplist(G, T),
        ),
        maplist(symbols._, []),
        #
        # write out a list, end with newline:
        lwriteln([H | T]).when(
            writeln(H),
            lwriteln(T),
        ),
        lwriteln([]).when(
            nl,
        ),
        #
        # write out a newline:
        nl.when(
            writeln(""),
        ),
        #
        # test to see if two arithemtic expressions yield the same result:
        arithmetic_equal(X, Y).when(
            let(A, X),
            let(B, Y),
            equal(A, B),
        ),
        #
        # convenience predicate for DCG queries:
        phrase(G0, R).when(
            univ(G0, L0),
            append(L0, [R, []], L1),
            univ(G1, L1),
            call(G1),
        ),
    )

    def database() -> Database:
        """Return a new child of the default database."""
        return db.new_child()

    return database


database = _bootstrap_database()
