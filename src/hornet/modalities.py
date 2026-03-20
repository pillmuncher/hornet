# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable
from itertools import chain, combinations
from typing import cast

import hornet.combinators as combinators
from hornet.clauses import Database, Environment, Subst, failure, predicate, resolve
from hornet.combinators import Goal, Next, Step, amb_from_iterable, seq_from_iterable
from hornet.symbols import (
    AccessPred,
    AccessPred1,
    AccessPred2,
    Action,
    Agent,
    Fact,
    Obligations,
    Query,
    T,
    UncertainFacts,
    combine,
    compliance_world,
    epistemic_world,
    fail,
    necessarily,
    performed,
    possibly,
)
from hornet.tailcalls import Frame, trampoline
from hornet.terms import NonVariable


def powerset[E](iterable: Iterable[E]) -> Iterable[tuple[E, ...]]:
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def collect_worlds(
    access: Goal[Database, Environment],
    db: Database,
    env: Environment,
) -> list[tuple[Database, Environment]]:
    worlds: list[tuple[Database, Environment]] = []

    def collect(ctx: Database, e: Environment, no: Next[Environment]) -> Frame[Environment]:
        worlds.append((ctx, e))
        return no()

    step = access(db, env)
    list(trampoline(lambda: step(collect, failure, failure)))
    return worlds or [(db, env)]


def _switch(w: Database, e: Environment) -> Goal[Database, Environment]:
    def goal(db2: Database, env2: Environment) -> Step[Database, Environment]:
        return combinators.unit(w, e)

    return goal


def _in_world(
    w: Database, e: Environment, query: Goal[Database, Environment]
) -> Goal[Database, Environment]:
    def goal(db2: Database, env2: Environment) -> Step[Database, Environment]:
        return query(w, e)

    return goal


@predicate(necessarily(Query, AccessPred))
def _necessarily(db: Database, subst: Subst) -> Step[Database, Environment]:
    access = resolve(subst[AccessPred])
    query = resolve(subst[Query])
    worlds = collect_worlds(access, db, subst.env)
    return seq_from_iterable(_in_world(w, e, query) for w, e in worlds)(db, subst.env)


@predicate(possibly(Query, AccessPred))
def _possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
    access = resolve(subst[AccessPred])
    query = resolve(subst[Query])
    worlds = collect_worlds(access, db, subst.env)
    return amb_from_iterable(tuple(_in_world(w, e, query) for w, e in worlds))(db, subst.env)


@predicate(epistemic_world(UncertainFacts, Agent, T))
def _epistemic_world(db: Database, subst: Subst) -> Step[Database, Environment]:
    facts: list[NonVariable] = [
        cast(NonVariable, s[Fact]) for s in db.ask(cast(NonVariable, subst[UncertainFacts]))
    ]
    worlds: list[Database] = [
        db.shadow(*[f.when(fail) for f in hidden]) for hidden in powerset(facts)
    ] or [db]
    return amb_from_iterable(tuple(_switch(w, subst.env) for w in worlds))(db, subst.env)


@predicate(compliance_world(Obligations, Agent, T))
def _compliance_world(db: Database, subst: Subst) -> Step[Database, Environment]:
    return combinators.unit(
        db.overlay(performed(Agent, Action, T).when(cast(NonVariable, subst[Obligations]))),
        subst.env,
    )


# Kleisli composition over access relations:
@predicate(combine(AccessPred1, AccessPred2))
def _combine(db: Database, subst: Subst) -> Step[Database, Environment]:
    access1 = resolve(subst[AccessPred1])
    access2 = resolve(subst[AccessPred2])
    all_worlds = [
        (w2, e2)
        for w1, e1 in collect_worlds(access1, db, subst.env)
        for w2, e2 in collect_worlds(access2, w1, e1)
    ]
    return amb_from_iterable(tuple(_switch(w, e) for w, e in all_worlds))(db, subst.env)


def modal(db: Database) -> Database:
    child = db.new_child()
    child.tell(_necessarily, _possibly, _epistemic_world, _compliance_world, _combine)
    return child
