# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""
Kripke-style epistemic and deontic modal operators for Hornet.

SEMANTICS — Epistemic worlds (k / possibly_k):
    Accessible worlds are all subsets of accessible facts the agent could have
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

    World *construction* (enumerating accessible facts / obligations) still
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
    If no worlds are accessible (e.g. no obligations, no accessible facts),
    box vacuously succeeds and diamond fails. This follows from the standard
    Kripke definition: all-w-in-empty.phi is trivially true; exists-w-in-empty
    is false. With the powerset construction the empty subset is always
    included, so this case arises only when the outer set is itself empty —
    meaning the single accessible world is the unmodified database.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain, combinations
from typing import Iterable, Iterator, cast

from hornet.clauses import Database, Environment, Subst, predicate, resolve
from hornet.combinators import Step, amb_from_iterable, neg, then, unit
from hornet.symbols import (
    Action,
    Agent,
    KnownFact,
    Query,
    T,
    _,
    accessible,
    compliance_world,
    epistemic_world,
    fail,
    k,
    o,
    obligation,
    performed,
    possibly_k,
    possibly_o,
)
from hornet.terms import NonVariable


def powerset[E](iterable: Iterable[E]) -> Iterator[tuple[E, ...]]:
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


@dataclass(frozen=True, slots=True)
class switch:
    target_db: Database

    def __call__(self, _current_db: Database, env: Environment) -> Step[Database, Environment]:
        return unit(self.target_db, env)


def modal(db: Database) -> Database:
    child = db.new_child()

    # Epistemic worlds: generate all accessible worlds for an agent at time T
    # as powersets of accessible facts. Each world hides a different subset of
    # facts to model bounded awareness.
    @child.tell
    @predicate(epistemic_world(Agent, KnownFact, T))
    def _epistemic_world(db: Database, subst: Subst) -> Step[Database, Environment]:
        agent = subst[Agent]
        t = subst[T]

        # Only consider facts that this agent could have known at time t
        facts: list[NonVariable] = [
            cast(NonVariable, s[KnownFact]) for s in db.ask(accessible(agent, KnownFact, t))
        ]

        # Construct all possible worlds: subsets of facts, modeling partial awareness
        return amb_from_iterable(
            tuple(switch(db.shadow(*[f.when(fail) for f in hidden])) for hidden in powerset(facts))
        )(db, subst.env)

    # Compliance worlds: generate all accessible worlds for an agent at time T
    # as powersets of obligations. Each world represents a different pattern of
    # performed obligations.
    @child.tell
    @predicate(compliance_world(Agent, Action, T))
    def _compliance_world(db: Database, subst: Subst) -> Step[Database, Environment]:
        agent = subst[Agent]
        t = subst[T]
        obligations: list[NonVariable] = [
            cast(NonVariable, s[Action]) for s in db.ask(obligation(agent, Action, t))
        ]
        if not obligations:
            return unit(db, subst.env)
        return amb_from_iterable(
            tuple(
                switch(db.overlay(*[performed(agent, act, t) for act in subset]))
                for subset in powerset(obligations)
            )
        )(db, subst.env)

    # Box epistemic operator: k(Query, Agent, T) succeeds iff Query holds in
    # all epistemic worlds accessible to the agent.
    @child.tell
    @predicate(k(Query, Agent, T))
    def _k(db: Database, subst: Subst) -> Step[Database, Environment]:
        query = resolve(subst[Query])
        access = resolve(epistemic_world(subst[Agent], _, subst[T]))
        return neg(then(access, neg(query)))(db, subst.env)

    # Box deontic operator: o(Query, Agent, T) succeeds iff Query holds in all
    # compliance worlds (all obligation fulfillment patterns).
    @child.tell
    @predicate(o(Query, Agent, T))
    def _o(db: Database, subst: Subst) -> Step[Database, Environment]:
        query = resolve(subst[Query])
        access = resolve(compliance_world(subst[Agent], _, subst[T]))
        return neg(then(access, neg(query)))(db, subst.env)

    # Diamond epistemic operator: possibly_k(Query, Agent, T) succeeds if Query
    # holds in at least one epistemic world.
    @child.tell
    @predicate(possibly_k(Query, Agent, T))
    def _k_possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
        query = resolve(subst[Query])
        access = resolve(epistemic_world(subst[Agent], _, subst[T]))
        return then(access, query)(db, subst.env)

    # Diamond deontic operator: possibly_o(Query, Agent, T) succeeds if Query
    # holds in at least one compliance world.
    @child.tell
    @predicate(possibly_o(Query, Agent, T))
    def _o_possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
        query = resolve(subst[Query])
        access = resolve(compliance_world(subst[Agent], _, subst[T]))
        return then(access, query)(db, subst.env)

    return child
