# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""Tests for tail-call elimination via thunking and trampolining."""

import sys
from typing import Iterable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hornet.tailcalls import Frame, tailcall, trampoline


def test_simple_recursion():
    """Tail-recursive countdown should not overflow stack."""

    @tailcall
    def countdown(n: int) -> Frame[int]:
        if n <= 0:
            return None
        return n, lambda: countdown(n - 1)

    result = list(trampoline(lambda: countdown(10000)))
    assert result == list(range(10000, 0, -1))


def test_empty_result():
    """Base case with no results."""

    @tailcall
    def empty() -> Frame[int]:
        return None

    result = list(trampoline(empty))
    assert result == []


def test_single_result():
    """Single yielded value before termination."""

    @tailcall
    def single() -> Frame[int]:
        return 42, lambda: None

    result = list(trampoline(single))
    assert result == [42]


def test_factorial_accumulator():
    """Tail-recursive factorial with accumulator."""

    @tailcall
    def factorial(n: int, acc: int = 1) -> Frame[int]:
        if n <= 1:
            return acc, lambda: None
        return None, lambda: factorial(n - 1, acc * n)

    result = list(trampoline(lambda: factorial(5)))
    assert result == [120]


def test_mutual_recursion():
    """Even/odd check via mutual tail recursion."""

    @tailcall
    def is_even(n: int) -> Frame[bool]:
        if n == 0:
            return True, lambda: None
        return None, lambda: is_odd(n - 1)

    @tailcall
    def is_odd(n: int) -> Frame[bool]:
        if n == 0:
            return False, lambda: None
        return None, lambda: is_even(n - 1)

    assert list(trampoline(lambda: is_even(1000))) == [True]
    assert list(trampoline(lambda: is_odd(1000))) == [False]
    assert list(trampoline(lambda: is_even(999))) == [False]
    assert list(trampoline(lambda: is_odd(999))) == [True]


def test_multiple_yields():
    """Generate sequence with multiple intermediate results."""

    @tailcall
    def range_acc(n: int, acc: list[int]) -> Frame[int]:
        if n < 0:
            return None
        return n, lambda: range_acc(n - 1, acc)

    result = list(trampoline(lambda: range_acc(5, [])))
    assert result == [5, 4, 3, 2, 1, 0]


def test_deep_recursion_without_overflow():
    """Verify no RecursionError with deep tail recursion."""
    limit = sys.getrecursionlimit()
    depth = limit * 2

    @tailcall
    def deep(n: int) -> Frame[int]:
        if n <= 0:
            return 0, lambda: None
        return None, lambda: deep(n - 1)

    result = list(trampoline(lambda: deep(depth)))
    assert result == [0]


def test_arguments_propagation():
    """Verify arguments and kwargs pass through correctly."""

    @tailcall
    def with_args(a: int, b: int, *, c: int) -> Frame[int]:
        total = a + b + c
        if total <= 0:
            return total, lambda: None
        return None, lambda: with_args(a - 1, b - 1, c=c - 1)

    result = list(trampoline(lambda: with_args(5, 3, c=2)))
    assert result == [-2]


def test_fibonacci_stream():
    """Generate Fibonacci sequence up to limit."""

    @tailcall
    def fib(a: int, b: int, limit: int) -> Frame[int]:
        if a > limit:
            return None
        return a, lambda: fib(b, a + b, limit)

    result = list(trampoline(lambda: fib(0, 1, 100)))
    assert result == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]


def test_no_decoration_returns_none():
    """Undecorated function terminating immediately."""

    def immediate() -> Frame[int]:
        return None

    result = list(trampoline(immediate))
    assert result == []


def test_closure_capture():
    """Verify closures work correctly in thunks."""
    multiplier = 3

    @tailcall
    def multiply_down(n: int) -> Frame[int]:
        if n <= 0:
            return None
        return n * multiplier, lambda: multiply_down(n - 1)

    result = list(trampoline(lambda: multiply_down(5)))
    assert result == [15, 12, 9, 6, 3]


# Hypothesis-based property tests


