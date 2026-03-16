# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

# Modal compliance reasoning on top of Hornet.
#
# Architecture
# ------------
# Three clause sources feed a time-sliced Hornet database:
#
#   domain_events    -- business facts recorded by the operational system
#                       e.g. transaction/4, report_generated/3
#
#   normative_acts   -- compliance-significant actions recorded by the
#                       compliance system e.g. approved_report/3,
#                       assigned_role/3, came_into_force/2
#
#   epistemic_attrs  -- knowledge attributions, either recorded
#                       (notified/3, completed_training/3) or derived
#                       from normative acts via Horn rules
#
# All three are append-only streams of time-stamped Horn facts.
# Rules are also time-indexed via came_into_force/expired_at and are
# pre-filtered to those in force at query time.
#
# The world at time T is:
#
#   W(T) = domain_events[:T] ∪ normative_acts[:T] ∪ rules_in_force(T)
#
# Modal reasoning is implemented as a WorldGen algebra:
#
#   WorldGen : Database -> Iterable[Database]
#
# which forms the same distributive lattice as Hornet's goal combinators
# (wg_then/wg_unit and wg_choice/wg_fail), but operates one level above
# the Horn solver. The solver is never modified.
#
# Modal operators are folds over generated worlds:
#
#   necessity  = all worlds satisfy the query
#   possibility = some world satisfies the query
#
# The legal attribution predicate treated_as_known/3 collapses the modal
# reasoning into a ground fact suitable for audit queries.

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from hornet import database
from hornet.clauses import Database, Indicator
from hornet.symbols import (
    T0,
    T1,
    Action,
    Agent,
    F,
    Fact,
    T,
    after,
    completed_training,
    fail,
    greater,
    learned,
    notified,
    obligation,
    performed,
    required_event,
    should_have_known,
    treated_as_known,
)
from hornet.terms import NonVariable

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type Timestamp = int | float
type WorldGen = Callable[[Database], Iterable[Database]]


# ---------------------------------------------------------------------------
# Clause source records
# ---------------------------------------------------------------------------


@dataclass
class DomainEvent:
    """A material fact recorded by the operational system."""

    term: Any  # Hornet term e.g. transaction(tx17, alice, 250000, t1)
    time: Timestamp


@dataclass
class NormativeAct:
    """A compliance-significant action or regulatory event."""

    term: Any  # e.g. came_into_force(approve_deadline(cfo), t0)
    time: Timestamp


@dataclass
class EpistemicAttribution:
    """
    A recorded knowledge attribution.

    Derived epistemic attributions (e.g. learned/3 inferred from reviewed/3)
    are not stored here — they are produced by Horn rules in the rule layer.
    Only ground attributions recorded by the compliance system appear here.
    """

    term: Any  # e.g. notified(alice, policy_update, t3)
    time: Timestamp


@dataclass
class RuleClause:
    """
    A Horn rule with a validity interval.

    came_into_force marks the start; supersession by a later version of the
    same rule (same identity) marks the end. Rules are never explicitly
    retracted — supersession is derived.
    """

    term: Any  # Hornet rule term (head.when(*body))
    identity: str  # rule identity for supersession e.g. 'approve_deadline_cfo'
    effective: Timestamp  # time came into force


# ---------------------------------------------------------------------------
# Clause source store
# ---------------------------------------------------------------------------


@dataclass
class ClauseStore:
    """
    Append-only store for all three clause sources plus rules.

    Pre-filtering at world construction time keeps the Hornet search space
    small. Python-level filtering is cheap; Horn resolution is not.
    """

    domain_events: list[DomainEvent] = field(default_factory=list)
    normative_acts: list[NormativeAct] = field(default_factory=list)
    epistemic_attrs: list[EpistemicAttribution] = field(default_factory=list)
    rules: list[RuleClause] = field(default_factory=list)

    def append_domain(self, term: Any, time: Timestamp) -> None:
        self.domain_events.append(DomainEvent(term, time))

    def append_normative(self, term: Any, time: Timestamp) -> None:
        self.normative_acts.append(NormativeAct(term, time))

    def append_epistemic(self, term: Any, time: Timestamp) -> None:
        self.epistemic_attrs.append(EpistemicAttribution(term, time))

    def append_rule(self, term: Any, identity: str, effective: Timestamp) -> None:
        self.rules.append(RuleClause(term, identity, effective))

    # ------------------------------------------------------------------
    # Query-driven pre-filtering
    # ------------------------------------------------------------------

    def domain_at(
        self, t: Timestamp, relevant: Callable[[DomainEvent], bool] | None = None
    ) -> Iterable[Any]:
        """Domain events up to and including t, optionally filtered by relevance."""
        for e in self.domain_events:
            if e.time <= t and (relevant is None or relevant(e)):
                yield e.term

    def normative_at(
        self, t: Timestamp, relevant: Callable[[NormativeAct], bool] | None = None
    ) -> Iterable[Any]:
        """Normative acts up to and including t, optionally filtered."""
        for a in self.normative_acts:
            if a.time <= t and (relevant is None or relevant(a)):
                yield a.term

    def epistemic_at(
        self, t: Timestamp, relevant: Callable[[EpistemicAttribution], bool] | None = None
    ) -> Iterable[Any]:
        """Recorded epistemic attributions up to and including t."""
        for e in self.epistemic_attrs:
            if e.time <= t and (relevant is None or relevant(e)):
                yield e.term

    def rules_in_force_at(self, t: Timestamp) -> Iterable[Any]:
        """
        Rules in force at t after supersession.

        A rule R with identity I is in force at t iff:
          - R.effective <= t
          - no later version of I came into force before t

        Rules are never retracted; supersession is derived here in Python
        rather than inside Hornet, as a pre-filtering optimisation.
        """
        # For each identity, keep only the version with the latest effective
        # timestamp that is still <= t.
        latest: dict[str, RuleClause] = {}
        for r in self.rules:
            if r.effective <= t:
                if r.identity not in latest or r.effective > latest[r.identity].effective:
                    latest[r.identity] = r
        for r in latest.values():
            yield r.term


