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

    @db.add_action
    @predicate(univ(T, L))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            """Convert between a functor/relation and its argument list (Cons only)."""

            match subst.smooth(term.args[0]), subst.smooth(term.args[1]):
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

    @db.add_action
    @predicate(write(V))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            print(subst.smooth(term.args[0]), end="")
            return _unit(db, subst)

        return goal

    @db.add_action
    @predicate(writeln(V))
    def _(term: Functor) -> Goal:
        def goal(db: Database, subst: Subst) -> Step:
            print(subst.smooth(term.args[0]))
            return _unit(db, subst)

        return goal

    def is_category(fn: Expression[Functor], match: Callable[[Term], bool]) -> Clause:
        @predicate(fn)
        def clause(term: Functor) -> Goal:
            def goal(db: Database, subst: Subst) -> Step:
                match_term = match(subst.smooth(term.args[0]))
                return _unit(db, subst) if match_term else _fail(db, subst)

            return goal

        return clause

    def match_atom(term: Term) -> bool:
        return isinstance(term, Atom)

    def match_atomic(term: Term) -> bool:
        return isinstance(term, Atom | Constant)

    def match_variable(term: Term) -> bool:
        return isinstance(term, Variable)

    db.add_action(is_category(is_atom(V), match_atom))
    db.add_action(is_category(is_atomic(V), match_atomic))
    db.add_action(is_category(is_var(V), match_variable))

    def is_type(head: Expression[Functor], T: type) -> Clause:
        @predicate(head)
        def clause(term: Functor) -> Goal:
            def goal(db: Database, subst: Subst) -> Step:
                value = subst.smooth(term.args[0])
                if isinstance(value, Constant) and isinstance(value.value, T):
                    return _unit(db, subst)
                else:
                    return _fail(db, subst)

            return goal

        return clause

    db.add_action(is_type(is_int(V), int))
    db.add_action(is_type(is_bool(V), bool))
    db.add_action(is_type(is_float(V), float))
    db.add_action(is_type(is_complex(V), complex))
    db.add_action(is_type(is_numeric(V), Number))
    db.add_action(is_type(is_str(V), str))
    db.add_action(is_type(is_bytes(V), bytes))

    db.add_action(predicate(true)(const(_unit)))
    db.add_action(predicate(fail)(const(_fail)))

    return db


_db = bootstrap_database()


def database():
    return _db.new_child()
