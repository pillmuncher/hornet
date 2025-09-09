# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Callable

from hornet.expressions import Expression

from .combinators import (
    Clause,
    Database,
    Emit,
    Goal,
    Next,
    Result,
    Step,
    Subst,
    predicate,
    resolve,
)
from .symbols import (
    append,
    arithmetic_equal,
    arithmetic_not_equal,
    atomic,
    call,
    cut,
    equal,
    fail,
    findall,
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
    join,
    length,
    let,
    listing,
    lwriteln,
    maplist,
    member,
    nl,
    nonvar,
    numeric,
    once,
    real,
    repeat,
    reverse,
    select,
    smaller,
    tail,
    throw,
    transpose,
    true,
    unequal,
    univ,
    write,
    writeln,
)

__all__ = (
    "Clause",
    "Database",
    "Emit",
    "Goal",
    "Next",
    "Result",
    "Step",
    "Subst",
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
    "is_atom",
    "is_atomic",
    "is_bool",
    "is_bytes",
    "is_complex",
    "is_float",
    "is_int",
    "is_numeric",
    "is_str",
    "is_var",
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
    "predicate",
    "real",
    "repeat",
    "reverse",
    "select",
    "smaller",
    "tail",
    "throw",
    "transpose",
    "true",
    "unequal",
    "univ",
    "write",
    "writeln",
)


def bootstrap_database() -> Database:
    from numbers import Number

    from .combinators import Atom, Cons
    from .combinators import fail as _fail
    from .combinators import unify as _unify
    from .combinators import unit as _unit
    from .symbols import G, L, T, V, X
    from .terms import Constant, Empty, Functor, Term, Variable

    def const(value):
        return lambda *_: value

    db = Database()

    @db.tell
    @predicate(call(G))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            return resolve(subst.actualize(term.args[0]))(db, subst)

        return goal

    @db.tell
    @predicate(univ(T, L))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            """Convert between a functor/relation and its argument list (Cons only)."""

            match subst.actualize(term.args[0]), subst.actualize(term.args[1]):
                case Atom(name=name), L:
                    return _unify(L, Cons(Atom(name), Empty()))(db, subst)

                case Functor(name=name, args=args), L:
                    # Build Cons chain of head Atom + parameters
                    def build_cons(item, *items: Term) -> Term:
                        if not items:
                            return Cons(item, Empty())
                        return Cons(item, build_cons(*items))

                    return _unify(L, build_cons(Atom(name), *args))(db, subst)

                # L is a single-element Cons cell
                case _ as T, Cons(head=Atom(name), tail=Empty()):
                    return _unify(T, Atom(name))(db, subst)

                # L is a Cons chain, convert into Atom or Relation
                case _ as T, Cons(head=Atom(name), tail=tail):
                    # Collect tail elements into a list
                    items = []
                    cur = tail
                    while isinstance(cur, Cons):
                        items.append(cur.head)
                        cur = cur.tail
                    assert isinstance(cur, Empty), (
                        f"L must be a proper list ending with Empty(), got {cur!r}"
                    )
                    return _unify(T, Functor(name, *items))(db, subst)

                # fallback: error
                case T, L:
                    raise TypeError(f"Cannot unify {T} with {L}")

        return goal

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

    def check(expr: Expression, match: Callable[[Term], bool]) -> Expression:
        @predicate(expr)
        def clause(term: Functor) -> Goal:
            def goal(db: Database, subst: Subst) -> Step:
                match_term = match(subst.actualize(term.args[0]))
                return _unit(db, subst) if match_term else _fail(db, subst)

            return goal

        return clause

    db.tell(
        equal(X, X),
        check(is_atom(V), lambda term: isinstance(term, Atom)),
        check(is_atomic(V), lambda term: isinstance(term, Atom | Constant)),
        check(is_constant(V), lambda term: isinstance(term, Constant)),
        check(is_bool(V), lambda term: isinstance(term, bool)),
        check(is_bytes(V), lambda term: isinstance(term, bytes)),
        check(is_complex(V), lambda term: isinstance(term, complex)),
        check(is_float(V), lambda term: isinstance(term, float)),
        check(is_int(V), lambda term: isinstance(term, int)),
        check(is_numeric(V), lambda term: isinstance(term, Number)),
        check(is_str(V), lambda term: isinstance(term, str)),
        check(is_var(V), lambda term: isinstance(term, Variable)),
        predicate(true)(const(_unit)),
        predicate(fail)(const(_fail)),
    )

    return db


_db = bootstrap_database()


def database():
    return _db.new_child()
