# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generator

type StateFunction[S, V] = Callable[[V], State[S, V]]
type StateGenerator[S, R] = Generator[State[S, Any], Any, R]


@dataclass(frozen=True, slots=True)
class State[S, V]:
    run: Callable[[S], tuple[V, S]]

    def bind(self, f: StateFunction[S, V]) -> State[S, V]:
        def inner(state: S):
            value, new_state = self.run(state)
            return f(value).run(new_state)

        return State(inner)

    @staticmethod
    def unit(value: V) -> State[S, V]:
        return State(lambda s: (value, s))


def with_state[S, R](
    fn: Callable[..., StateGenerator[S, R]],
) -> Callable[..., State[S, R]]:
    def wrapper(*args, **kwargs) -> State[S, R]:
        gen = fn(*args, **kwargs)

        def step(value: Any | None = None):
            try:
                return gen.send(value).bind(step)
            except StopIteration as e:
                return State.unit(e.value)

        return step()  # start the trampoline

    return wrapper


def identity[T](x: T) -> T:
    return x


def const[T](x: T) -> Callable[[T], Any]:
    return lambda *_, **__: x


def get_state[S](fn: Callable[[S], S] = identity) -> State[S, S]:
    return State(lambda state: (fn(state), state))


def set_state[S](f: Callable[[S], S]) -> State[S, Any]:
    return State(lambda state: (None, f(state)))
