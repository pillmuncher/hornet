# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Callable, Iterable

__all__ = (
    "Cont",
    "Thunk",
    "Frame",
    "tailcall",
    "trampoline",
)

type Cont[R] = Callable[..., Frame[R]]
type Thunk[R] = Callable[[], Frame[R]]
type Frame[R] = tuple[R | None, Thunk[R]] | None


def tailcall[R](cont: Cont[R]) -> Cont[R]:
    """
    Mark a continuation for tail-call elimination.
    Instead of calling `cont` directly, wrap it in a thunk
    so the trampoline driver can evaluate it without recursion.
    """

    def decorated(*args, **kwargs) -> Frame[R]:
        return None, lambda: cont(*args, **kwargs)

    return decorated


def trampoline[R](thunk: Thunk[R]) -> Iterable[R]:
    """
    Drive a thunk() that returns Frame[R].
    Yield only non-None R payloads.
    """
    while (frame := thunk()) is not None:
        maybe_result, thunk = frame
        if maybe_result is not None:
            yield maybe_result
