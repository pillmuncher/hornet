# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""The Prolog Monad: A Triple-Barrelled Continuation-based Engine.

This module implements the core resolution logic for a Prolog-style system.
It uses a "Triple-Barrelled Continuation Monad" to manage search,
backtracking, and pruning:
1.  **Success (Emit)**: Propagates the current substitution forward.
2.  **Failure (Next)**: Backtracks to the last available choice point.
3.  **Prune**: Defines the jump-target for the 'cut' (!) operator.

The engine is context-agnostic; `Ctx` (typically the clause database) is
passed through without direct access to maintain a clean separation of
concerns. All operations are tail-call optimized to support deep recursion.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from immutables import Map
from toolz import flip, reduce

from .tailcalls import Frame, tailcall
from .terms import Compound, Term, Variable, Wildcard

type Env = Map[Variable, Term]
type Result = Frame[Env]
type Next = Callable[[], Result]
type Emit[Ctx] = Callable[[Ctx, Env, Next], Result]
type Step[Ctx] = Callable[[Emit[Ctx], Next, Next], Result]
type Goal[Ctx] = Callable[[Ctx, Env], Step[Ctx]]


def success(ctx: Any, subst: Env, no: Next) -> Result:
    """
    The primitive success handler that returns the current substitution.
    """
    return subst, no


def failure() -> Result:
    """
    The primitive failure handler that returns None.
    """
    return None


def bind[Ctx](bind_step: Step[Ctx], goal: Goal[Ctx]) -> Step[Ctx]:
    """
    Monadic bind for goals. Chains a computation step to a subsequent goal.
    """

    @tailcall
    def step(
        yes: Emit[Ctx],
        no: Next,
        prune: Next,
        bind_step: Step[Ctx] = bind_step,
        goal: Goal[Ctx] = goal,
    ) -> Result:
        @tailcall
        def bound(ctx: Ctx, subst: Env, then_no: Next) -> Result:
            return goal(ctx, subst)(yes, then_no, prune)

        return bind_step(bound, no, prune)

    return step


def unit[Ctx](ctx: Ctx, subst: Env) -> Step[Ctx]:
    """
    A goal that always succeeds once with the current substitution.
    """

    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next, ctx: Ctx = ctx, subst: Env = subst) -> Result:
        return yes(ctx, subst, no)

    return step


def cut[Ctx](ctx: Ctx, subst: Env) -> Step[Ctx]:
    """
    A goal that succeeds once but prunes all other choices in its scope.

    Effectively implements the Prolog '!' operator by setting the backtrack
    continuation to the 'prune' continuation.
    """

    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next, ctx: Ctx = ctx, subst: Env = subst) -> Result:
        return yes(ctx, subst, prune)

    return step


def fail[Ctx](ctx: Ctx, subst: Env) -> Step[Ctx]:
    """
    A goal that always fails immediately.
    """

    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next, ctx: Ctx = ctx, subst: Env = subst) -> Result:
        return no()

    return step


def then[Ctx](goal1: Goal[Ctx], goal2: Goal[Ctx]) -> Goal[Ctx]:
    """
    Logical conjunction (AND) of two goals.
    """

    def goal(
        ctx: Ctx, subst: Env, goal1: Goal[Ctx] = goal1, goal2: Goal[Ctx] = goal2
    ) -> Step[Ctx]:
        return bind(goal1(ctx, subst), goal2)

    return goal


def seq_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    """
    Sequence multiple goals; all must succeed for the sequence to succeed.
    """
    return reduce(flip(then), reversed(tuple(goals)), unit)  # type: ignore


