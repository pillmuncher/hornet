# Copyright (c) 2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
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
from hornet.tailcalls import Frame, trampoline
from hornet.terms import NonVariable, Term


def powerset[E](iterable: Iterable[E]) -> Iterator[tuple[E, ...]]:
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def make_box(access_pred: Callable[[Term, Term, Term], Term]) -> Goal[Database, Subst]:
    """Factory for 'necessarily' style predicate."""

    def _box(db: Database, subst: Subst) -> Step[Database, Environment]:
        query: Goal[Database, Environment] = resolve(subst[Query])
        agent: Term = subst[Agent]
        t: Term = subst[T]

        access: Goal[Database, Environment] = resolve(access_pred(agent, _, t))
        worlds: list[tuple[Database, Environment]] = collect_worlds(access, db, subst.env)

        def check_world(w: Database, e: Environment) -> Goal[Database, Environment]:
            def goal(db2: Database, env2: Environment) -> Step[Database, Environment]:
                if succeeds(query(w, e)):
                    return combinators.unit(db2, env2)
                return combinators.fail(db2, env2)

            return goal

        # seq_from_iterable requires all subgoals to succeed (logical AND)
        return seq_from_iterable(check_world(w, e) for w, e in worlds)(db, subst.env)

    return _box


def make_diamond(access_pred: Callable[[Term, Term, Term], Term]) -> Goal[Database, Subst]:
    """Factory for 'possibly' style predicate."""

    def _diamond(db: Database, subst: Subst) -> Step[Database, Environment]:
        query: Goal[Database, Environment] = resolve(subst[Query])
        agent: Term = subst[Agent]
        t: Term = subst[T]

        access: Goal[Database, Environment] = resolve(access_pred(agent, _, t))
        worlds: list[tuple[Database, Environment]] = collect_worlds(access, db, subst.env)

        # any success in worlds is enough (logical OR)
        if any(succeeds(query(w, e)) for w, e in worlds):
            return combinators.unit(db, subst.env)
        return combinators.fail(db, subst.env)

    return _diamond


# build box/diamond once at setup
k_box: Goal[Database, Subst] = make_box(epistemic_world)
o_box: Goal[Database, Subst] = make_box(compliance_world)
k_diamond: Goal[Database, Subst] = make_diamond(epistemic_world)
o_diamond: Goal[Database, Subst] = make_diamond(compliance_world)


@predicate(k(Query, Agent, T))
def _k(db: Database, subst: Subst) -> Step[Database, Environment]:
    return k_box(db, subst)


@predicate(o(Query, Agent, T))
def _o(db: Database, subst: Subst) -> Step[Database, Environment]:
    return o_box(db, subst)


@predicate(possibly_k(Query, Agent, T))
def _k_possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
    return k_diamond(db, subst)


@predicate(possibly_o(Query, Agent, T))
def _o_possibly(db: Database, subst: Subst) -> Step[Database, Environment]:
    return o_diamond(db, subst)


@predicate(epistemic_world(Agent, KnownFact, T))
def _epistemic_world(db: Database, subst: Subst) -> Step[Database, Environment]:
    agent = subst[Agent]
    t = subst[T]

    facts: list[NonVariable] = [
        cast(NonVariable, s[KnownFact]) for s in db.ask(knowable(agent, KnownFact, t))
    ]

    worlds: list[Database] = [
        db.shadow(*[f.when(fail) for f in hidden]) for hidden in powerset(facts)
    ]

    return amb_from_iterable(tuple(switch(w, subst.env) for w in worlds))(db, subst.env)


@predicate(compliance_world(Agent, Action, T))
def _compliance_world(db: Database, subst: Subst) -> Step[Database, Environment]:
    agent = subst[Agent]
    t = subst[T]

    obligations: list[NonVariable] = [
        cast(NonVariable, s[Action]) for s in db.ask(obligation(agent, Action, t))
    ]

    return combinators.unit(
        db.overlay(*[performed(agent, act, t) for act in obligations]),
        subst.env,
    )


def succeeds(step: Step[Database, Environment]) -> bool:
    for _ in trampoline(lambda: step(success, failure, failure)):
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
        k(Query, Agent, T),
        o(Query, Agent, T),
        possibly_k(Query, Agent, T),
        possibly_o(Query, Agent, T),
        epistemic_world(Agent, KnownFact, T),
        compliance_world(Agent, Action, T),
    )

    return child
