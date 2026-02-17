# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""Tests for the State monad implementation."""

from hypothesis import given
from hypothesis import strategies as st

from hornet.states import State, const, get_state, identity, set_state, with_state

# Traditional tests


def test_state_unit_returns_value_unchanged():
    """State.unit preserves value and state."""
    state = State.unit(42)
    value, s = state.run(0)
    assert value == 42
    assert s == 0


def test_state_bind_chains_computations():
    """Bind threads state through computations."""
    state = State.unit(10).bind(lambda x: State.unit(x + 5))
    value, s = state.run(0)
    assert value == 15


def test_state_bind_preserves_state_changes():
    """Bind propagates state modifications."""

    def increment_state(x: int) -> State[int, int]:
        return State(lambda s: (x, s + 1))

    state = State.unit(100).bind(increment_state).bind(increment_state)
    value, s = state.run(0)
    assert value == 100
    assert s == 2


def test_get_state_retrieves_current_state():
    """get_state returns current state without modification."""
    state = get_state()
    value, s = state.run(42)
    assert value == 42
    assert s == 42


def test_get_state_with_function():
    """get_state applies function to state."""
    state = get_state(lambda x: x * 2)
    value, s = state.run(10)
    assert value == 20
    assert s == 10


def test_set_state_modifies_state():
    """set_state updates state."""
    state = set_state(lambda s: s + 10)
    value, s = state.run(5)
    assert value is None
    assert s == 15


def test_set_state_const_replacement():
    """set_state can replace state entirely."""
    state = set_state(const(100))
    value, s = state.run(0)
    assert value is None
    assert s == 100


def test_with_state_decorator_simple():
    """with_state wraps generator into State monad."""

    @with_state
    def increment():
        state = yield get_state()
        yield set_state(lambda s: s + 1)
        return state

    value, s = increment().run(10)
    assert value == 10
    assert s == 11


def test_with_state_accumulation():
    """with_state accumulates state changes."""

    @with_state
    def add_three():
        yield set_state(lambda s: s + 1)
        yield set_state(lambda s: s + 1)
        yield set_state(lambda s: s + 1)
        final = yield get_state()
        return final

    value, s = add_three().run(0)
    assert value == 3
    assert s == 3


def test_with_state_with_parameters():
    """with_state handles function parameters."""

    @with_state
    def add_value(n: int):
        state = yield get_state()
        yield set_state(lambda s: s + n)
        return state

    value, s = add_value(5).run(10)
    assert value == 10
    assert s == 15


def test_identity_function():
    """identity returns its argument unchanged."""
    assert identity(42) == 42
    assert identity('hello') == 'hello'
    assert identity([1, 2, 3]) == [1, 2, 3]


def test_const_function():
    """const creates function that ignores arguments."""
    f = const(42)
    assert f() == 42
    assert f(1, 2, 3) == 42


def test_multiple_get_states():
    """Multiple get_state calls in sequence."""

    @with_state
    def multiple_gets():
        x = yield get_state()
        yield set_state(lambda s: s + 10)
        y = yield get_state()
        return (x, y)

    value, s = multiple_gets().run(5)
    assert value == (5, 15)
    assert s == 15


def test_yielding_non_state_fails():
    """Yielding non-State values should fail gracefully."""

    @with_state
    def bad_yield():
        yield 42  # This is not a State
        return None

    try:
        bad_yield().run(0)
        assert False, 'Should have raised AttributeError'
    except AttributeError:
        pass  # Expected


# Hypothesis property tests


@given(st.integers(), st.integers())
def test_unit_ignores_initial_state(value: int, initial_state: int):
    """State.unit produces value regardless of initial state."""
    state = State.unit(value)
    result, s = state.run(initial_state)
    assert result == value
    assert s == initial_state


@given(st.integers())
def test_get_state_identity_law(initial_state: int):
    """get_state with identity satisfies monad laws."""
    state = get_state()
    value, s = state.run(initial_state)
    assert value == initial_state
    assert s == initial_state


