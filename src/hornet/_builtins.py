# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Callable

from hornet.terms import (
    Add,
    BitAnd,
    BitOr,
    BitXor,
    Div,
    FloorDiv,
    Invert,
    LShift,
    Mod,
    Mul,
    Pow,
    RShift,
    Sub,
    UAdd,
    USub,
)

from .goals import Database

__all__ = ["_bootstrap_database"]

# TODO: implement the following builtin predicates:
#
# assertz
# is_list
# arithmetic_equal,
# listing,
# transpose,
#
# from toolz import flip, reduce
#
#
# def all_of_(left, right, *rights):
#     if rights:
#         return reduce(flip(and_), (right, *rights), left)  # pyright: ignore
#     return and_(left, right)
#
#
# def any_of_(left, right, *rights):
#     if rights:
#         return reduce(flip(or_), (right, *rights), left)  # pyright: ignore
#     return or_(left, right)
# @db.tell
# @predicate(all_of())
# def _1(env: Environment) -> Step:
#     def goal(db: Database, subst: Subst) -> Step:
#         return amb_from_iterable(
#             map(resolve, (subst.actualize(term) for term in env))
#         )(db, subst)
#
#     return goal
#
# @db.tell
# @predicate(any_of())
# def _2(env: Environment) -> Step:
#     def goal(db: Database, subst: Subst) -> Step:
#         return seq_from_iterable(
#             map(resolve, (subst.actualize(term) for term in env))
#         )(db, subst)
#
#     return goal
# @db.tell
# @predicate(univ(F, L))
# def _3(env: Environment) -> Step:
#     def goal(db: Database, subst: Subst) -> Step:
#         match subst.actualize(env[F]):
#             case Atom(name=name) as res:
#                 left = term_to_resolvable([res])
#             case Functor(args=args) as res:
#                 actual_args = tuple(
#                     resolvable_to_term(subst.actualize(a), subst) for a in args
#                 )
#                 left = term_to_resolvable([res, *actual_args])
#             case v:
#                 left = v
#         match subst.actualize(env[L]):
#             case Cons(head=Atom() as head, tail=Empty()):
#                 right = head
#             case Cons(head=Atom(name=name) as head, tail=tail):
#                 args = to_python_list(cast(Cons | Empty, tail), subst)
#                 new_args = tuple(term_to_resolvable(item) for item in args)
#                 right = Functor(name=name, args=new_args)
#             case v:
#                 right = v
#         if isinstance(left, Variable) and isinstance(right, Variable):
#             raise TypeError(f"Cannot unify {F} with {L}")
#         return _unify(left, right)(db, subst)
#
#     return goal


