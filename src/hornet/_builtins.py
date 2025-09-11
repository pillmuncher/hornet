# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Callable

from hornet.terms import Atomic

from .combinators import Database, Step, then

__all__ = ("_bootstrap_database",)


# Bootstrap a default database with builtins
def _bootstrap_database() -> Callable[[], Database]:
    """Add default Hornet builtins to the given database."""
    from numbers import Number

    from hornet.combinators import Atom, Cons, Goal, Subst
    from hornet.combinators import cut as _cut
    from hornet.combinators import fail as _fail
    from hornet.combinators import predicate, resolve
    from hornet.combinators import unify as _unify
    from hornet.combinators import unit as _unit
    from hornet.expressions import Expression, promote
    from hornet.terms import (
        Add,
        BitAnd,
        BitOr,
        BitXor,
        Bool,
        Complex,
        Constant,
        Div,
        Empty,
        Float,
        FloorDiv,
        Functor,
        Integer,
        Invert,
        LShift,
        Mod,
        Mult,
        Pow,
        RShift,
        Sub,
        Term,
        UAdd,
        USub,
        Variable,
    )

    from . import symbols
    from .symbols import (
        G1,
        A,
        B,
        C,
        D,
        F,
        G,
        H,
        L,
        N,
        P,
        Q,
        R,
        Rest,
        T,
        V,
        X,
        Y,
        append,
        call,
        cut,
        equal,
        fail,
        greater,
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
        true,
        unequal,
        univ,
        write,
        writeln,
    )

    # TODO: implement the following builtin predicates:
    #
    # arithmetic_equal,
    # arithmetic_not_equal,
    # findall,
    # greater,
    # join,
    # let,
    # listing,
    # smaller,
    # throw,
    # transpose,
    db = Database()

    def eval_term(term: Term) -> int | float | complex | bool:
        """Evaluate a Hornet arithmetic term into a Python number."""

        match term:
            # Base constants
            case Integer(value=v):
                return v
            case Bool(value=v):
                return v
            case Float(value=v):
                return v
            case Complex(value=v):
                return v

            # Unary operators
            case Invert(operand=a):
                r = eval_term(a)
                assert not isinstance(r, bool | float | complex)
                return ~r
            case UAdd(operand=a):
                return +eval_term(a)
            case USub(operand=a):
                return -eval_term(a)

            # Binary operators
            case LShift(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, float | complex)
                rr = eval_term(r)
                assert not isinstance(rr, float | complex)
                return rl << rr
            case RShift(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, float | complex)
                rr = eval_term(r)
                assert not isinstance(rr, float | complex)
                return rl >> rr
            case BitOr(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, float | complex)
                rr = eval_term(r)
                assert not isinstance(rr, float | complex)
                return rl | rr
            case BitXor(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, float | complex)
                rr = eval_term(r)
                assert not isinstance(rr, float | complex)
                return rl ^ rr
            case BitAnd(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, float | complex)
                rr = eval_term(r)
                assert not isinstance(rr, float | complex)
                return rl & rr
            case Add(left=l, right=r):
                return eval_term(l) + eval_term(r)
            case Sub(left=l, right=r):
                return eval_term(l) - eval_term(r)
            case Mult(left=l, right=r):
                return eval_term(l) * eval_term(r)
            case Div(left=l, right=r):
                return eval_term(l) / eval_term(r)
            case FloorDiv(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, complex)
                rr = eval_term(r)
                assert not isinstance(rr, complex)
                return rl // rr
            case Mod(left=l, right=r):
                rl = eval_term(l)
                assert not isinstance(rl, complex)
                rr = eval_term(r)
                assert not isinstance(rr, complex)
                return rl % rr
            case Pow(left=l, right=r):
                return eval_term(l) ** eval_term(r)

            # Fallback
            case _:
                raise TypeError(f"Cannot evaluate non-arithmetic term: {repr(term)}")

    def const(value):
        return lambda *_: value

    @db.tell
    @predicate(smaller(A, B))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            a = subst.actualize(term.args[0])
            b = subst.actualize(term.args[1])
            match eval_term(a), eval_term(b):
                case int() | float() as m, int() | float() as n:
                    if m < n:
                        return _unit(db, subst)
            return _fail(db, subst)

        return goal

    @db.tell
    @predicate(greater(A, B))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            a = subst.actualize(term.args[0])
            b = subst.actualize(term.args[1])
            match eval_term(a), eval_term(b):
                case int() | float() as m, int() | float() as n:
                    if m > n:
                        return _unit(db, subst)
            return _fail(db, subst)

        return goal

    @db.tell
    @predicate(let(R, F))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            r = subst.actualize(term.args[0])
            assert isinstance(r, Variable)
            f = eval_term(subst.actualize(term.args[1]))
            return then(_unify(r, promote(f)), _cut)(db, subst)

        return goal

    @db.tell
    @predicate(nonvar(G))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            if isinstance(subst.actualize(term.args[0]), Variable):
                return _fail(db, subst)
            else:
                return _unit(db, subst)

        return goal

    @db.tell
    @predicate(call(G))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            return resolve(subst.actualize(term.args[0]))(db, subst)

        return goal

    @db.tell
    @predicate(length(L, N))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            count = 0
            tail = subst.actualize(term.args[0])
            length = subst.actualize(term.args[1])
            while True:
                match tail:
                    case Empty():
                        return _unify(Constant(count), length)(db, subst)
                    case Cons(tail=tail):
                        count += 1
                    case _:
                        raise TypeError(f"list must end with [], not {tail}")

        return goal

    @db.tell
    @predicate(univ(F, L))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            match subst.actualize(term.args[0]), subst.actualize(term.args[1]):
                case Atom(name=name), L:
                    return _unify(L, Cons(Atom(name), Empty()))(db, subst)
                case Functor(name=name, args=args), L:

                    def build_cons(item, *items: Term) -> Term:
                        if not items:
                            return Cons(item, Empty())
                        return Cons(item, build_cons(*items))

                    return _unify(L, build_cons(Atom(name), *args))(db, subst)
                case _ as F, Cons(head=Atom(name), tail=Empty()):
                    return _unify(F, Atom(name))(db, subst)
                case _ as F, Cons(head=Atom(name), tail=tail):
                    items = []
                    cur = tail
                    while isinstance(cur, Cons):
                        items.append(cur.head)
                        cur = cur.tail
                    assert isinstance(cur, Empty)
                    return _unify(F, Functor(name, *items))(db, subst)
                case F, L:
                    raise TypeError(f"Cannot unify {F} with {L}")

        return goal

    # Printing predicates
    @db.tell
    @predicate(write(V))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            print(subst.actualize(term.args[0]), end="")
            return _unit(db, subst)

        return goal

    @db.tell
    @predicate(writeln(V))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            print(subst.actualize(term.args[0]))
            return _unit(db, subst)

        return goal

    # Type checking predicates
    def check(expr: Expression, match: Callable[[Term], bool]) -> Expression:
        @predicate(expr)
        def clause(term: Functor) -> Goal:
            def goal(db: Database, subst: Subst) -> Step:
                return (
                    _unit(db, subst)
                    if match(subst.actualize(term.args[0]))
                    else _fail(db, subst)
                )

            return goal

        return clause

    db.tell(
        check(is_var(V), lambda term: isinstance(term, Variable)),
        check(is_atom(V), lambda term: isinstance(term, Atom)),
        check(is_atomic(V), lambda term: isinstance(term, Atomic)),
        check(is_constant(V), lambda term: isinstance(term, Constant)),
        check(
            is_bool(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, bool),
        ),
        check(
            is_bytes(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, bytes),
        ),
        check(
            is_complex(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, complex),
        ),
        check(
            is_float(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, float),
        ),
        check(
            is_int(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, int),
        ),
        check(
            is_numeric(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, Number),
        ),
        check(
            is_str(V),
            lambda term: isinstance(term, Constant) and isinstance(term.value, str),
        ),
    )
    db.tell(
        predicate(cut)(const(_cut)),
        predicate(fail)(const(_fail)),
        predicate(true)(const(_unit)),
    )
    # from .symbols import (
    #     Args,
    #     Body,
    #     F,
    #     Head,
    #     Rule,
    #     assertz,
    #     foo,
    #     is_list,
    #     make_conjunction,
    #     rule,
    # )
    #
    # db.tell(
    #     foo(Head, Args, Body).when(
    #         is_list(Args),
    #         is_list(Body),
    #         univ(F, [Head | Args]),
    #         make_conjunction(B, Body),
    #         univ(Rule, [rule, F, B]),
    #         assertz(Rule),
    #     )
    # )
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
        # test if two terms can be unified:
        equal(X, X),
    )
    db.tell(
        #
        # test if two terms cannot be unified:
        unequal(X, X).when(~equal(X)),
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
        # test if an item occurs in a list:
        member(H, [H | T]),
        member(G, [H | T]).when(
            member(G, T),
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
        #
        # select an item from a list:
        select(X, [X | T], T),
        select(X, [H | T], [H | Rest]).when(
            select(X, T, Rest),
        ),
    )

    def database() -> Database:
        """Return a new child of the default database."""
        return db.new_child()

    return database