# ---------------------------------------------------------------------------
# Base world construction
# ---------------------------------------------------------------------------


def base_world(
    store: ClauseStore,
    t: Timestamp,
    domain_filter: Callable[[DomainEvent], bool] | None = None,
    normative_filter: Callable[[NormativeAct], bool] | None = None,
    epistemic_filter: Callable[[EpistemicAttribution], bool] | None = None,
) -> Database:
    """
    Construct the actual world W(t) as a Hornet database.

    The result is a time-sliced ChainMap containing:
      - domain events[:t]
      - normative acts[:t]
      - epistemic attributions[:t]
      - rules in force at t (after supersession)
      - inference rules (see _assert_inference_rules)

    Optional filters allow query-driven pre-filtering: only clauses
    relevant to the query at hand need be asserted.
    """
    db = database()

    db.tell(
        *store.domain_at(t, domain_filter),
        *store.normative_at(t, normative_filter),
        *store.epistemic_at(t, epistemic_filter),
        *store.rules_in_force_at(t),
    )

    _assert_inference_rules(db)

    return db


def _assert_inference_rules(db: Database) -> None:
    """
    Core modal inference rules, domain-agnostic.

    These rules constitute the modality layer proper. They operate
    entirely on generic epistemic and deontic predicates:
    learned/3, obligation/3, performed/3, required_event/3,
    treated_as_known/3, should_have_known/3.

    No domain concepts (reports, roles, transactions) appear here.
    Domain-specific rules belong in the caller's rule layer, asserted
    via ClauseStore.append_rule().
    """
    dynamic(
        db,
        ('notified', 3),
        ('completed_training', 3),
        ('performed', 3),
        ('obligation', 3),
        ('learned', 3),
        ('should_have_known', 3),
    )

    db.tell(
        # after/2 — the only temporal primitive.
        after(T0, T1).when(greater(T0, T1)),
        # Knowledge from recorded attributions.
        learned(Agent, Fact, T).when(notified(Agent, Fact, T)),
        learned(Agent, Fact, T).when(completed_training(Agent, Fact, T)),
        # Legal attribution: actual or constructive knowledge.
        # Audit queries use treated_as_known/3 as their entry point.
        treated_as_known(Agent, Fact, T).when(
            learned(Agent, Fact, T),
        ),
        treated_as_known(Agent, Fact, T).when(
            should_have_known(Agent, Fact, T),
        ),
        # Obligation bridge: what must be performed to satisfy obligations.
        required_event(Agent, Action, T).when(
            obligation(Agent, Action, T),
        ),
    )


def dynamic(db: Database, *indicators: Indicator) -> None:
    for indicator in indicators:
        db.setdefault(indicator, [])


# ---------------------------------------------------------------------------
# World generator algebra
# ---------------------------------------------------------------------------
#
# WorldGen = Database -> Iterable[Database]
#
# Algebraic structure:
#   (WorldGen, wg_then, wg_unit)  — monoid
#   (WorldGen, wg_choice, wg_fail) — monoid
#   together: distributive lattice
#
# This mirrors exactly the structure of Hornet's goal combinators
# (then/unit, choice/fail), but operates on worlds rather than goals.


def wg_unit(world: Database) -> Iterable[Database]:
    """Identity for wg_then. Yields the world unchanged."""
    yield world


def wg_fail(world: Database) -> Iterable[Database]:  # noqa: ARG001
    """Identity for wg_choice. Yields nothing."""
    return iter(())


def wg_then(g1: WorldGen, g2: WorldGen) -> WorldGen:
    """Sequential composition. Apply g2 to every world produced by g1."""

    def composed(world: Database) -> Iterable[Database]:
        for w1 in g1(world):
            yield from g2(w1)

    return composed


def wg_choice(*gs: WorldGen) -> WorldGen:
    """Branching. Yield worlds from all generators."""

    def branched(world: Database) -> Iterable[Database]:
        for g in gs:
            yield from g(world)

    return branched


