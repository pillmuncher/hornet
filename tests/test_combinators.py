# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""Tests for the Triple-Barrelled Continuation Monad (hornet.combinators)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from immutables import Map

from hornet.clauses import (
    Environment,
    deref_and_compress,
    unify,
    unify_any,
    unify_pairs,
    unify_variable,
)
from hornet.combinators import (
    amb,
    amb_from_iterable,
    bind,
    call_cc,
    call_ec,
    choice,
    cut,
    fail,
    failure,
    if_then_else,
    neg,
    prunable,
    seq,
    seq_from_iterable,
    success,
    then,
    unit,
)
from hornet.tailcalls import trampoline
from hornet.terms import Atom, Functor, Variable, Wildcard

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EMPTY_ENV: Environment = Map()


def run(goal, subst: Environment = EMPTY_ENV) -> list[Environment]:
    """Run a goal against a substitution and collect all results."""
    step = goal(None, subst)
    return list(trampoline(lambda: step(success, failure, failure)))


def ctx_run(goal, ctx=None, subst: Environment = EMPTY_ENV) -> list[Environment]:
    step = goal(ctx, subst)
    return list(trampoline(lambda: step(success, failure, failure)))


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def test_unit_succeeds_once():
    results = run(unit)
    assert len(results) == 1
    assert results[0] == EMPTY_ENV


def test_fail_produces_no_results():
    assert run(fail) == []


def test_cut_succeeds_once():
    results = run(cut)
    assert len(results) == 1


def test_success_returns_subst():
    subst = Map().set(Variable('X'), 42)
    result, _ = success(None, subst, failure)
    assert result == subst


def test_failure_returns_none():
    assert failure() is None


# ---------------------------------------------------------------------------
# bind / then / seq
# ---------------------------------------------------------------------------


def test_bind_chains_unit():
    step = bind(unit(None, EMPTY_ENV), unit)
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) == 1


def test_then_both_succeed():
    results = run(then(unit, unit))
    assert len(results) == 1


def test_then_first_fails():
    results = run(then(fail, unit))
    assert results == []


def test_then_second_fails():
    results = run(then(unit, fail))
    assert results == []


def test_seq_empty_is_unit():
    results = run(seq())
    assert len(results) == 1


def test_seq_multiple():
    results = run(seq(unit, unit, unit))
    assert len(results) == 1


def test_seq_with_fail():
    results = run(seq(unit, fail, unit))
    assert results == []


def test_seq_from_iterable():
    results = run(seq_from_iterable([unit, unit]))
    assert len(results) == 1


# ---------------------------------------------------------------------------
# choice / amb
# ---------------------------------------------------------------------------


def test_choice_first_succeeds():
    results = run(choice(unit, fail))
    assert len(results) == 1


def test_choice_second_on_failure():
    results = run(choice(fail, unit))
    assert len(results) == 1


def test_choice_both_succeed():
    results = run(choice(unit, unit))
    assert len(results) == 2


def test_choice_both_fail():
    results = run(choice(fail, fail))
    assert results == []


def test_amb_empty_is_fail():
    results = run(amb())
    assert results == []


def test_amb_single():
    results = run(amb(unit))
    assert len(results) == 1


def test_amb_multiple():
    results = run(amb(unit, unit, unit))
    assert len(results) == 3


def test_amb_with_fail():
    results = run(amb(unit, fail, unit))
    assert len(results) == 2


def test_amb_from_iterable():
    results = run(amb_from_iterable([unit, unit]))
    assert len(results) == 2


# ---------------------------------------------------------------------------
# prunable / cut interaction
# ---------------------------------------------------------------------------


def test_prunable_cut_stops_search():
    # prunable sets prune=no, so cut inside just triggers backtracking.
    # All three branches still produce results.
    results = run(prunable([unit, cut, unit]))
    assert len(results) == 2


def test_prunable_without_cut_gives_all():
    results = run(prunable([unit, unit, unit]))
    assert len(results) == 3


