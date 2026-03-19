# Copyright (c) 2025-2026 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""The Prolog Monad: A Triple-Barrelled Continuation-based Engine.

This module implements the core resolution logic for a Prolog-style system.
It uses a "Triple-Barrelled Continuation Monad" to manage search,
backtracking, and pruning:
1.  **Success (Emit[Ctx, Env])**: Propagates the current substitution forward.
2.  **Failure (Next[Env])**: Backtracks to the last available choice point.
3.  **Prune (Next[Env])**: Defines the jump-target for the 'cut' (!) operator.

The engine is context-agnostic; `Ctx` (typically the clause database) is
passed through without direct access to maintain a clean separation of
concerns. All operations are tail-call optimized to support deep recursion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from toolz import flip, reduce

from .tailcalls import Frame, Thunked, tailcall

type Next[Env] = Callable[[], Frame[Env]]
type Emit[Ctx, Env] = Callable[[Ctx, Env, Next[Env]], Frame[Env]]
type Step[Ctx, Env] = Callable[[Emit[Ctx, Env], Next[Env], Next[Env]], Frame[Env]]
type Goal[Ctx, Env] = Callable[[Ctx, Env], Step[Ctx, Env]]


@dataclass(frozen=True, slots=True)
class bind_step[Ctx, Env]:
    goal: Goal[Ctx, Env]
    yes: Emit[Ctx, Env]
    prune: Next[Env]

    @tailcall
    def __call__(self, ctx: Ctx, env: Env, no: Next[Env]) -> Frame[Env]:
        return self.goal(ctx, env)(self.yes, no, self.prune)


@dataclass(frozen=True, slots=True)
class bind[Ctx, Env]:
    step: Step[Ctx, Env]
    goal: Goal[Ctx, Env]

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.step(bind_step(self.goal, yes, prune), no, prune)


@dataclass(frozen=True, slots=True)
class unit[Ctx, Env]:
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return yes(self.ctx, self.env, no)


@dataclass(frozen=True, slots=True)
class cut[Ctx, Env]:
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return yes(self.ctx, self.env, prune)


@dataclass(frozen=True, slots=True)
class fail[Ctx, Env]:
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return no()


@dataclass(frozen=True, slots=True)
class then[Ctx, Env]:
    goal1: Goal[Ctx, Env]
    goal2: Goal[Ctx, Env]

    def __call__(self, ctx: Ctx, env: Env) -> Step[Ctx, Env]:
        return bind(self.goal1(ctx, env), self.goal2)


def seq_from_iterable[Ctx, Env](goals: Iterable[Goal[Ctx, Env]]) -> Goal[Ctx, Env]:
    """
    Sequence multiple goals; all must succeed for the sequence to succeed.
    """
    return reduce(flip(then), reversed(tuple(goals)), unit)  # type: ignore