@given(st.integers(), st.integers())
def test_set_state_overwrites(initial: int, new: int):
    """set_state replaces state completely."""
    state = set_state(const(new))
    _, s = state.run(initial)
    assert s == new


@given(st.integers(), st.integers())
def test_bind_left_identity(value: int, initial_state: int):
    """Monad left identity: unit(a).bind(f) ≡ f(a)."""

    def f(x: int) -> State[int, int]:
        return State(lambda s: (x * 2, s + 1))

    left = State.unit(value).bind(f).run(initial_state)
    right = f(value).run(initial_state)
    assert left == right


@given(st.integers(), st.integers())
def test_bind_right_identity(value: int, initial_state: int):
    """Monad right identity: m.bind(unit) ≡ m."""
    state = State(lambda s: (value, s + 1))

    left = state.bind(State.unit).run(initial_state)
    right = state.run(initial_state)
    assert left == right


@given(st.integers(), st.integers())
def test_bind_associativity(value: int, initial_state: int):
    """Monad associativity: (m.bind(f)).bind(g) ≡ m.bind(λx.f(x).bind(g))."""

    def f(x: int) -> State[int, int]:
        return State(lambda s: (x + 1, s + 1))

    def g(x: int) -> State[int, int]:
        return State(lambda s: (x * 2, s + 1))

    state = State.unit(value)

    left = state.bind(f).bind(g).run(initial_state)
    right = state.bind(lambda x: f(x).bind(g)).run(initial_state)
    assert left == right


@given(st.integers())
def test_get_set_roundtrip(initial: int):
    """Getting then setting state is identity."""

    @with_state
    def roundtrip():
        s = yield get_state()
        yield set_state(const(s))
        return s

    value, final = roundtrip().run(initial)
    assert value == initial
    assert final == initial


@given(st.integers(), st.integers())
def test_set_get_retrieves_set_value(initial: int, new_value: int):
    """Setting then getting retrieves the set value."""

    @with_state
    def set_then_get():
        yield set_state(const(new_value))
        result = yield get_state()
        return result

    value, final = set_then_get().run(initial)
    assert value == new_value
    assert final == new_value


@given(st.integers(), st.integers(), st.integers())
def test_set_set_last_wins(initial: int, first: int, second: int):
    """Sequential sets keep only the last value."""

    @with_state
    def double_set():
        yield set_state(const(first))
        yield set_state(const(second))
        return None

    _, final = double_set().run(initial)
    assert final == second


@given(st.integers(), st.lists(st.integers(), min_size=0, max_size=20))
def test_accumulation_sequence(initial: int, increments: list[int]):
    """State accumulates multiple operations correctly."""

    @with_state
    def accumulate():
        for inc in increments:
            yield set_state(lambda s, i=inc: s + i)
        return (yield get_state())

    value, final = accumulate().run(initial)
    expected = initial + sum(increments)
    assert value == expected
    assert final == expected


@given(st.integers(-1000, 1000), st.integers(-1000, 1000))
def test_with_state_complex_computation(a: int, b: int):
    """with_state handles complex stateful computations."""

    @with_state
    def compute():
        x = yield get_state()
        yield set_state(lambda s: s + a)
        y = yield get_state()
        yield set_state(lambda s: s * 2)
        z = yield get_state()
        return (x, y, z)

    (x, y, z), final = compute().run(b)
    assert x == b
    assert y == b + a
    assert z == (b + a) * 2
    assert final == (b + a) * 2


@given(st.text(), st.integers())
def test_state_polymorphic_value(value: str, state: int):
    """State monad works with different value types."""
    s = State.unit(value)
    result, final = s.run(state)
    assert result == value
    assert final == state


@given(st.integers())
def test_get_state_with_transformation(initial: int):
    """get_state applies transformation function correctly."""
    state = get_state(lambda x: x * 3 + 7)
    value, final = state.run(initial)
    assert value == initial * 3 + 7
    assert final == initial
