# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Callable

from hornet.expressions import Expression
from hornet.terms import Variable

from .combinators import (
    Clause,
    ClauseTerm,
    Database,
    Emit,
    Goal,
    MatchTerm,
    Next,
    PythonClause,
    QueryTerm,
    Result,
    Step,
    Subst,
    predicate,
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
    "ClauseTerm",
    "Database",
    "Emit",
    "Goal",
    "MatchTerm",
    "Next",
    "QueryTerm",
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
    from .symbols import L, T, V
    from .terms import Constant, Empty, Functor, Term

    def const(value):
        return lambda *_, **__: value

    db = Database()

    @db.tell
    @predicate(univ(T, L))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            """Convert between a functor/relation and its argument list (Cons only)."""

            match subst.actualize(term.args[0]), subst.actualize(term.args[1]):
                # T is an Atom or Relation, produce a Cons chain in L
                case Atom(name=name), L:
                    # L = Cons(Atom(name), Empty())
                    result = Cons(Atom(name), Empty())
                    return _unify(L, result)(db, subst)

                case Functor(name=name, args=args), L:
                    # Build Cons chain of head Atom + parameters
                    def build_cons(item, *items: Term) -> Term:
                        if not items:
                            return Cons(item, Empty())
                        return Cons(item, build_cons(*items))

                    result = build_cons(Atom(name), *args)
                    return _unify(L, result)(db, subst)

                # L is a Cons chain, convert into Atom or Relation
                case _ as T, Cons(head=head, tail=tail):
                    # head must be an Atom
                    if not isinstance(head, Atom):
                        raise TypeError(
                            f"First element of L must be Atom, got {type(head)}"
                        )

                    # Collect tail elements into a list
                    items = []
                    cur = tail
                    while isinstance(cur, Cons):
                        items.append(cur.head)
                        cur = cur.tail
                    if not isinstance(cur, Empty):
                        raise TypeError(
                            f"L must be a proper list ending with Empty(), got {cur}"
                        )

                    if items:
                        new_term = Functor(head.name, *items)
                    else:
                        new_term = Atom(head.name)

                    return _unify(T, new_term)(db, subst)

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

    def check(
        expr: Expression[Term], match: Callable[[Term], bool]
    ) -> Expression[PythonClause]:
        @predicate(expr)
        def clause(term: Functor) -> Goal:
            def goal(db: Database, subst: Subst) -> Step:
                match_term = match(subst.actualize(term.args[0]))
                return _unit(db, subst) if match_term else _fail(db, subst)

            return goal

        return clause

    db.tell(
        check(is_atomic(V), lambda term: isinstance(term, Atom | Constant)),
        check(is_atom(V), lambda term: isinstance(term, Atom)),
        check(is_var(V), lambda term: isinstance(term, Variable)),
        check(is_int(V), lambda term: isinstance(term, int)),
        check(is_bool(V), lambda term: isinstance(term, bool)),
        check(is_float(V), lambda term: isinstance(term, float)),
        check(is_complex(V), lambda term: isinstance(term, complex)),
        check(is_numeric(V), lambda term: isinstance(term, Number)),
        check(is_str(V), lambda term: isinstance(term, str)),
        check(is_bytes(V), lambda term: isinstance(term, bytes)),
        predicate(true)(const(_unit)),
        predicate(fail)(const(_fail)),
    )

    return db


_db = bootstrap_database()


def database():
    return _db.new_child()
