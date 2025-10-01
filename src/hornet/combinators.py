# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from functools import reduce
from typing import Callable, Iterable

from immutables import Map
from toolz import flip

from .tailcalls import Frame, tailcall
from .terms import Compound, Term, Variable

type Result = Frame[Map]
type Next = Callable[[], Result]
type Emit[Ctx] = Callable[[Ctx, Map, Next], Result]
type Step[Ctx] = Callable[[Emit[Ctx], Next, Next], Result]
type Goal[Ctx] = Callable[[Ctx, Map], Step[Ctx]]


def success[Ctx](ctx: Ctx, subst: Map, no: Next) -> Result:
    return subst, no


def failure() -> Result:
    return None


def bind[Ctx](bind_step: Step[Ctx], goal: Goal[Ctx]) -> Step[Ctx]:
    @tailcall
    def step(
        yes: Emit[Ctx], no: Next, prune: Next, bind_step=bind_step, goal=goal
    ) -> Result:
        return bind_step(
            tailcall(lambda ctx, subst, then_no: goal(ctx, subst)(yes, then_no, prune)),
            no,
            prune,
        )

    return step


def unit[Ctx](ctx: Ctx, subst: Map) -> Step[Ctx]:
    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next, ctx=ctx, subst=subst) -> Result:
        return yes(ctx, subst, no)

    return step


def cut[Ctx](ctx: Ctx, subst: Map) -> Step[Ctx]:
    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next, ctx=ctx, subst=subst) -> Result:
        return yes(ctx, subst, prune)

    return step


def fail[Ctx](ctx: Ctx, subst: Map) -> Step[Ctx]:
    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next, ctx=ctx, subst=subst) -> Result:
        return no()

    return step


def then[Ctx](goal1: Goal[Ctx], goal2: Goal[Ctx]) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Map, goal1=goal1, goal2=goal2) -> Step[Ctx]:
        return bind(goal1(ctx, subst), goal2)

    return goal


def seq_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    return reduce(flip(then), reversed(tuple(goals)), unit)  # type: ignore


def seq[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    return seq_from_iterable(goals)


def choice[Ctx](goal1: Goal[Ctx], goal2: Goal[Ctx]) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Map, goal1=goal1, goal2=goal2) -> Step[Ctx]:
        @tailcall
        def step(
            yes: Emit[Ctx], no: Next, prune: Next, goal1=goal1, goal2=goal2
        ) -> Result:
            return goal1(ctx, subst)(
                yes,
                tailcall(lambda: goal2(ctx, subst)(yes, no, prune)),
                prune,
            )

        return step

    return goal


def amb_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Map) -> Step[Ctx]:
        @tailcall
        def step(
            yes: Emit[Ctx], no: Next, prune: Next, ctx=ctx, subst=subst, goals=goals
        ) -> Result:
            amb_goal: Goal[Ctx] = reduce(flip(choice), reversed(tuple(goals)), fail)  # pyright: ignore
            return amb_goal(ctx, subst)(yes, no, prune)

        return step

    return goal


def amb[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    return amb_from_iterable(goals)


def prunable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Map, goals=goals) -> Step[Ctx]:
        @tailcall
        def step(
            yes: Emit[Ctx], no: Next, prune: Next, ctx=ctx, subst=subst, goals=goals
        ) -> Result:
            return amb_from_iterable(goals)(ctx, subst)(yes, no, no)

        return step

    return goal


def neg[Ctx](goal: Goal[Ctx]) -> Goal[Ctx]:
    return prunable([amb(seq(goal, cut, fail), unit)])


def deref_and_compress(subst: Map, term: Term) -> tuple[Map, Term]:
    visited = set()
    while isinstance(term, Variable) and term in subst:
        if term in visited:
            raise RuntimeError(f"Cyclic variable binding detected: {term}")
        visited.add(term)
        term = subst[term]
    mm = subst.mutate()
    for v in visited:
        mm[v] = term
    return mm.finish(), term


def unify[Ctx](this: Term, that: Term) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Map, this=this, that=that) -> Step[Ctx]:
        subst, this = deref_and_compress(subst, this)
        subst, that = deref_and_compress(subst, that)
        return _unify(this, that)(ctx, subst)

    return goal


def unify_variable[Ctx](variable: Variable, term: Term) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Map, variable=variable, term=term) -> Step[Ctx]:
        subst, value = deref_and_compress(subst, variable)
        if value is variable:
            return unit(ctx, subst.set(variable, term))
        else:
            return tailcall(unify(value, term)(ctx, subst))

    return goal


def unify_pairs[Ctx](*pairs: tuple[Term, Term]) -> Goal[Ctx]:
    return lambda ctx, subst, pairs=pairs: tailcall(
        seq_from_iterable(unify(this, that) for this, that in pairs)(ctx, subst)
    )


def unify_any[Ctx](variable: Variable, *values: Term) -> Goal[Ctx]:
    return amb_from_iterable(unify(variable, value) for value in values)


def _unify[Ctx](this: Term, that: Term) -> Goal[Ctx]:
    match this, that:
        case _ if this == that:
            return unit

        case Variable(name="_"), _:
            return unit

        case _, Variable(name="_"):
            return unit

        case Variable(), _:
            return unify_variable(this, that)

        case _, Variable():
            return unify_variable(that, this)

        case Compound(), Compound():
            if this.indicator == that.indicator:
                return unify_pairs(*zip(this.args, that.args))
            else:
                return fail

        case _:
            return fail
