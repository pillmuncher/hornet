# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""The Prolog Monad: A Triple-Barrelled Continuation-based Engine.

This module implements the core resolution logic for a Prolog-style system.
It uses a "Triple-Barrelled Continuation Monad" to manage search,
backtracking, and pruning:
1.  **Success (Emit)**: Propagates the current substitution forward.
2.  **Failure (Next[Env])**: Backtracks to the last available choice point.
3.  **Prune**: Defines the jump-target for the 'cut' (!) operator.

The engine is context-agnostic; `Ctx` (typically the clause database) is
passed through without direct access to maintain a clean separation of
concerns. All operations are tail-call optimized to support deep recursion.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from toolz import flip, reduce

from .tailcalls import Frame, tailcall

type Next[Env] = Callable[[], Frame[Env]]
type Emit[Ctx, Env] = Callable[[Ctx, Env, Next[Env]], Frame[Env]]
type Step[Ctx, Env] = Callable[[Emit[Ctx, Env], Next[Env], Next[Env]], Frame[Env]]
type Goal[Ctx, Env] = Callable[[Ctx, Env], Step[Ctx, Env]]


def success[Env](ctx: Any, subst: Env, no: Next[Env]) -> Frame[Env]:
    """
    The primitive success handler that returns the current substitution.
    """
    return subst, no


def failure[Env]() -> Frame[Env]:
    """
    The primitive failure handler that returns None.
    """
    return None


def bind[Ctx, Env](bind_step: Step[Ctx, Env], goal: Goal[Ctx, Env]) -> Step[Ctx, Env]:
    """
    Monadic bind for goals. Chains a computation step to a subsequent goal.
    """

    @tailcall
    def step(
        yes: Emit[Ctx, Env],
        no: Next[Env],
        prune: Next[Env],
        bind_step: Step[Ctx, Env] = bind_step,
        goal: Goal[Ctx, Env] = goal,
    ) -> Frame[Env]:
        @tailcall
        def bound(ctx: Ctx, subst: Env, then_no: Next[Env]) -> Frame[Env]:
            return goal(ctx, subst)(yes, then_no, prune)

        return bind_step(bound, no, prune)

    return step


def unit[Ctx, Env](ctx: Ctx, subst: Env) -> Step[Ctx, Env]:
    """
    A goal that always succeeds once with the current substitution.
    """

    @tailcall
    def step(
        yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env], ctx: Ctx = ctx, subst: Env = subst
    ) -> Frame[Env]:
        return yes(ctx, subst, no)

    return step


def cut[Ctx, Env](ctx: Ctx, subst: Env) -> Step[Ctx, Env]:
    """
    A goal that succeeds once but prunes all other choices in its scope.

    Effectively implements the Prolog '!' operator by setting the backtrack
    continuation to the 'prune' continuation.
    """

    @tailcall
    def step(
        yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env], ctx: Ctx = ctx, subst: Env = subst
    ) -> Frame[Env]:
        return yes(ctx, subst, prune)

    return step


def fail[Ctx, Env](ctx: Ctx, subst: Env) -> Step[Ctx, Env]:
    """
    A goal that always fails immediately.
    """

    @tailcall
    def step(
        yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env], ctx: Ctx = ctx, subst: Env = subst
    ) -> Frame[Env]:
        return no()

    return step


