# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterable, Iterator
from itertools import chain, combinations
from typing import cast

import hornet.combinators as combinators
from hornet.clauses import Database, Environment, Subst, failure, predicate, resolve, success
from hornet.combinators import Goal, Next, Step, amb_from_iterable, seq_from_iterable
from hornet.symbols import (
    E2,
    L2,
    T1,
    T2,
    AccessPred,
    AccessPred1,
    AccessPred2,
    Action,
    Agent,
    Event,
    Fact,
    Init,
    L,
    Obligations,
    Query,
    T,
    UncertainFacts,
    _,
    append,
    call,
    combine,
    compliance_world,
    currently,
    epistemic_world,
    fail,
    greater,
    necessarily,
    no_later_than,
    performed,
    possibly,
    superseding,
    univ,
)
from hornet.tailcalls import Frame, trampoline
from hornet.terms import NonVariable


def powerset[E](iterable: Iterable[E]) -> Iterator[tuple[E, ...]]:
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


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
    )

    @child.tell
    @predicate(necessarily(Query, AccessPred))
    def _necessarily(db: Database, subst: Subst) -> Step[Database, Environment]:
        access = resolve(subst[AccessPred])
        query = resolve(subst[Query])
        worlds = collect_worlds(access, db, subst.env)

        def check_world(w: Database, e: Environment) -> Goal[Database, Environment]:
            def goal(db2: Database, env2: Environment) -> Step[Database, Environment]:
                if succeeds(query(w, e)):
                    return combinators.unit(db2, env2)
                return combinators.fail(db2, env2)

            return goal

        return seq_from_iterable(check_world(w, e) for w, e in worlds)(db, subst.env)

    @child.tell
    @predicate(possibly(Query, AccessPred))
    def _possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
        access = resolve(subst[AccessPred])
        query = resolve(subst[Query])
        worlds = collect_worlds(access, db, subst.env)

        if any(succeeds(query(w, e)) for w, e in worlds):
            return combinators.unit(db, subst.env)
        return combinators.fail(db, subst.env)

    @child.tell
    @predicate(epistemic_world(UncertainFacts, Agent, T))
    def _epistemic_world(db: Database, subst: Subst) -> Step[Database, Environment]:
        facts: list[NonVariable] = [
            cast(NonVariable, s[Fact]) for s in db.ask(cast(NonVariable, subst[UncertainFacts]))
        ]
        worlds: list[Database] = [
            db.shadow(*[f.when(fail) for f in hidden]) for hidden in powerset(facts)
        ] or [db]
        return amb_from_iterable(tuple(switch(w, subst.env) for w in worlds))(db, subst.env)

    @child.tell
    @predicate(compliance_world(Obligations, Agent, T))
    def _compliance_world(db: Database, subst: Subst) -> Step[Database, Environment]:
        return combinators.unit(
            db.overlay(performed(Agent, Action, T).when(subst[Obligations])),
            subst.env,
        )

    # Kleisli composition over access relations:
    @child.tell
    @predicate(combine(AccessPred1, AccessPred2))
    def _combine(db: Database, subst: Subst) -> Step[Database, Environment]:
        access1 = resolve(subst[AccessPred1])
        access2 = resolve(subst[AccessPred2])
        all_worlds = [
            (w2, e2)
            for w1, e1 in collect_worlds(access1, db, subst.env)
            for w2, e2 in collect_worlds(access2, w1, e1)
        ]
        return amb_from_iterable(tuple(switch(w, e) for w, e in all_worlds))(db, subst.env)

    def succeeds(step: Step[Database, Environment]) -> bool:
        for _s in trampoline(lambda: step(success, failure, failure)):
            return True
        return False

    def switch(w: Database, e: Environment) -> Goal[Database, Environment]:
        def goal(db2: Database, env2: Environment) -> Step[Database, Environment]:
            return combinators.unit(w, e)

        return goal

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

    return child
