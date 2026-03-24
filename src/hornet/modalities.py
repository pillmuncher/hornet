# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""
Kripke-style epistemic and deontic modal operators for Hornet.

SEMANTICS — Epistemic worlds (k / possibly_k):
    Accessible worlds are all subsets of knowable facts the agent could have
    received (powerset of accessible information). This models *bounded/partial
    awareness* rather than standard S5: an agent may have observed only a
    subset of available evidence. k(φ) holds iff φ is true in every such world
    — i.e., φ survives any pattern of missing information. This is strictly
    stronger than S5 □_K, which would require only that φ holds given full
    awareness.

SEMANTICS — Compliance worlds (o / possibly_o):
    Accessible worlds are all subsets of obligations the agent could have
    performed (powerset of obligations).
      o(φ)          holds iff φ holds in every compliance world, including the
                    one where no obligations are met.
      possibly_o(φ) holds iff φ holds in some partial-compliance world.

IMPLEMENTATION — Box and diamond as combinator composition:
    Modal operators are expressed without a nested trampoline by encoding
    standard Kripke semantics via neg/then:

        ◇φ  =  then(access, query)
        □φ  =  neg(then(access, neg(query)))

    The `choice` combinator captures (db, env) at choice-point creation time,
    so backtracking through `neg` correctly restores the pre-switch database.
    Query evaluation is fully integrated into the outer trampoline.

    World *construction* (enumerating knowable facts / obligations) still
    requires a db.ask call inside _epistemic_world and _compliance_world, but
    that nesting is constant-depth regardless of modal nesting depth. With the
    old collect_worlds/succeeds approach, every level of o(k(o(...))) added
    another trampoline; now it does not.

KNOWN LIMITATION — Box operators are purely boolean:
    k and o do not propagate variable bindings outward. Any unifications
    produced inside a box evaluation remain local and are discarded by the
    double-neg structure.
    Diamond operators (possibly_k, possibly_o) do propagate bindings.

KNOWN LIMITATION — World construction is still eager:
    _epistemic_world and _compliance_world call db.ask to enumerate
    facts/obligations before constructing the powerset of worlds. This is
    unavoidable: the powerset cannot be computed lazily without knowing all
    elements upfront.

VACUOUS TRUTH — empty accessibility:
    If no worlds are accessible (e.g. no obligations, no knowable facts),
    box vacuously succeeds and diamond fails. This follows from the standard
    Kripke definition: all-w-in-empty.phi is trivially true; exists-w-in-empty
    is false. With the powerset construction the empty subset is always
    included, so this case arises only when the outer set is itself empty —
    meaning the single accessible world is the unmodified database.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import chain, combinations
from typing import cast

import hornet.combinators as combinators
from hornet.clauses import Database, Environment, Subst, predicate, resolve
from hornet.combinators import Goal, Step, amb_from_iterable, neg, then
from hornet.symbols import (
    E2,
    L2,
    T1,
    T2,
    Action,
    Agent,
    Event,
    Init,
    KnownFact,
    L,
    Query,
    T,
    _,
    append,
    call,
    compliance_world,
    currently,
    epistemic_world,
    fail,
    greater,
    k,
    knowable,
    no_later_than,
    o,
    obligation,
    performed,
    possibly_k,
    possibly_o,
    superseding,
    univ,
)
from hornet.terms import NonVariable


def powerset[E](iterable: Iterable[E]) -> Iterator[tuple[E, ...]]:
    """Generate all subsets of `iterable`.
    Note: the input is eagerly converted to a list, so the function is not
    fully lazy in terms of memory consumption. Subsets themselves are
    generated lazily.
    """
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def switch(w: Database) -> Goal[Database, Environment]:
    """Switch execution into world w, preserving the current substitution environment."""

    def goal(_db: Database, env: Environment) -> Step[Database, Environment]:
        return combinators.unit(w, env)

    return goal


@predicate(epistemic_world(Agent, KnownFact, T))
def _epistemic_world(db: Database, subst: Subst) -> Step[Database, Environment]:
    agent = subst[Agent]
    t = subst[T]

    facts: list[NonVariable] = [
        cast(NonVariable, s[KnownFact]) for s in db.ask(knowable(agent, KnownFact, t))
    ]

    # Each accessible world hides a different subset of knowable facts.
    # Powerset ranges from "agent saw everything" (no facts hidden)
    # to "agent saw nothing" (all facts hidden).
    # Inlined generator to avoid unnecessary function indirection.
    return amb_from_iterable(
        tuple(switch(db.shadow(*[f.when(fail) for f in hidden])) for hidden in powerset(facts))
    )(db, subst.env)


@predicate(compliance_world(Agent, Action, T))
def _compliance_world(db: Database, subst: Subst) -> Step[Database, Environment]:
    agent = subst[Agent]
    t = subst[T]

    obligations: list[NonVariable] = [
        cast(NonVariable, s[Action]) for s in db.ask(obligation(agent, Action, t))
    ]

    # Each accessible compliance world overlays a different subset of obligations.
    # o(φ) requires φ in all subsets (including the empty one);
    # possibly_o(φ) requires φ in at least one.
    # Inlined generator to avoid unnecessary function indirection.
    return amb_from_iterable(
        tuple(
            switch(db.overlay(*[performed(agent, act, t) for act in subset]))
            for subset in powerset(obligations)
        )
    )(db, subst.env)


@predicate(possibly_k(Query, Agent, T))
def _k_possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
    query = resolve(subst[Query])
    access = resolve(epistemic_world(subst[Agent], _, subst[T]))
    return then(access, query)(db, subst.env)


@predicate(possibly_o(Query, Agent, T))
def _o_possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
    query = resolve(subst[Query])
    access = resolve(compliance_world(subst[Agent], _, subst[T]))
    return then(access, query)(db, subst.env)


@predicate(k(Query, Agent, T))
def _k(db: Database, subst: Subst) -> Step[Database, Environment]:
    query = resolve(subst[Query])
    access = resolve(epistemic_world(subst[Agent], _, subst[T]))
    return neg(then(access, neg(query)))(db, subst.env)


@predicate(o(Query, Agent, T))
def _o(db: Database, subst: Subst) -> Step[Database, Environment]:
    query = resolve(subst[Query])
    access = resolve(compliance_world(subst[Agent], _, subst[T]))
    return neg(then(access, neg(query)))(db, subst.env)


def modal(db: Database) -> Database:
    child = db.new_child()
    child.tell(
        no_later_than(T1, T2).when(~greater(T1, T2)),
        currently(Event, T).when(
            call(Event),
            univ(Event, L),
            append(Init, [T1], L),
            no_later_than(T1, T),
            ~superseding(Event, Init, T1, T),
        ),
        superseding(_, Init, T1, T).when(
            append(Init, [T2], L2),
            univ(E2, L2),
            call(E2),
            greater(T2, T1),
            no_later_than(T2, T),
        ),
        epistemic_world(Agent, KnownFact, T),
        compliance_world(Agent, Action, T),
        possibly_k(Query, Agent, T),
        possibly_o(Query, Agent, T),
        k(Query, Agent, T),
        o(Query, Agent, T),
    )

    return child
