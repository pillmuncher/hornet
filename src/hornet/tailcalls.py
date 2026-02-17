# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""
Tail-Call Elimination (TCE) via Thunking and Trampolining.

This module provides a mechanism for deep recursion in Python without
encountering `RecursionError`. It implements a trampoline pattern where
functions marked with `@tailcall` return a 'thunk' (a deferred execution unit)
instead of increasing the call stack.

The `trampoline` driver iteratively executes these thunks, effectively
flattening recursive logic into a linear loop.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

__all__ = (
    'Cont',
    'Thunk',
    'Frame',
    'tailcall',
    'trampoline',
)

type Cont[R] = Callable[..., Frame[R]]
type Thunk[R] = Callable[[], Frame[R]]
type Frame[R] = tuple[R | None, Thunk[R]] | None


def tailcall[R](cont: Cont[R]) -> Cont[R]:
    """
    Wraps a function to participate in tail-call elimination.

    When a decorated function is called, it returns a 'Frame' containing
    a thunk rather than executing the function body immediately. This
    defers the actual call until the `trampoline` handles it.

    Returns:
        A callable that returns a `Frame[R]`.
    """

    def decorated(*args: Any, **kwargs: Any) -> Frame[R]:
        return None, lambda: cont(*args, **kwargs)

    return decorated


def trampoline[R](thunk: Thunk[R]) -> Iterable[R]:
    """
    The iterative driver for tail-recursive functions.

    Repeatedly evaluates thunks to advance the computation. If a thunk
    yields a result (the first element of the `Frame` tuple), it is
    emitted to the caller. The loop continues until the computation
    signals termination by returning `None`.

    Yields:
        Successful results of type `R` produced during the execution.
    """
    while (frame := thunk()) is not None:
        maybe_result, thunk = frame
        if maybe_result is not None:
            yield maybe_result
