# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

__all__ = (
    "Cont",
    "Thunk",
    "Frame",
    "tailcall",
    "trampoline",
)

type Cont[Result] = Callable[..., Frame[Result]]
type Thunk[Result] = Callable[[], Frame[Result]]
type Frame[Result] = tuple[Result | None, Thunk[Result]] | None


@dataclass(frozen=True, slots=True)
class thunk[Result]:
    cont: Cont[Result]
    args: tuple[Any]
    kwargs: dict[str, Any]

    def __call__(self):
        return self.cont(*self.args, **self.kwargs)


def tailcall[Result](cont: Cont[Result]) -> Cont[Result]:
    """
    Mark a continuation for tail-call elimination.
    Instead of calling `cont` directly, wrap it in a thunk
    so the trampoline driver can evaluate it without recursion.
    """

    def decorated(*args, **kwargs) -> Frame[Result]:
        return None, thunk(cont, args, kwargs)

    return decorated


def trampoline[Result](thunk: Thunk[Result]) -> Iterable[Result]:
    """
    Drive a thunk() that returns Frame[R].
    Yield only non-None R payloads.
    """
    while (frame := thunk()) is not None:
        maybe_result, thunk = frame
        if maybe_result is not None:
            yield maybe_result