def test_cut_in_seq_prunes_outer_choice():
    # choice(seq(cut, unit), unit) — cut should prune the second branch
    results = run(prunable([choice(seq(cut, unit), unit)]))
    assert len(results) == 1


# ---------------------------------------------------------------------------
# neg
# ---------------------------------------------------------------------------


def test_neg_of_fail_succeeds():
    results = run(neg(fail))
    assert len(results) == 1


def test_neg_of_unit_fails():
    results = run(neg(unit))
    assert results == []


def test_neg_does_not_bind():
    # neg(unify(x, 42)) fails because unbound x unifies with 42 (neg of success = failure)
    x = Variable('X')
    results = run(neg(unify(x, 42)))
    assert results == []

    # neg(unify(x, 42)) succeeds when x is already bound to something else
    subst = Map().set(x, Atom('other'))
    results = run(neg(unify(x, 42)), subst)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# if_then_else
# ---------------------------------------------------------------------------


def test_if_then_else_cond_succeeds():
    results = run(if_then_else(unit, unit, fail))
    assert len(results) == 1


def test_if_then_else_cond_fails():
    results = run(if_then_else(fail, fail, unit))
    assert len(results) == 1


def test_if_then_else_commits_to_then():
    # if_then_else is a soft cut: once cond succeeds, else is not tried
    x = Variable('X')
    results = run(if_then_else(unify(x, 1), unit, unify(x, 2)))
    assert len(results) == 1
    assert results[0][x] == 1


# ---------------------------------------------------------------------------
# unify / deref_and_compress
# ---------------------------------------------------------------------------


def test_unify_identical_atoms():
    results = run(unify(Atom('a'), Atom('a')))
    assert len(results) == 1


def test_unify_different_atoms_fails():
    results = run(unify(Atom('a'), Atom('b')))
    assert results == []


def test_unify_variable_with_atom():
    x = Variable('X')
    results = run(unify(x, Atom('hello')))
    assert len(results) == 1
    assert results[0][x] == Atom('hello')


def test_unify_two_variables():
    x, y = Variable('X'), Variable('Y')
    results = run(unify(x, y))
    assert len(results) == 1


def test_unify_wildcard_always_succeeds():
    w = Wildcard()
    results = run(unify(w, Atom('anything')))
    assert len(results) == 1


def test_unify_wildcard_with_wildcard():
    results = run(unify(Wildcard(), Wildcard()))
    assert len(results) == 1


def test_unify_functor_same_indicator():
    x = Variable('X')
    f1 = Functor('f', x)
    f2 = Functor('f', Atom('a'))
    results = run(unify(f1, f2))
    assert len(results) == 1
    assert results[0][x] == Atom('a')


def test_unify_functor_different_name_fails():
    results = run(unify(Functor('f', Atom('a')), Functor('g', Atom('a'))))
    assert results == []


def test_unify_functor_different_arity_fails():
    results = run(unify(Functor('f', Atom('a')), Functor('f', Atom('a'), Atom('b'))))
    assert results == []


def test_unify_pairs():
    x, y = Variable('X'), Variable('Y')
    results = run(unify_pairs((x, Atom('a')), (y, Atom('b'))))
    assert len(results) == 1
    assert results[0][x] == Atom('a')
    assert results[0][y] == Atom('b')


def test_unify_any():
    x = Variable('X')
    results = run(unify_any(x, Atom('a'), Atom('b'), Atom('c')))
    assert len(results) == 3


def test_unify_variable_already_bound():
    x = Variable('X')
    subst = Map().set(x, Atom('a'))
    results = run(unify(x, Atom('a')), subst)
    assert len(results) == 1


def test_unify_variable_bound_conflict_fails():
    x = Variable('X')
    subst = Map().set(x, Atom('a'))
    results = run(unify(x, Atom('b')), subst)
    assert results == []


