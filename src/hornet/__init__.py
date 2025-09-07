# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .combinators import Atom, Cons, Database, Goal, Step, Subst
from .combinators import fail as _fail
from .combinators import predicate, unify
from .combinators import unit as _true
from .symbols import (
    L,
    T,
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
    integer,
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
from .terms import Empty, Functor, Term

__all__ = (
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
    "tail",
    "throw",
    "transpose",
    "true",
    "unequal",
    "univ",
    "write",
    "writeln",
)


_db = Database()


@predicate(univ(T, L))
def _univ(term: Functor) -> Goal:
    def goal(db: Database, subst: Subst) -> Step:
        """Convert between a functor/relation and its argument list (Cons only)."""

        T = subst.smooth(term.args[0])
        L = subst.smooth(term.args[1])

        match T, L:
            # T is an Atom or Relation, produce a Cons chain in L
            case Atom(name=name), _:
                # L = Cons(Atom(name), Empty())
                result = Cons(Atom(name), Empty())
                return unify(L, result)(db, subst)

            case Functor(name=name, args=args), _:
                # Build Cons chain of head Atom + parameters
                def build_cons(item, *items: Term) -> Term:
                    if not items:
                        return Cons(item, Empty())
                    return Cons(item, build_cons(*items))

                result = build_cons(Atom(name), *args)
                return unify(L, result)(db, subst)

            # L is a Cons chain, convert into Atom or Relation
            case _, Cons(head=head, tail=tail):
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

                return unify(T, new_term)(db, subst)

            # fallback: error
            case _:
                raise TypeError(f"Cannot unify {T} with {L}")

    return goal


def const(value):
    return lambda *_, **__: value


_db.add_action(_univ)


def database():
    return _db.new_child()