def seq[Ctx, Env](*goals: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    """
    Sequence multiple goals; all must succeed for the sequence to succeed.
    """

    return seq_from_iterable(goals)


@dataclass(frozen=True, slots=True)
class choice_step[Ctx, Env]:
    goal1: Goal[Ctx, Env]
    goal2: Goal[Ctx, Env]
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.goal1(self.ctx, self.env)(
            yes,
            Thunked(self.goal2(self.ctx, self.env), (yes, no, prune), {}),
            prune,
        )


@dataclass(frozen=True, slots=True)
class choice[Ctx, Env]:
    goal1: Goal[Ctx, Env]
    goal2: Goal[Ctx, Env]

    def __call__(self, ctx: Ctx, env: Env) -> Step[Ctx, Env]:
        return choice_step(self.goal1, self.goal2, ctx, env)


@dataclass(frozen=True, slots=True)
class amb_step[Ctx, Env]:
    goal: Goal[Ctx, Env]
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.goal(self.ctx, self.env)(yes, no, prune)


@dataclass(frozen=True, slots=True)
class amb_from_iterable[Ctx, Env]:
    goals: tuple[Goal[Ctx, Env], ...]

    def __call__(self, ctx: Ctx, env: Env) -> Step[Ctx, Env]:
        return amb_step(reduce(flip(choice), reversed(self.goals), fail), ctx, env)  # pyright: ignore


def amb[Ctx, Env](*goals: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    """
    Ambiguous choice; tries each goal in order via backtracking.
    """
    return amb_from_iterable(goals)


@dataclass(frozen=True, slots=True)
class prunable_step[Ctx, Env]:
    goal: Goal[Ctx, Env]
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.goal(self.ctx, self.env)(yes, no, no)


@dataclass(frozen=True, slots=True)
class prunable[Ctx, Env]:
    goals: tuple[Goal[Ctx, Env], ...]

    def __call__(self, ctx: Ctx, env: Env) -> Step[Ctx, Env]:
        return prunable_step(amb_from_iterable(self.goals), ctx, env)


def neg[Ctx, Env](goal: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    return prunable((amb(seq(goal, cut, fail), unit),))


@dataclass(frozen=True, slots=True)
class ite_yes_branch[Ctx, Env]:
    then_: Goal[Ctx, Env]
    ctx: Ctx
    env: Env
    yes: Emit[Ctx, Env]
    no: Next[Env]
    prune: Next[Env]

    def __call__(self, ctx: Ctx, env: Env, _: Next[Env]) -> Frame[Env]:
        return self.then_(ctx, env)(self.yes, self.no, self.prune)


@dataclass(frozen=True, slots=True)
class ite_no_branch[Ctx, Env]:
    else_: Goal[Ctx, Env]
    ctx: Ctx
    env: Env
    yes: Emit[Ctx, Env]
    no: Next[Env]
    prune: Next[Env]

    def __call__(self) -> Frame[Env]:
        return self.else_(self.ctx, self.env)(self.yes, self.no, self.prune)


@dataclass(frozen=True, slots=True)
class ite_step[Ctx, Env]:
    cond_step: Step[Ctx, Env]
    then_: Goal[Ctx, Env]
    else_: Goal[Ctx, Env]
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.cond_step(
            ite_yes_branch(self.then_, self.ctx, self.env, yes, no, prune),
            ite_no_branch(self.else_, self.ctx, self.env, yes, no, prune),
            prune,
        )


@dataclass(frozen=True, slots=True)
class if_then_else[Ctx, Env]:
    cond: Goal[Ctx, Env]
    then_: Goal[Ctx, Env]
    else_: Goal[Ctx, Env]

    def __call__(self, ctx: Ctx, env: Env) -> Step[Ctx, Env]:
        return ite_step(self.cond(ctx, env), self.then_, self.else_, ctx, env)


type CC[Ctx, Env] = Callable[[Emit[Ctx, Env], Next[Env], Next[Env]], Step[Ctx, Env]]
type Escape[Ctx, Env] = Callable[[Goal[Ctx, Env]], Goal[Ctx, Env]]
type EC[Ctx, Env] = Callable[[Escape[Ctx, Env]], Goal[Ctx, Env]]


@dataclass(frozen=True, slots=True)
class call_cc[Ctx, Env]:
    f: CC[Ctx, Env]

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.f(yes, no, prune)(yes, no, prune)


@dataclass(frozen=True, slots=True)
class ec_forward_emit[Ctx, Env]:
    yes: Emit[Ctx, Env]
    prune: Next[Env]

    def __call__(self, ctx: Ctx, env: Env, _: Next[Env]) -> Frame[Env]:
        return self.yes(ctx, env, self.prune)


@dataclass(frozen=True, slots=True)
class ec_inner_step[Ctx, Env]:
    goal: Goal[Ctx, Env]
    inner_ctx: Ctx
    inner_env: Env
    yes: Emit[Ctx, Env]
    no: Next[Env]
    prune: Next[Env]

    @tailcall
    def __call__(self, _yes: Emit[Ctx, Env], _no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.goal(self.inner_ctx, self.inner_env)(
            ec_forward_emit(self.yes, self.prune),
            self.no,
            self.prune,
        )


@dataclass(frozen=True, slots=True)
class ec_escaped_goal[Ctx, Env]:
    goal: Goal[Ctx, Env]
    yes: Emit[Ctx, Env]
    no: Next[Env]
    prune: Next[Env]

    def __call__(self, inner_ctx: Ctx, inner_env: Env) -> Step[Ctx, Env]:
        return ec_inner_step(self.goal, inner_ctx, inner_env, self.yes, self.no, self.prune)


@dataclass(frozen=True, slots=True)
class ec_escape[Ctx, Env]:
    yes: Emit[Ctx, Env]
    no: Next[Env]
    prune: Next[Env]

    def __call__(self, goal: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
        return ec_escaped_goal(goal, self.yes, self.no, self.prune)


@dataclass(frozen=True, slots=True)
class ec_step[Ctx, Env]:
    fn: EC[Ctx, Env]
    ctx: Ctx
    env: Env

    @tailcall
    def __call__(self, yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return self.fn(ec_escape(yes, no, prune))(self.ctx, self.env)(yes, no, prune)


@dataclass(frozen=True, slots=True)
class call_ec[Ctx, Env]:
    fn: EC[Ctx, Env]

    def __call__(self, ctx: Ctx, env: Env) -> Step[Ctx, Env]:
        return ec_step(self.fn, ctx, env)
