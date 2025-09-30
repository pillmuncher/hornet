# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class start_query[Ctx]:
    step: Step[Ctx]

    def __call__(self) -> Result:
        return self.step(success, failure, failure)


@dataclass(frozen=True, slots=True)
class on_success[Ctx]:
    goal: Goal[Ctx]
    yes: Emit[Ctx]
    prune: Next

    @tailcall
    def __call__(self, ctx: Ctx, subst: Map, no: Next) -> Result:
        return self.goal(ctx, subst)(self.yes, no, self.prune)


@dataclass(frozen=True, slots=True)
class on_failure[Ctx]:
    goal: Goal[Ctx]
    ctx: Ctx
    subst: Map
    yes: Emit[Ctx]
    no: Next
    prune: Next

    @tailcall
    def __call__(self) -> Result:
        return self.goal(self.ctx, self.subst)(self.yes, self.no, self.prune)


@dataclass(frozen=True, slots=True)
class bind[Ctx]:
    step: Step[Ctx]
    goal: Goal[Ctx]

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return self.step(on_success(self.goal, yes, prune), no, prune)


@dataclass(frozen=True, slots=True)
class unit[Ctx]:
    ctx: Ctx
    subst: Map

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return yes(self.ctx, self.subst, no)


@dataclass(frozen=True, slots=True)
class cut[Ctx]:
    ctx: Ctx
    subst: Map

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return yes(self.ctx, self.subst, prune)


@tailcall
def fail_step[Ctx](yes: Emit[Ctx], no: Next, prune: Next) -> Result:
    return no()


def fail[Ctx](ctx: Ctx, subst: Map) -> Step[Ctx]:
    return fail_step


@dataclass(frozen=True, slots=True)
class then[Ctx]:
    goal1: Goal[Ctx]
    goal2: Goal[Ctx]

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        return bind(self.goal1(ctx, subst), self.goal2)


def seq_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    return reduce(flip(then), reversed(tuple(goals)), unit)  # type: ignore


def seq[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    return seq_from_iterable(goals)


@dataclass(frozen=True, slots=True)
class choice_step[Ctx]:
    goal1: Goal[Ctx]
    goal2: Goal[Ctx]
    ctx: Ctx
    subst: Map

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return self.goal1(self.ctx, self.subst)(
            yes,
            on_failure(self.goal2, self.ctx, self.subst, yes, no, prune),
            prune,
        )


@dataclass(frozen=True, slots=True)
class choice[Ctx]:
    goal1: Goal[Ctx]
    goal2: Goal[Ctx]

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        return choice_step(self.goal1, self.goal2, ctx, subst)


@dataclass(frozen=True, slots=True)
class amb_step[Ctx]:
    goal: Goal[Ctx]
    ctx: Ctx
    subst: Map

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return self.goal(self.ctx, self.subst)(yes, no, prune)


@dataclass(frozen=True, slots=True)
class amb_goal[Ctx]:
    goal: Goal[Ctx]

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        return amb_step(self.goal, ctx, subst)


def amb_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    return amb_goal(reduce(flip(choice), reversed(tuple(goals)), fail))  # type: ignore


def amb[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    return amb_from_iterable(goals)


@dataclass(frozen=True, slots=True)
class predicate_step[Ctx]:
    goals: list[Goal[Ctx]]
    ctx: Ctx
    subst: Map

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return amb_from_iterable(self.goals)(self.ctx, self.subst)(yes, no, no)


@dataclass(frozen=True, slots=True)
class predicate_goal[Ctx]:
    goals: list[Goal[Ctx]]

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        return predicate_step(self.goals, ctx, subst)


def neg[Ctx](goal: Goal[Ctx]) -> Goal[Ctx]:
    return predicate_goal([amb(seq(goal, cut, fail), unit)])


def deref_and_compress(subst: Map, obj: Term) -> tuple[Map, Term]:
    visited = set()
    while isinstance(obj, Variable) and obj in subst:
        if obj in visited:
            raise RuntimeError(f"Cyclic variable binding detected: {obj}")
        visited.add(obj)
        obj = subst[obj]
    for v in visited:
        subst = subst.set(v, obj)
    return subst, obj


def unify_deref[Ctx](this: Term, that: Term) -> Goal[Ctx]:
    def inner(ctx: Ctx, subst: Map) -> Step[Ctx]:
        subst1, this1 = deref_and_compress(subst, this)
        subst2, that1 = deref_and_compress(subst1, that)
        return _unify(this1, that1)(ctx, subst2)

    return inner


@dataclass(frozen=True, slots=True)
class unify_variable[Ctx]:
    variable: Variable
    term: Term

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        subst, value = deref_and_compress(subst, self.variable)
        if value is self.variable:
            return unit(ctx, subst.set(self.variable, self.term))
        else:
            return tailcall(_unify(value, self.term)(ctx, subst))


@dataclass(frozen=True, slots=True, init=False)
class unify_pairs[Ctx]:
    pairs: tuple[tuple[Term, Term], ...]

    def __init__(self, *pairs: tuple[Term, Term]) -> None:
        object.__setattr__(self, "pairs", pairs)

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        return tailcall(
            seq_from_iterable(unify_deref(this, that) for this, that in self.pairs)(
                ctx, subst
            )
        )


@dataclass(frozen=True, slots=True)
class unify[Ctx]:
    this: Term
    that: Term

    def __call__(self, ctx: Ctx, subst: Map) -> Step[Ctx]:
        return unify_deref(self.this, self.that)(ctx, subst)


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
