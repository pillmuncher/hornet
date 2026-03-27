# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""
Modal Logic by way of Constructive Refinement.

STRUCTURE — Theory Transitions as Kleisli arrows:
    Worlds are Database instances representing constructive proof states.
    Transitions are Kleisli arrows `Database → tuple[Database, ...]`, composed via
    composition over tuples.

LOGIC POSIT:
    Modal logic is represented as a poset of information states, reflecting constructive
    transformations:
        epistemic (↓) ≼ deontic (↑) ≼ compliance
        with
            ↓ indicating refinement via information subtraction (subsets of known facts),
            ↑ indicating extension via information addition (performed obligations).

TRANSITIONS:

    - epistemic_worlds:
        Produces sub-theories by shadowing subsets of accessible facts.
        Models what remains provable under **bounded awareness** or information loss.

    - deontic_worlds:
        Produces super-theories by overlaying subsets of performed obligations.
        Models partial fulfillment and extension of duties.

    - compliance_worlds:
        Composition of epistemic and deontic transitions via `KleisliComposition`.
        Models what knowledge persists when accounting for both restricted knowledge and
        expanded obligations.

CONSTRUCTIVE VIEW:
    - Truth = provability under CWA / NAF.
    - Transitions always include the base database (identity) to satisfy **reflexivity
      (Axiom T)**.
    - All variations are generated as tuples, ensuring **serializability** and
      defunctionalized combinators.
    - `powerset` generates all subsets of facts or obligations to implement epistemic and
      deontic branching.

MODAL SEMANTICS — Persistence and Possibility:
    □φ = forall(transform, φ)  → φ holds in all resulting worlds (persistent)
    ◇φ = exists(transform, φ)  → φ holds in some resulting world (reachable)

INTERFACE:
    The modal interface predicates:
        - k(Query, Agent, T)
        - o(Query, Agent, T)
        - possibly_k(Query, Agent, T)
        - possibly_o(Query, Agent, T)
        - deemed_known(Agent, Fact, T)

NOTES:
    - The design reflects a **Hornet control algebra perspective**:
      epistemic and deontic transitions are first-class, composable, and fully
      defunctionalized.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain, combinations
from typing import Callable, Iterable, cast

from hornet.clauses import Database, Environment, Subst, predicate, resolve
from hornet.combinators import Goal, Step, amb_from_iterable, lift_ctx, neg, then
from hornet.symbols import (
    Action,
    Agent,
    Fact,
    KnownFact,
    Query,
    T,
    accessible,
    deemed_known,
    fail,
    k,
    knows,
    o,
    obligation,
    performed,
    possibly_k,
    possibly_o,
)
from hornet.terms import NonVariable, Term, const


@dataclass(frozen=True, slots=True)
class KleisliComposition[A, B, C]:
    f: Callable[[A], tuple[B, ...]]
    g: Callable[[B], tuple[C, ...]]

    def __call__(self, a: A) -> tuple[C, ...]:
        return tuple(y for x in self.f(a) for y in self.g(x))


type Transformer = Callable[[Database], tuple[Database, ...]]


@dataclass(frozen=True, slots=True)
class Branch:
    transform: Transformer

    def __call__(self, db: Database, env: Environment) -> Step[Database, Environment]:
        goals: tuple[Goal[Database, Environment], ...] = tuple(
            cast(Goal[Database, Environment], lift_ctx(const(w))) for w in self.transform(db)
        )
        return amb_from_iterable(goals)(db, env)


def exists(
    transform: Transformer, query: Goal[Database, Environment]
) -> Goal[Database, Environment]:
    return then(Branch(transform), query)


def forall(
    transform: Transformer, query: Goal[Database, Environment]
) -> Goal[Database, Environment]:
    return neg(then(Branch(transform), neg(query)))


def powerset[E](iterable: Iterable[E]) -> tuple[tuple[E, ...], ...]:

    s = list(iterable)
    return tuple(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))


@dataclass(frozen=True, slots=True)
class epistemic_worlds:
    agent: Term
    t: Term

    def __call__(self, db: Database) -> tuple[Database, ...]:
        facts: list[NonVariable] = [
            s[KnownFact]  # type: ignore
            for s in db.ask(accessible(self.agent, KnownFact, self.t))
        ]
        return tuple(db.shadow(*[f.when(fail) for f in hidden]) for hidden in powerset(facts))


@dataclass(frozen=True, slots=True)
class deontic_worlds:
    agent: Term
    t: Term

    def __call__(self, db: Database) -> tuple[Database, ...]:
        obligations: list[NonVariable] = [
            s[Action]  # type: ignore
            for s in db.ask(obligation(self.agent, Action, self.t))
        ]
        return tuple(
            db.overlay(*[performed(self.agent, act, self.t) for act in subset])
            for subset in powerset(obligations)
        )


@dataclass(frozen=True, slots=True)
class compliance_worlds:
    agent: Term
    t: Term

    def __call__(self, db: Database) -> tuple[Database, ...]:
        return KleisliComposition(
            epistemic_worlds(self.agent, self.t),
            deontic_worlds(self.agent, self.t),
        )(db)


def modal(db: Database) -> Database:
    child = db.new_child()

    @child.tell
    @predicate(k(Query, Agent, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return forall(
            epistemic_worlds(subst[Agent], subst[T]),
            resolve(subst[Query]),
        )(db, subst.env)

    @child.tell
    @predicate(o(Query, Agent, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return forall(
            deontic_worlds(subst[Agent], subst[T]),
            resolve(subst[Query]),
        )(db, subst.env)

    @child.tell
    @predicate(possibly_k(Query, Agent, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return exists(
            epistemic_worlds(subst[Agent], subst[T]),
            resolve(subst[Query]),
        )(db, subst.env)

    @child.tell
    @predicate(possibly_o(Query, Agent, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return exists(
            deontic_worlds(subst[Agent], subst[T]),
            resolve(subst[Query]),
        )(db, subst.env)

    @child.tell
    @predicate(deemed_known(Agent, Fact, T))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return forall(
            compliance_worlds(subst[Agent], subst[T]),
            resolve(knows(subst[Agent], subst[Fact], subst[T])),
        )(db, subst.env)

    return child
