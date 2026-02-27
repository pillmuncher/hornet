# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""Tests for hornet.clauses and the bootstrapped database (hornet.__init__)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hornet import database
from hornet.clauses import Database, Environment, Subst, make_clause, make_term, predicate, resolve
from hornet.combinators import Step, unit
from hornet.symbols import (
    A,
    B,
    L,
    N,
    R,
    S,
    X,
    append,
    arithmetic_equal,
    call,
    cut,
    equal,
    fail,
    findall,
    greater,
    ifelse,
    ignore,
    is_atom,
    is_atomic,
    is_bool,
    is_bytes,
    is_complex,
    is_constant,
    is_float,
    is_int,
    is_numeric,
    is_str,
    is_var,
    join,
    length,
    let,
    maplist,
    member,
    nonvar,
    once,
    phrase,
    repeat,
    reverse,
    select,
    smaller,
    throw,
    true,
    unequal,
    univ,
)
from hornet.terms import Atom, DCGs, Empty, Functor, HornetRule, Variable, promote

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def db() -> Database:
    return database()


def solutions(db: Database, *goals) -> list[Subst]:
    return list(db.ask(*goals))


def first(db: Database, *goals) -> Subst:
    return solutions(db, *goals)[0]


# ---------------------------------------------------------------------------
# make_term / make_clause
# ---------------------------------------------------------------------------


def test_make_term_atom():
    term, env = make_term(Atom('foo'))
    assert term == Atom('foo')
    assert len(env) == 0


def test_make_term_variable_renamed():
    x = Variable('X')
    term, env = make_term(x)
    assert isinstance(term, Variable)
    assert term.name != 'X'  # fresh name
    assert x in env


def test_make_term_functor():
    f = Functor('f', Variable('X'), Atom('a'))
    term, env = make_term(f)
    assert isinstance(term, Functor)
    assert term.name == 'f'
    assert term.args[1] == Atom('a')


def test_make_clause_atomic_fact():
    clause, indicator = make_clause(Atom('foo'))
    assert indicator == ('foo', 0)


def test_make_clause_compound_fact():
    clause, indicator = make_clause(Functor('foo', Atom('a'), Atom('b')))
    assert indicator == ('foo', 2)


def test_make_clause_rule():
    head = Functor('foo', Variable('X'))
    body = Functor('bar', Variable('X'))
    rule = HornetRule(head, body)
    clause, indicator = make_clause(rule)
    assert indicator == ('foo', 1)


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------


def test_resolve_unknown_type_raises():
    with pytest.raises(TypeError):
        resolve(Variable('X'))


# ---------------------------------------------------------------------------
# Basic database operations
# ---------------------------------------------------------------------------


def test_fact_query():
    d = db()
    d.tell(Atom('foo')('bar'))
    results = solutions(d, Atom('foo')(X))
    assert len(results) == 1
    assert results[0][X] == 'bar'  # string literals are primitives, not Atoms


def test_multiple_facts():
    d = db()
    d.tell(Atom('color')('red'), Atom('color')('green'), Atom('color')('blue'))
    results = solutions(d, Atom('color')(X))
    assert len(results) == 3


def test_rule_query():
    d = db()
    d.tell(
        Atom('human')('socrates'),
        Atom('mortal')(X).when(Atom('human')(X)),
    )
    results = solutions(d, Atom('mortal')(X))
    assert len(results) == 1
    assert results[0][X] == 'socrates'


def test_new_child_inherits_facts():
    d = db()
    d.tell(Atom('base')('fact'))
    child = d.new_child()
    results = solutions(child, Atom('base')(X))
    assert len(results) == 1


# ---------------------------------------------------------------------------
# Built-in predicates: equality / unification
# ---------------------------------------------------------------------------


def test_equal():
    d = db()
    results = solutions(d, equal(X, Atom('hello')))
    assert results[0][X] == Atom('hello')


def test_equal_fails_on_mismatch():
    d = db()
    results = solutions(d, equal(Atom('a'), Atom('b')))
    assert results == []


def test_unequal():
    d = db()
    results = solutions(d, unequal(Atom('a'), Atom('b')))
    assert len(results) == 1