def then[Ctx, Env](goal1: Goal[Ctx, Env], goal2: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    """
    Logical conjunction (AND) of two goals.
    """

    def goal(
        ctx: Ctx, subst: Env, goal1: Goal[Ctx, Env] = goal1, goal2: Goal[Ctx, Env] = goal2
    ) -> Step[Ctx, Env]:
        return bind(goal1(ctx, subst), goal2)

    return goal


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


def choice[Ctx, Env](goal1: Goal[Ctx, Env], goal2: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    """
    Logical disjunction (OR) of two goals. Backtracks to goal2 if goal1 fails.
    """

    def goal(
        ctx: Ctx, subst: Env, goal1: Goal[Ctx, Env] = goal1, goal2: Goal[Ctx, Env] = goal2
    ) -> Step[Ctx, Env]:
        @tailcall
        def step(
            yes: Emit[Ctx, Env],
            no: Next[Env],
            prune: Next[Env],
            goal1: Goal[Ctx, Env] = goal1,
            goal2: Goal[Ctx, Env] = goal2,
        ) -> Frame[Env]:
            return goal1(ctx, subst)(
                yes,
                tailcall(lambda: goal2(ctx, subst)(yes, no, prune)),
                prune,
            )

        return step

    return goal


def amb_from_iterable[Ctx, Env](goals: Iterable[Goal[Ctx, Env]]) -> Goal[Ctx, Env]:
    """
    Ambiguous choice; tries each goal in order via backtracking.
    """

    def goal(ctx: Ctx, subst: Env) -> Step[Ctx, Env]:
        @tailcall
        def step(
            yes: Emit[Ctx, Env],
            no: Next[Env],
            prune: Next[Env],
            ctx: Ctx = ctx,
            subst: Env = subst,
            goals: Iterable[Goal[Ctx, Env]] = goals,
        ) -> Frame[Env]:
            amb_goal: Goal[Ctx, Env] = reduce(flip(choice), reversed(tuple(goals)), fail)  # pyright: ignore
            return amb_goal(ctx, subst)(yes, no, prune)

        return step

    return goal


def amb[Ctx, Env](*goals: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    """
    Ambiguous choice; tries each goal in order via backtracking.
    """
    return amb_from_iterable(goals)


def prunable[Ctx, Env](goals: Iterable[Goal[Ctx, Env]]) -> Goal[Ctx, Env]:
    """
    Establishes a pruning boundary for a collection of goals.

    This combinator creates a choice-point scope. Any `cut` (!) invoked within
    the nested `goals` will only discard backtrack points back to the
    start of this block, preventing the cut from affecting choices made
    by previous goals in the parent sequence.
    """

    def goal(ctx: Ctx, subst: Env, goals: Iterable[Goal[Ctx, Env]] = goals) -> Step[Ctx, Env]:
        @tailcall
        def step(
            yes: Emit[Ctx, Env],
            no: Next[Env],
            prune: Next[Env],
            ctx: Ctx = ctx,
            subst: Env = subst,
            goals: Iterable[Goal[Ctx, Env]] = goals,
        ) -> Frame[Env]:
            return amb_from_iterable(goals)(ctx, subst)(yes, no, no)

        return step

    return goal


def neg[Ctx, Env](goal: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
    """
    Negation by failure. Succeeds only if the provided goal fails.
    """
    return prunable([amb(seq(goal, cut, fail), unit)])


def if_then_else[Ctx, Env](
    cond: Goal[Ctx, Env], then: Goal[Ctx, Env], else_: Goal[Ctx, Env]
) -> Goal[Ctx, Env]:
    """
    Soft-cut conditional. If `cond` succeeds, commit to `then`; otherwise `else_`.
    """

    def goal(ctx: Ctx, subst: Env) -> Step[Ctx, Env]:
        cond_step = cond(ctx, subst)

        @tailcall
        def step(yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
            def yes_branch(ctx: Ctx, subst: Env, _: Next[Env]):
                return then(ctx, subst)(yes, no, prune)

            def no_branch():
                return else_(ctx, subst)(yes, no, prune)

            return cond_step(yes_branch, no_branch, prune)

        return step

    return goal


def call_cc[Ctx, Env](
    f: Callable[[Emit[Ctx, Env], Next[Env], Next[Env]], Step[Ctx, Env]],
) -> Step[Ctx, Env]:
    """Call with Current Continuations"""

    @tailcall
    def step(yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
        return f(yes, no, prune)(yes, no, prune)

    return step


def call_ec[Ctx, Env](
    fn: Callable[[Callable[[Goal[Ctx, Env]], Goal[Ctx, Env]]], Goal[Ctx, Env]],
) -> Goal[Ctx, Env]:
    """Call with Escape Continuation"""

    def goal(
        ctx: Ctx,
        subst: Env,
        fn: Callable[[Callable[[Goal[Ctx, Env]], Goal[Ctx, Env]]], Goal[Ctx, Env]] = fn,
    ) -> Step[Ctx, Env]:
        @tailcall
        def step(yes: Emit[Ctx, Env], no: Next[Env], prune: Next[Env]) -> Frame[Env]:
            # escape: given a goal g, return a goal that, when run,
            # forwards any success to the captured `yes` and uses the
            # captured `prune` as the next continuation (thus pruning).
            def escape(g: Goal[Ctx, Env]) -> Goal[Ctx, Env]:
                def escaped_goal(inner_ctx: Ctx, inner_subst: Env) -> Step[Ctx, Env]:
                    @tailcall
                    def inner_step(
                        _yes: Emit[Ctx, Env], _no: Next[Env], _prune: Next[Env]
                    ) -> Frame[Env]:
                        # when g emits success, forward it to the captured yes
                        def forward_emit(_ctx: Ctx, _subst: Env, _next: Next[Env]) -> Frame[Env]:
                            return yes(_ctx, _subst, prune)

                        # run g; on success forward to captured yes, on failure fall back to
                        # the current `no`, and preserve `prune` for deeper pruning behavior.
                        return g(inner_ctx, inner_subst)(forward_emit, no, prune)

                    return inner_step

                return escaped_goal

            # call user-supplied fn with our escape and run the resulting goal
            return fn(escape)(ctx, subst)(yes, no, prune)

        return step

    return goal