# Bootstrap a default database with builtins
def _bootstrap_database() -> Callable[[], Database]:
    """Add default Hornet builtins to the given database."""
    from numbers import Number

    from toolz import flip, reduce

    from hornet.combinators import Goal, Step, Subst
    from hornet.combinators import cut as _cut
    from hornet.combinators import fail as _fail
    from hornet.combinators import neg as _neg
    from hornet.combinators import then
    from hornet.combinators import unify as _unify
    from hornet.combinators import unit as _unit
    from hornet.expressions import Expression
    from hornet.goals import Environment, PythonGoal, predicate, resolve, to_python_list
    from hornet.terms import (
        EMPTY,
        Atom,
        Atomic,
        Cons,
        Empty,
        Primitive,
        QueryTerm,
        Term,
        Variable,
    )

    from . import symbols
    from .symbols import (
        G1,
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
        Z,
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

    def goal(value: Goal) -> PythonGoal:
        return lambda db, subst, _: value(db, subst)

    db = Database()

    def eval_term(val: Term, subst: Subst) -> int | float | complex | bool:
        """Evaluate a Hornet arithmetic term directly from Terms."""

        # Dereference variables
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

    db.tell(
        predicate(cut)(goal(_cut)),
        predicate(fail)(goal(_fail)),
        predicate(true)(goal(_unit)),
    )

    @db.tell
    @predicate(~X)
    def _5(db: Database, subst: Subst, env: Environment) -> Step:
        return _neg(resolve(subst.actualize(env[X])))(db, subst)

    @db.tell
    @predicate(let(R, F))
    def _6(db: Database, subst: Subst, env: Environment) -> Step:
        r = subst.actualize(env[R])
        assert isinstance(r, Variable)
        f = subst.actualize(env[F])
        f1 = eval_term(f, subst=subst)
        return then(_unify(r, f1), _cut)(db, subst)

    @db.tell
    @predicate(call(G))
    def _7(db: Database, subst: Subst, env: Environment) -> Step:
        return resolve(subst.actualize(env[G]))(db, subst)

    @db.tell
    @predicate(throw(E))
    def _8(db: Database, subst: Subst, env: Environment) -> Step:
        raise Exception(subst.actualize(env[E]))

    @db.tell
    @predicate(ifelse(T, Y, N))
    def _9(db: Database, subst: Subst, env: Environment) -> Step:
        for new_subst in db.resolve(subst.actualize(env[T]), subst):
            return resolve(new_subst.actualize(env[Y]))(db, new_subst)
        else:
            return resolve(subst.actualize(env[N]))(db, subst)

    @db.tell
    @predicate(smaller(A, B))
    def _10(db: Database, subst: Subst, env: Environment) -> Step:
        match subst.actualize(env[A]), subst.actualize(env[B]):
            case int() | float() as a, int() | float() as b:
                if a < b:
                    return _unit(db, subst)
        return _fail(db, subst)

    @db.tell
    @predicate(greater(A, B))
    def _11(db: Database, subst: Subst, env: Environment) -> Step:
        match subst.actualize(env[A]), subst.actualize(env[B]):
            case int() | float() as a, int() | float() as b:
                if a > b:
                    return _unit(db, subst)
        return _fail(db, subst)

    @db.tell
    @predicate(length(L, N))
    def _12(db: Database, subst: Subst, env: Environment) -> Step:
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
    def _13(db: Database, subst: Subst, env: Environment) -> Step:
        items = subst.actualize(env[L])
        assert isinstance(items, Cons | Empty)

        result = to_python_list(items, subst)
        assert all(isinstance(each, str) for each in result)

        return _unify(env[S], "".join(map(str, result)))(db, subst)

    def list_to_cons(items: list[Term]) -> Cons | Empty:
        return reduce(flip(Cons), reversed(items), EMPTY)  # pyright: ignore

    @db.tell
    @predicate(findall(O, G, L))
    def _14(db: Database, subst: Subst, env: Environment) -> Step:
        obj = subst.actualize(dict(env)[O])
        assert isinstance(obj, Variable)

        goal = subst.actualize(env[G])
        assert isinstance(goal, QueryTerm)

        items = [s.actualize(obj) for s in db.resolve(goal, subst=subst)]

        return _unify(env[L], list_to_cons(items))(db, subst)

    # Printing predicates
    @db.tell
    @predicate(write(V))
    def _15(db: Database, subst: Subst, env: Environment) -> Step:
        print(subst.actualize(env[V]), end="")
        return _unit(db, subst)

    @db.tell
    @predicate(writeln(V))
    def _16(db: Database, subst: Subst, env: Environment) -> Step:
        print(subst.actualize(env[V]))
        return _unit(db, subst)

    # Type checking predicates
    def check(
        db: Database,
        expr: Expression,
        var: Expression[Variable],
        match: Callable[[Term], bool],
    ) -> None:
        @db.tell
        @predicate(expr)
        def _17(db: Database, subst: Subst, env: Environment) -> Step:
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

    db.tell(
        #
        # test if two terms can be unified:
        equal(X, X),
    )
    db.tell(
        #
        # test if two terms cannot be unified:
        unequal(X, Y).when(
            ~equal(X, Y),
        ),
    )
    db.tell(
        #
        # call a goal G but never backtrack:
        once(G).when(
            call(G),
            cut,
        ),
    )
    db.tell(
        #
        # repeat infinitely:
        repeat,
        repeat.when(
            repeat,
        ),
    )
    db.tell(
        #
        # call goal G but ignore if it succeeds:
        ignore(G).when(
            call(G),
            cut,
        ),
        ignore(symbols._),
    )
    db.tell(
        #
        # append two lists:
        append([A | B], C, [A | D]).when(
            append(B, C, D),
        ),
    )
    db.tell(
        append([], A, A),
    )
    db.tell(
        #
        # test if an item occurs in a list:
        member(H, [H | T]),
        member(G, [H | T]).when(
            member(G, T),
        ),
    )
    db.tell(
        #
        # select an item from a list:
        select(X, [X | T], T),
        select(X, [H | T], [H | R]).when(
            select(X, T, R),
        ),
    )
    db.tell(
        #
        # call goal G on every element of a list and collect the results:
        maplist(G, [H | T]).when(
            cut,
            univ(G1, [G, H]),
            call(G1),
            maplist(G, T),
        ),
        maplist(symbols._, []),
    )
    db.tell(
        #
        # write out a list, end with newline:
        lwriteln([H | T]).when(
            writeln(H),
            lwriteln(T),
        ),
        lwriteln([]).when(
            nl,
        ),
    )
    db.tell(
        #
        # write out a newline:
        nl.when(
            writeln(""),
        ),
    )
    db.tell(
        #
        # reverse a list:
        reverse([X | P], Q, Y).when(
            reverse(P, [X | Q], Y),
        ),
        reverse(X, Y).when(
            reverse(X, [], Y),
        ),
        reverse([], Y, Y),
    )
    db.tell(
        arithmetic_equal(X, Y).when(
            let(Z, X),
            let(Z, Y),
        )
    )

    def database() -> Database:
        """Return a new child of the default database."""
        return db.new_child()

    return database