@given(st.integers(min_value=0, max_value=10000))
def test_countdown_length_matches_input(n: int):
    """Countdown produces exactly n results."""

    @tailcall
    def countdown(i: int) -> Frame[int]:
        if i <= 0:
            return None
        return i, lambda: countdown(i - 1)

    result = list(trampoline(lambda: countdown(n)))
    assert len(result) == n


@given(st.integers(min_value=0, max_value=10000))
def test_countdown_values_are_descending(n: int):
    """Countdown produces descending sequence."""

    @tailcall
    def countdown(i: int) -> Frame[int]:
        if i <= 0:
            return None
        return i, lambda: countdown(i - 1)

    result = list(trampoline(lambda: countdown(n)))
    if result:
        assert result == list(range(n, 0, -1))


@given(st.integers(min_value=1, max_value=20))
def test_factorial_matches_iterative(n: int):
    """Tail-recursive factorial matches iterative computation."""

    @tailcall
    def factorial(i: int, acc: int = 1) -> Frame[int]:
        if i <= 1:
            return acc, lambda: None
        return None, lambda: factorial(i - 1, acc * i)

    def iterative_factorial(x: int) -> int:
        result = 1
        for i in range(2, x + 1):
            result *= i
        return result

    result = list(trampoline(lambda: factorial(n)))
    assert result == [iterative_factorial(n)]


@given(st.integers(min_value=0, max_value=1000))
def test_even_odd_parity(n: int):
    """Even/odd check matches modulo operation."""

    @tailcall
    def is_even(i: int) -> Frame[bool]:
        if i == 0:
            return True, lambda: None
        return None, lambda: is_odd(i - 1)

    @tailcall
    def is_odd(i: int) -> Frame[bool]:
        if i == 0:
            return False, lambda: None
        return None, lambda: is_even(i - 1)

    even_result = list(trampoline(lambda: is_even(n)))
    odd_result = list(trampoline(lambda: is_odd(n)))

    assert even_result == [n % 2 == 0]
    assert odd_result == [n % 2 == 1]


@given(st.integers(min_value=0, max_value=500))
def test_fibonacci_invariant(limit: int):
    """Each Fibonacci number is sum of previous two."""

    @tailcall
    def fib(a: int, b: int, lim: int) -> Frame[int]:
        if a > lim:
            return None
        return a, lambda: fib(b, a + b, lim)

    result = list(trampoline(lambda: fib(0, 1, limit)))

    if len(result) >= 3:
        for i in range(2, len(result)):
            assert result[i] == result[i - 1] + result[i - 2]


@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100),
)
def test_sum_accumulation(a: int, b: int, c: int):
    """Sum accumulation terminates at or below zero."""

    @tailcall
    def accumulate(x: int, y: int, z: int) -> Frame[int]:
        total = x + y + z
        if total <= 0:
            return total, lambda: None
        return None, lambda: accumulate(x - 1, y - 1, z - 1)

    result = list(trampoline(lambda: accumulate(a, b, c)))

    assert len(result) == 1
    assert result[0] <= 0


@given(st.integers(min_value=0, max_value=100))
def test_multiple_yields_count(n: int):
    """Yielding at each step produces n+1 results."""

    @tailcall
    def count_down(i: int) -> Frame[int]:
        if i < 0:
            return None
        return i, lambda: count_down(i - 1)

    result = list(trampoline(lambda: count_down(n)))
    assert len(result) == n + 1
    assert result[0] == n
    assert result[-1] == 0


@given(st.integers(min_value=1, max_value=100), st.integers(min_value=2, max_value=10))
def test_closure_multiplication(n: int, multiplier: int):
    """Closure captures multiplier correctly."""

    @tailcall
    def multiply_down(i: int) -> Frame[int]:
        if i <= 0:
            return None
        return i * multiplier, lambda: multiply_down(i - 1)

    result = list(trampoline(lambda: multiply_down(n)))
    expected = [i * multiplier for i in range(n, 0, -1)]
    assert result == expected


@given(st.integers(min_value=0, max_value=sys.getrecursionlimit() * 2))
def test_no_stack_overflow(depth: int):
    """Deep recursion never raises RecursionError."""

    @tailcall
    def deep(i: int) -> Frame[int]:
        if i <= 0:
            return 0, lambda: None
        return None, lambda: deep(i - 1)

    result = list(trampoline(lambda: deep(depth)))
    assert result == [0]