def test_deref_and_compress_unbound():
    x = Variable('X')
    subst, term = deref_and_compress(EMPTY_ENV, x)
    assert term is x


def test_deref_and_compress_follows_chain():
    x, y = Variable('X'), Variable('Y')
    subst = Map().set(x, y).set(y, Atom('end'))
    _, term = deref_and_compress(subst, x)
    assert term == Atom('end')


def test_deref_and_compress_path_compression():
    x, y = Variable('X'), Variable('Y')
    subst = Map().set(x, y).set(y, Atom('end'))
    new_subst, _ = deref_and_compress(subst, x)
    # After compression, X should point directly to Atom('end')
    assert new_subst[x] == Atom('end')


def test_deref_cyclic_raises():
    x = Variable('X')
    subst = Map().set(x, x)
    with pytest.raises(RuntimeError, match='Cyclic'):
        deref_and_compress(subst, x)


# ---------------------------------------------------------------------------
# call_cc / call_ec
# ---------------------------------------------------------------------------


def test_call_cc_passes_continuations():
    # call_cc returns a Step directly, not a Goal — wrap it as a Goal to run it
    def f(yes, no, prune):
        return unit(None, EMPTY_ENV)  # Step
    step = call_cc(f)
    results = list(trampoline(lambda: step(success, failure, failure)))
    assert len(results) == 1


def test_call_ec_escape_short_circuits():
    # escape should commit to the first solution found
    def f(escape):
        return then(amb(unit, unit, unit), escape(unit))
    results = run(call_ec(f))
    assert len(results) == 1


def test_call_ec_without_escape_gives_all():
    def f(escape):
        return amb(unit, unit)
    results = run(call_ec(f))
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------


@given(st.integers())
def test_unify_integer_with_itself(n: int):
    results = run(unify(n, n))
    assert len(results) == 1


@given(st.integers(), st.integers())
def test_unify_different_integers_fails(a: int, b: int):
    if a != b:
        results = run(unify(a, b))
        assert results == []


@given(st.integers(min_value=1, max_value=10))
def test_amb_n_units_gives_n_results(n: int):
    results = run(amb_from_iterable([unit] * n))
    assert len(results) == n


@given(st.integers(min_value=0, max_value=10))
def test_seq_n_units_gives_one_result(n: int):
    results = run(seq_from_iterable([unit] * n))
    assert len(results) == 1


@given(st.text(min_size=1, max_size=10, alphabet='abcdefghij'))
def test_unify_atom_with_itself(name: str):
    a = Atom(name)
    results = run(unify(a, a))
    assert len(results) == 1


@given(st.text(min_size=1, max_size=5, alphabet='abcde'),
       st.text(min_size=1, max_size=5, alphabet='fghij'))
def test_unify_distinct_atoms_fails(name1: str, name2: str):
    results = run(unify(Atom(name1), Atom(name2)))
    assert results == []


@given(st.integers())
def test_neg_of_specific_unification(n: int):
    x = Variable('X')
    subst = Map().set(x, n)
    # neg(unify(x, n)) should fail because x is already n
    results = run(neg(unify(x, n)), subst)
    assert results == []


@given(st.integers(min_value=2, max_value=5))
def test_choice_depth(n: int):
    # chain of choices all succeeding gives n results
    goals = [unit] * n
    combined = goals[0]
    for g in goals[1:]:
        combined = choice(combined, g)
    results = run(combined)
    assert len(results) == n


# ---------------------------------------------------------------------------
# Additional coverage: unify_variable already-bound recursive case
# ---------------------------------------------------------------------------


def test_unify_variable_bound_to_variable():
    # variable is bound to another variable, triggers recursive unify
    x, y = Variable('X'), Variable('Y')
    subst = Map().set(x, y)  # X -> Y, Y unbound
    results = run(unify(x, Atom('a')), subst)
    assert len(results) == 1
    assert results[0][y] == Atom('a')