def wg_overlay(*clauses: Any) -> WorldGen:
    """
    Add clauses to a new child world.

    Used for compliance worlds (additive overlay: procedural events)
    and epistemic worlds (subtractive overlay: shadow facts to fail).
    """

    def gen(world: Database) -> Iterable[Database]:
        child = world.new_child()
        if clauses:
            child.tell(*clauses)
        yield child

    return gen


def wg_filter(predicate: Callable[[Database], bool]) -> WorldGen:
    """Accessibility constraint. Pass the world through only if predicate holds."""

    def gen(world: Database) -> Iterable[Database]:
        if predicate(world):
            yield world

    return gen


# ---------------------------------------------------------------------------
# Derived generators
# ---------------------------------------------------------------------------


def compliance_gen(world: Database, agent: Any, t: Timestamp) -> WorldGen:
    """
    Generate the minimal compliance world for agent at time t.

    Queries the base world for required_event/3 facts and produces a
    single child world where all required procedural events are asserted
    as performed/3 facts. This is the deontic accessibility relation:
    worlds where the agent fulfilled their obligations.
    """

    overlays = [
        performed(agent, s[Action], t) for s in world.ask(required_event(agent, Action, t))
    ]
    return wg_overlay(*overlays) if overlays else wg_unit


def epistemic_gen(
    world: Database,
    agent: Any,
    t: Timestamp,
    hidden_query: Any,  # Hornet goal enumerating potentially hidden facts
) -> WorldGen:
    """
    Generate epistemic worlds by branching over hidden facts.

    For each fact that agent may not have observed at t, yields:
      - a world where the fact is visible (no overlay)
      - a world where the fact is retracted (shadowed to fail)

    The hidden_query argument is a Hornet goal that enumerates the
    candidate facts subject to epistemic uncertainty. What counts as
    hidden is determined by the normative stream: a fact is hidden if
    no corresponding learned/notified/observed attribution exists for
    the agent at or before t.
    """

    branches: list[WorldGen] = []

    for s in world.ask(hidden_query):
        f = s[F]
        if not isinstance(f, NonVariable):
            raise TypeError(f'Expected NonVariable in epistemic retraction, got {f!r}')
        # world where agent has seen the fact
        branches.append(wg_unit)
        # world where the fact is retracted via negation-as-failure shadowing:
        # assert f :- fail, which makes f unprovable in this world.

        branches.append(wg_overlay(f.when(fail)))

    return wg_choice(*branches) if branches else wg_unit


# ---------------------------------------------------------------------------
# Modal folds
# ---------------------------------------------------------------------------


def _evaluate(gen: WorldGen, world: Database, query: Any) -> list[bool]:
    return [bool(list(w.ask(query))) for w in gen(world)]


def necessity(gen: WorldGen, world: Database, query: Any) -> bool:
    """□φ — query holds in all accessible worlds (and at least one exists)."""
    # Non-empty requirement: necessity over an empty world set is False,
    # not True. An agent with no obligations cannot have constructive
    # knowledge attributed via compliance worlds.
    results = _evaluate(gen, world, query)
    return bool(results) and all(results)


def possibility(gen: WorldGen, world: Database, query: Any) -> bool:
    """◇φ — query holds in at least one accessible world."""
    return any(_evaluate(gen, world, query))


def impossibility(gen: WorldGen, world: Database, query: Any) -> bool:
    """¬◇φ — query holds in no accessible world."""
    return not possibility(gen, world, query)


# ---------------------------------------------------------------------------
# Modal query interface
# ---------------------------------------------------------------------------


def query_should_have_known(
    world: Database,
    agent: Any,
    fact_query: Any,
    t: Timestamp,
    hidden_query: Any | None = None,
) -> bool:
    """
    Evaluate: should agent have known fact at time t?

    Constructs epistemic-compliance worlds and tests necessity.

    Pipeline:
      base world
        -> epistemic worlds  (what the agent might not have seen)
        -> compliance worlds (what procedures would reveal)
        -> necessity fold    (fact derivable in all of them)

    If hidden_query is None, skips epistemic branching and evaluates
    purely over the single compliance world — sufficient for cases where
    the knowledge gap is purely procedural rather than observational.
    """

    if hidden_query is not None:
        gen = wg_then(
            epistemic_gen(world, agent, t, hidden_query),
            compliance_gen(world, agent, t),
        )
    else:
        gen = compliance_gen(world, agent, t)
    return necessity(gen, world, learned(agent, fact_query, t))


def query_treated_as_known(
    world: Database,
    agent: Any,
    fact_query: Any,
    t: Timestamp,
    hidden_query: Any | None = None,
) -> bool:
    """
    Evaluate: is agent legally attributed knowledge of fact at time t?

    Covers both:
      - actual knowledge  (learned/3 in the base world)
      - constructive knowledge (should_have_known via compliance worlds)

    This is the primary entry point for audit queries.
    """
    # Check actual knowledge first (cheap, no world generation).

    if any(True for _ in world.ask(learned(agent, fact_query, t))):
        return True

    # Fall through to constructive knowledge.
    return query_should_have_known(world, agent, fact_query, t, hidden_query)
