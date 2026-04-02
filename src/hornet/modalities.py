# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""
Modal Logic by way of Constructive World Generation.

STRUCTURE:
    Worlds are generated variants of a root Database that represent
    constructive proof states.

    Accessibility is not given as a relation but instead as generators
    `Database → tuple[Database, ...]` that produce alternative worlds via
    systematic transformations.

    Modal structure arises from quantification over these generated worlds.

LOGIC POSIT:
    Modal logic is represented as an algebra of information states under
    constructive transformations:

        epistemic (↓)   : information restriction (shadowing facts)
        deontic   (↑)   : information extension (overlaying actions)

    These transformations are asymmetric:
        ↓ is generally non-monotone (information removal)
        ↑ is monotone (information addition)

    Modal interactions are expressed by *nesting quantifiers* over generators,
    rather than composing transitions.

TRANSITIONS:

    - epistemic_worlds:
        Produces sub-theories by shadowing subsets of accessible facts.
        Models bounded awareness and information loss.

    - deontic_worlds:
        Produces super-theories by overlaying subsets of performed obligations.
        Models partial fulfillment and extension of duties.

CONSTRUCTIVE VIEW:
    - Truth = provability under CWA / NAF.
    - Worlds are *constructed*, not assumed; possibility = generability.
    - Transitions include the base database (identity), ensuring reflexivity (Axiom T).
    - `powerset` enumerates systematic variants for epistemic and deontic branching.

MODAL SEMANTICS:
    Modal operators are quantifiers over generated worlds:
    - □φ = forall(generator, φ)  → φ holds in all generated worlds
    - ◇φ = exists(generator, φ)  → φ holds in some generated world

    Nested modalities retain constructive structure:
        - ∀ₒ (∃ₖ φ) – φ could be known for every obligation.
        - ∀ₖ (∃ₒ φ) – For every epistemic state, some obligation makes φ hold.
        - ∃ₒ (∀ₖ φ) – Some duty guarantees φ in all epistemic states.
        - ∃ₖ (∀ₒ φ) – Knowledge state ensures φ regardless of duties.
        - ∀ₒ (∀ₖ φ) – Knowledge-invariant across all obligations.
        - ∀ₖ (∀ₒ φ) – Knowledge-relative normative invariance.
        - ∃ₒ (∃ₖ φ) – φ is possible in at least one knowledge-obligation scenario.
        - ∃ₖ (∃ₒ φ) – There exists a knowledge-obligation pair making φ true.

        Note:  ∀_ (∀ₒ _φ) and ∃_ (∃_ φ) are just Kleisli compositions, therefor
        - ∀ₒ (∀ₖ φ) ≡ ∀ₖ (∀ₒ φ)
        - ∃ₒ (∃ₖ φ) ≡ ∃ₖ (∃ₒ φ)

    Each combination is realized constructively as a tuple of generated worlds,
    preserving the algebraic structure of knowledge and obligation transitions.

INTERFACE:
    The modal interface predicates:
        - k(Query, Agent, T)
        - o(Query, Agent, T)
        - possibly_k(Query, Agent, T)
        - possibly_o(Query, Agent, T)
        - deemed_known(Agent, Fact, T)

NOTES:
    - Accessibility is *generative*, not relational: a world-transforming operation
      rather than a predicate over pairs of worlds.
    - The system is closer to an algebra of worldmaking (in the Goodmanian sense)
      than to classical Kripke semantics.
    - The design reflects a Hornet control algebra perspective: generators and
      quantifiers are first-class, composable, and fully defunctionalized.
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
    o,
    obligation,
    performed,
    possibly_k,
    possibly_o,
)
from hornet.terms import NonVariable, Term, const

type WorldGenerator = Callable[[Database], tuple[Database, ...]]


@dataclass(frozen=True, slots=True)
class Branch:
    generator: WorldGenerator

    def __call__(self, db: Database, env: Environment) -> Step[Database, Environment]:
        goals: tuple[Goal[Database, Environment], ...] = tuple(
            cast(Goal[Database, Environment], lift_ctx(const(w))) for w in self.generator(db)
        )
        return amb_from_iterable(goals)(db, env)


def exists(
    generator: WorldGenerator,
    query: Goal[Database, Environment],
) -> Goal[Database, Environment]:
    return then(Branch(generator), query)


def forall(
    generator: WorldGenerator,
    query: Goal[Database, Environment],
) -> Goal[Database, Environment]:
    return neg(then(Branch(generator), neg(query)))


def powerset[E](iterable: Iterable[E]) -> tuple[tuple[E, ...], ...]:
    s = list(iterable)
    return tuple(chain.from_iterable(combinations(s, r) for r in range(len(s) + 1)))


@dataclass(frozen=True, slots=True)
class epistemic_worlds:
    agent: Term
    t: Term

    def __call__(self, db: Database) -> tuple[Database, ...]:
        facts: list[NonVariable] = [
            cast(NonVariable, s[KnownFact])
            for s in db.ask(accessible(self.agent, KnownFact, self.t))
        ]
        return tuple(db.shadow(*[f.when(fail) for f in hidden]) for hidden in powerset(facts))


@dataclass(frozen=True, slots=True)
class deontic_worlds:
    agent: Term
    t: Term

    def __call__(self, db: Database) -> tuple[Database, ...]:
        obligations: list[NonVariable] = [
            cast(NonVariable, s[Action]) for s in db.ask(obligation(self.agent, Action, self.t))
        ]
        return tuple(
            db.overlay(*[performed(self.agent, act, self.t) for act in subset])
            for subset in powerset(obligations)
        )


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
        # ∀ₒ (∃ₖ accessible(...))
        return forall(
            deontic_worlds(subst[Agent], subst[T]),
            exists(
                epistemic_worlds(subst[Agent], subst[T]),
                resolve(accessible(subst[Agent], subst[Fact], subst[T])),
            ),
        )(db, subst.env)

    return child