def seq[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    """
    Sequence multiple goals; all must succeed for the sequence to succeed.
    """

    return seq_from_iterable(goals)


def choice[Ctx](goal1: Goal[Ctx], goal2: Goal[Ctx]) -> Goal[Ctx]:
    """
    Logical disjunction (OR) of two goals. Backtracks to goal2 if goal1 fails.
    """

    def goal(
        ctx: Ctx, subst: Env, goal1: Goal[Ctx] = goal1, goal2: Goal[Ctx] = goal2
    ) -> Step[Ctx]:
        @tailcall
        def step(
            yes: Emit[Ctx],
            no: Next,
            prune: Next,
            goal1: Goal[Ctx] = goal1,
            goal2: Goal[Ctx] = goal2,
        ) -> Result:
            return goal1(ctx, subst)(
                yes,
                tailcall(lambda: goal2(ctx, subst)(yes, no, prune)),
                prune,
            )

        return step

    return goal


def amb_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    """
    Ambiguous choice; tries each goal in order via backtracking.
    """

    def goal(ctx: Ctx, subst: Env) -> Step[Ctx]:
        @tailcall
        def step(
            yes: Emit[Ctx],
            no: Next,
            prune: Next,
            ctx: Ctx = ctx,
            subst: Env = subst,
            goals: Iterable[Goal[Ctx]] = goals,
        ) -> Result:
            amb_goal: Goal[Ctx] = reduce(flip(choice), reversed(tuple(goals)), fail)  # pyright: ignore
            return amb_goal(ctx, subst)(yes, no, prune)

        return step

    return goal


def amb[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    """
    Ambiguous choice; tries each goal in order via backtracking.
    """
    return amb_from_iterable(goals)


def prunable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    """
    Establishes a pruning boundary for a collection of goals.

    This combinator creates a choice-point scope. Any `cut` (!) invoked within
    the nested `goals` will only discard backtrack points back to the
    start of this block, preventing the cut from affecting choices made
    by previous goals in the parent sequence.
    """

    def goal(ctx: Ctx, subst: Env, goals: Iterable[Goal[Ctx]] = goals) -> Step[Ctx]:
        @tailcall
        def step(
            yes: Emit[Ctx],
            no: Next,
            prune: Next,
            ctx: Ctx = ctx,
            subst: Env = subst,
            goals: Iterable[Goal[Ctx]] = goals,
        ) -> Result:
            return amb_from_iterable(goals)(ctx, subst)(yes, no, no)

        return step

    return goal


def neg[Ctx](goal: Goal[Ctx]) -> Goal[Ctx]:
    """
    Negation by failure. Succeeds only if the provided goal fails.
    """
    return prunable([amb(seq(goal, cut, fail), unit)])


def if_then_else[Ctx](cond: Goal[Ctx], then: Goal[Ctx], else_: Goal[Ctx]) -> Goal[Ctx]:
    """
    Soft-cut conditional. If `cond` succeeds, commit to `then`; otherwise `else_`.
    """

    def goal(ctx: Ctx, subst: Env) -> Step[Ctx]:
        cond_step = cond(ctx, subst)

        @tailcall
        def step(yes: Emit[Ctx], no: Next, prune: Next) -> Result:
            def yes_branch(ctx: Ctx, subst: Env, _: Next):
                return then(ctx, subst)(yes, no, prune)

            def no_branch():
                return else_(ctx, subst)(yes, no, prune)

            return cond_step(yes_branch, no_branch, prune)

        return step

    return goal


def call_cc[Ctx](f: Callable[[Emit[Ctx], Next, Next], Step[Ctx]]) -> Step[Ctx]:
    """Call with Current Continuations"""

    @tailcall
    def step(yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return f(yes, no, prune)(yes, no, prune)

    return step


def call_ec[Ctx](
    fn: Callable[[Callable[[Goal[Ctx]], Goal[Ctx]]], Goal[Ctx]],
) -> Goal[Ctx]:
    """Call with Escape Continuation"""

    def goal(
        ctx: Ctx, subst: Env, fn: Callable[[Callable[[Goal[Ctx]], Goal[Ctx]]], Goal[Ctx]] = fn
    ) -> Step[Ctx]:
        @tailcall
        def step(yes: Emit[Ctx], no: Next, prune: Next) -> Result:
            # escape: given a goal g, return a goal that, when run,
            # forwards any success to the captured `yes` and uses the
            # captured `prune` as the next continuation (thus pruning).
            def escape(g: Goal[Ctx]) -> Goal[Ctx]:
                def escaped_goal(inner_ctx: Ctx, inner_subst: Env) -> Step[Ctx]:
                    @tailcall
                    def inner_step(_yes: Emit[Ctx], _no: Next, _prune: Next) -> Result:
                        # when g emits success, forward it to the captured yes
                        def forward_emit(_ctx: Ctx, _subst: Env, _next: Next) -> Result:
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


def deref_and_compress(subst: Env, term: Term) -> tuple[Env, Term]:
    """
    Resolve variable bindings and perform path compression.

    Follows the chain of substitutions for a variable and updates the map
    to point directly to the root value to speed up future lookups.
    """

    visited = set()
    while isinstance(term, Variable) and term in subst:
        if term in visited:
            raise RuntimeError(f'Cyclic variable binding detected: {term}')
        visited.add(term)
        term = subst[term]
    mm = subst.mutate()
    for v in visited:
        mm[v] = term
    return mm.finish(), term


def unify[Ctx](this: Term, that: Term) -> Goal[Ctx]:
    """
    Attempt to unify two terms.

    Returns a goal that succeeds if the terms can be matched under the
    current substitution, potentially extending it.
    """

    def goal(ctx: Ctx, subst: Env, this: Term = this, that: Term = that) -> Step[Ctx]:
        subst, this = deref_and_compress(subst, this)
        subst, that = deref_and_compress(subst, that)
        return _unify(this, that)(ctx, subst)

    return goal


def unify_variable[Ctx](variable: Variable, term: Term) -> Goal[Ctx]:
    def goal(ctx: Ctx, subst: Env, variable: Variable = variable, term: Term = term) -> Step[Ctx]:
        subst, value = deref_and_compress(subst, variable)
        assert value is variable
        return unit(ctx, subst.set(variable, term))

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

        case Wildcard(), _:
            return unit

        case _, Wildcard():
            return unit

        case Variable(), _:
            return unify_variable(this, that)

        case _, Variable():
            return unify_variable(that, this)

        case Compound(), Compound() if this.indicator == that.indicator:
            return unify_pairs(*zip(this.args, that.args))

        case _:
            return fail