def test_unequal_fails_when_equal():
    d = db()
    results = solutions(d, unequal(Atom('a'), Atom('a')))
    assert results == []


# ---------------------------------------------------------------------------
# Built-in predicates: arithmetic
# ---------------------------------------------------------------------------


def test_let_addition():
    d = db()
    results = solutions(d, let(R, 2 + 3))
    assert results[0][R] == 5


def test_let_multiplication():
    d = db()
    results = solutions(d, let(R, 6 * 7))
    assert results[0][R] == 42


def test_let_subtraction():
    d = db()
    results = solutions(d, let(R, 10 - 3))
    assert results[0][R] == 7


def test_let_division():
    d = db()
    results = solutions(d, let(R, 10 / 4))
    assert results[0][R] == 2.5


def test_let_floordiv():
    d = db()
    results = solutions(d, let(R, 10 // 3))
    assert results[0][R] == 3


def test_let_modulo():
    d = db()
    results = solutions(d, let(R, 10 % 3))
    assert results[0][R] == 1


def test_let_power():
    d = db()
    results = solutions(d, let(R, 2**10))
    assert results[0][R] == 1024


def test_let_bitwise_and():
    d = db()
    results = solutions(d, let(R, 0b1100 & 0b1010))
    assert results[0][R] == 0b1000


def test_let_bitwise_or():
    d = db()
    results = solutions(d, let(R, 0b1100 | 0b1010))
    assert results[0][R] == 0b1110


def test_let_bitwise_xor():
    d = db()
    results = solutions(d, let(R, 0b1100 ^ 0b1010))
    assert results[0][R] == 0b0110


def test_let_lshift():
    d = db()
    results = solutions(d, let(R, 1 << 4))
    assert results[0][R] == 16


def test_let_rshift():
    d = db()
    results = solutions(d, let(R, 16 >> 2))
    assert results[0][R] == 4


def test_let_unary_neg():
    d = db()
    results = solutions(d, let(R, -5))
    assert results[0][R] == -5


def test_let_unary_pos():
    d = db()
    results = solutions(d, let(R, +5))
    assert results[0][R] == 5


def test_let_invert():
    d = db()
    results = solutions(d, let(R, ~0))
    assert results[0][R] == ~0


def test_let_unbound_variable_raises():
    d = db()
    with pytest.raises((ValueError, Exception)):
        solutions(d, let(R, X))


def test_arithmetic_equal():
    d = db()
    results = solutions(d, arithmetic_equal(2 + 3, 1 + 4))
    assert len(results) == 1


def test_arithmetic_equal_fails():
    d = db()
    results = solutions(d, arithmetic_equal(2 + 3, 1 + 3))
    assert results == []


def test_smaller():
    d = db()
    results = solutions(d, smaller(1, 2))
    assert len(results) == 1


def test_smaller_fails():
    d = db()
    results = solutions(d, smaller(2, 1))
    assert results == []


def test_greater():
    d = db()
    results = solutions(d, greater(2, 1))
    assert len(results) == 1


def test_greater_fails():
    d = db()
    results = solutions(d, greater(1, 2))
    assert results == []


# ---------------------------------------------------------------------------
# Built-in predicates: type checks
# ---------------------------------------------------------------------------


def test_is_var():
    d = db()
    results = solutions(d, is_var(X))
    assert len(results) == 1


def test_is_var_fails_on_atom():
    d = db()
    results = solutions(d, is_var(Atom('a')))
    assert results == []


def test_nonvar():
    d = db()
    results = solutions(d, nonvar(Atom('a')))
    assert len(results) == 1


def test_nonvar_fails_on_var():
    d = db()
    results = solutions(d, nonvar(X))
    assert results == []


def test_is_atom():
    d = db()
    results = solutions(d, is_atom(Atom('hello')))
    assert len(results) == 1


def test_is_atom_fails_on_functor():
    d = db()
    results = solutions(d, is_atom(Functor('f', Atom('a'))))
    assert results == []


def test_is_atomic_on_string():
    d = db()
    results = solutions(d, is_atomic('hello'))
    assert len(results) == 1


def test_is_int():
    d = db()
    results = solutions(d, is_int(42))
    assert len(results) == 1


def test_is_int_fails_on_float():
    d = db()
    results = solutions(d, is_int(3.14))
    assert results == []


def test_is_float():
    d = db()
    results = solutions(d, is_float(3.14))
    assert len(results) == 1


def test_is_bool():
    d = db()
    results = solutions(d, is_bool(True))
    assert len(results) == 1


def test_is_str():
    d = db()
    results = solutions(d, is_str('hello'))
    assert len(results) == 1


def test_is_numeric_int():
    d = db()
    results = solutions(d, is_numeric(42))
    assert len(results) == 1


def test_is_numeric_float():
    d = db()
    results = solutions(d, is_numeric(3.14))
    assert len(results) == 1


def test_is_complex():
    d = db()
    results = solutions(d, is_complex(1 + 2j))
    assert len(results) == 1


def test_is_bytes():
    d = db()
    results = solutions(d, is_bytes(b'hello'))
    assert len(results) == 1


def test_is_constant_on_string():
    d = db()
    results = solutions(d, is_constant('hello'))
    assert len(results) == 1


# ---------------------------------------------------------------------------
# Built-in predicates: control
# ---------------------------------------------------------------------------


def test_true():
    d = db()
    results = solutions(d, true)
    assert len(results) == 1


def test_fail_builtin():
    d = db()
    results = solutions(d, fail)
    assert results == []


def test_once_commits_to_first():
    d = db()
    d.tell(Atom('p'), Atom('p'))
    results = solutions(d, once(Atom('p')))
    assert len(results) == 1


def test_ignore_succeeds_even_if_goal_fails():
    d = db()
    results = solutions(d, ignore(fail))
    assert len(results) == 1


def test_call():
    d = db()
    results = solutions(d, call(true))
    assert len(results) == 1


def test_ifelse_true_branch():
    d = db()
    results = solutions(d, ifelse(true, equal(X, 1), equal(X, 2)))
    assert results[0][X] == 1


def test_ifelse_false_branch():
    d = db()
    results = solutions(d, ifelse(fail, equal(X, 1), equal(X, 2)))
    assert results[0][X] == 2


def test_throw_raises():
    d = db()
    with pytest.raises(Exception):
        solutions(d, throw(Exception('oops')))


def test_repeat_is_infinite():
    d = db()
    # take first 5 solutions
    results = []
    for s in d.ask(repeat):
        results.append(s)
        if len(results) >= 5:
            break
    assert len(results) == 5


def test_cut_prevents_backtracking():
    d = db()
    d.tell(Atom('p')(1), Atom('p')(2), Atom('p')(3))
    results = solutions(d, Atom('p')(X), cut)
    assert len(results) == 1
    assert results[0][X] == 1


# ---------------------------------------------------------------------------
# Built-in predicates: lists
# ---------------------------------------------------------------------------


def test_member():
    d = db()
    results = solutions(d, member(X, [1, 2, 3]))
    assert len(results) == 3
    assert [s[X] for s in results] == [1, 2, 3]


def test_member_fails_on_empty():
    d = db()
    results = solutions(d, member(X, []))
    assert results == []


def test_append_forward():
    d = db()
    results = solutions(d, append([1, 2], [3, 4], L))
    assert len(results) == 1
    assert str(results[0][L]) == '[1, 2, 3, 4]'


def test_append_backward():
    d = db()
    results = solutions(d, append(A, B, [1, 2, 3]))
    assert len(results) == 4


def test_reverse():
    d = db()
    results = solutions(d, reverse([1, 2, 3], R))
    assert len(results) == 1
    assert str(results[0][R]) == '[3, 2, 1]'


def test_select():
    d = db()
    results = solutions(d, select(X, [1, 2, 3], R))
    assert len(results) == 3


def test_length():
    d = db()
    results = solutions(d, length([1, 2, 3], N))
    assert results[0][N] == 3


def test_length_empty():
    d = db()
    results = solutions(d, length([], N))
    assert results[0][N] == 0


def test_maplist():
    d = db()
    # maplist(G, L) calls G(elem) for each elem via univ/call, so G must be a 1-arg predicate
    d.tell(Atom('positive')(X).when(greater(X, 0)))
    results = solutions(d, maplist(Atom('positive'), [1, 2, 3]))
    assert len(results) == 1


def test_findall():
    d = db()
    d.tell(Atom('p')(1), Atom('p')(2), Atom('p')(3))
    results = solutions(d, findall(X, Atom('p')(X), L))
    assert len(results) == 1
    assert str(results[0][L]) == '[1, 2, 3]'


def test_findall_no_solutions():
    d = db()
    # define p/1 but add no facts — findall should collect empty list
    d.tell(Atom('p')(X).when(fail))
    results = solutions(d, findall(X, Atom('p')(X), L))
    assert len(results) == 1
    assert results[0][L] == Empty()


def test_join():
    d = db()
    results = solutions(d, join(['hello', ' ', 'world'], S))
    assert results[0][S] == 'hello world'


# ---------------------------------------------------------------------------
# Built-in predicates: univ
# ---------------------------------------------------------------------------


def test_univ_atom_to_list():
    d = db()
    results = solutions(d, univ(Atom('foo'), L))
    assert len(results) == 1


def test_univ_functor_to_list():
    d = db()
    results = solutions(d, univ(Functor('f', Atom('a'), Atom('b')), L))
    assert len(results) == 1


def test_univ_list_to_functor():
    d = db()
    results = solutions(d, univ(X, promote([Atom('f'), Atom('a'), Atom('b')])))
    assert len(results) == 1
    assert isinstance(results[0][X], Functor)


# ---------------------------------------------------------------------------
# DCGs via phrase
# ---------------------------------------------------------------------------


def test_phrase_simple_grammar():
    d = db()
    d.tell(
        *DCGs(
            Atom('ab').when([Atom('a'), Atom('b')]),
        )
    )
    results = solutions(d, phrase(Atom('ab'), [Atom('a'), Atom('b')]))
    assert len(results) == 1


def test_phrase_fails_on_mismatch():
    d = db()
    d.tell(
        *DCGs(
            Atom('ab').when([Atom('a'), Atom('b')]),
        )
    )
    results = solutions(d, phrase(Atom('ab'), [Atom('a'), Atom('c')]))
    assert results == []


# ---------------------------------------------------------------------------
# Native Python predicates via @predicate
# ---------------------------------------------------------------------------


def test_predicate_decorator():
    d = db()

    @d.tell
    @predicate(Atom('ping')(X))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return unit(db, subst.env)

    results = solutions(d, Atom('ping')(Atom('hello')))
    assert len(results) == 1


def test_predicate_can_read_subst():
    d = db()
    seen = []

    @d.tell
    @predicate(Atom('spy')(X))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        seen.append(subst[X])
        return unit(db, subst.env)

    solutions(d, Atom('spy')(Atom('value')))
    assert seen == [Atom('value')]


# ---------------------------------------------------------------------------
# Hypothesis property tests
# ---------------------------------------------------------------------------


@given(st.integers(min_value=0, max_value=20))
def test_member_count(n: int):
    d = db()
    items = list(range(n))
    results = solutions(d, member(X, items))
    assert len(results) == n


@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_length_matches_python_len(items: list[int]):
    d = db()
    results = solutions(d, length(items, N))
    assert results[0][N] == len(items)


@given(st.lists(st.integers(), min_size=0, max_size=8))
def test_reverse_involution(items: list[int]):
    d = db()
    results = solutions(d, reverse(items, R))
    assert len(results) == 1
    results2 = solutions(d, reverse(results[0][R], S))
    assert len(results2) == 1
    # reversing twice gives back the original list structure
    assert str(results2[0][S]) == str(promote(items))


@given(st.integers(), st.integers())
def test_let_add_commutative(a: int, b: int):
    d = db()
    r1 = solutions(d, let(R, a + b))[0][R]
    r2 = solutions(d, let(R, b + a))[0][R]
    assert r1 == r2


@given(st.integers(min_value=-1000, max_value=1000), st.integers(min_value=-1000, max_value=1000))
def test_arithmetic_equal_reflexive(a: int, b: int):
    d = db()
    results = solutions(d, arithmetic_equal(a + b, b + a))
    assert len(results) == 1


@given(
    st.lists(st.integers(), min_size=0, max_size=5),
    st.lists(st.integers(), min_size=0, max_size=5),
)
def test_append_length_sum(xs: list[int], ys: list[int]):
    d = db()
    results = solutions(d, append(xs, ys, L))
    assert len(results) == 1
    len_results = solutions(d, length(results[0][L], N))
    assert len_results[0][N] == len(xs) + len(ys)


# ---------------------------------------------------------------------------
# Additional coverage: missed lines
# ---------------------------------------------------------------------------


def test_subst_len():
    from immutables import Map

    x = Variable('X')
    subst = Subst(Map().set(x, 42), Map())
    assert len(subst) == 1


def test_subst_cyclic_raises():
    from immutables import Map

    x = Variable('X')
    subst = Subst(Map().set(x, x), Map().set(x, x))
    with pytest.raises(RuntimeError, match='Cyclic'):
        subst[x]


def test_resolve_unsupported_type_raises():
    with pytest.raises(TypeError):
        resolve(Variable('X'))


def test_atomic_fact_via_atom_head_rule():
    # Covers the AtomicRule (Atom head) branch in new_clause
    d = db()
    d.tell(Atom('ping').when(true))
    results = solutions(d, Atom('ping'))
    assert len(results) == 1


def test_python_rule_atom_head():
    # Covers AtomicPythonRule branch in new_clause
    d = db()

    @d.tell
    @predicate(Atom('beep'))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return unit(db, subst.env)

    results = solutions(d, Atom('beep'))
    assert len(results) == 1


def test_make_term_wildcard():
    from hornet.terms import WILDCARD

    term, env = make_term(WILDCARD)
    assert term is WILDCARD


def test_make_term_allof_ground():
    from hornet.terms import AllOf

    term, env = make_term(AllOf(Atom('a'), Atom('b')))
    assert isinstance(term, AllOf)


def test_make_term_cons_ground():
    from hornet.terms import Cons

    term, env = make_term(promote([Atom('a'), Atom('b')]))
    assert isinstance(term, Cons)


def test_make_term_unary_operator():
    from hornet.terms import USub

    x = Variable('X')
    term, env = make_term(USub(x))
    assert isinstance(term, USub)


def test_make_term_binary_operator():
    from hornet.terms import Add

    x, y = Variable('X'), Variable('Y')
    term, env = make_term(x + y)
    assert isinstance(term, Add)


# ---------------------------------------------------------------------------
# Additional coverage: remaining missed lines in clauses.py
# ---------------------------------------------------------------------------


def test_atomic_fact_no_args():
    d = db()
    d.tell(Atom('ping'))
    results = solutions(d, Atom('ping'))
    assert len(results) == 1


def test_python_rule_indicator():
    from hornet.clauses import PythonRule

    d = db()

    @d.tell
    @predicate(Atom('boop'))
    def _(db: Database, subst: Subst) -> Step[Database, Environment]:
        return unit(db, subst.env)

    clause, indicator = make_clause(Atom('boop'))
    assert indicator == ('boop', 0)


def test_subst_deref_cyclic_direct():
    from immutables import Map

    x, y = Variable('X'), Variable('Y')
    # X -> Y -> X cycle
    subst = Subst(Map().set(x, y).set(y, x), Map().set(x, x).set(y, y))
    with pytest.raises(RuntimeError, match='Cyclic'):
        subst[x]


def test_resolve_non_callable_raises():
    from hornet.terms import EMPTY, Cons

    with pytest.raises(TypeError):
        resolve(Cons(Atom('a'), EMPTY))


def test_make_clause_atomic_python_rule():
    from hornet.clauses import PythonRule

    def body(env: Environment):
        def goal(db: Database, env: Environment) -> Step[Database, Environment]:
            return unit(db, env)

        return goal

    rule = PythonRule(Atom('zap'), body)
    clause, indicator = make_clause(rule)
    assert indicator == ('zap', 0)


def test_make_clause_returns_tuple():
    clause, indicator = make_clause(Functor('foo', Atom('a')))
    assert indicator == ('foo', 1)
