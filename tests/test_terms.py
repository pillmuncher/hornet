# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""Tests for the Hornet term algebra."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hornet.terms import (
    DCG,
    EMPTY,
    WILDCARD,
    Add,
    AllOf,
    AnyOf,
    Atom,
    BitAnd,
    BitOr,
    BitXor,
    Cons,
    Div,
    FloorDiv,
    Functor,
    HornetRule,
    Invert,
    LShift,
    Mod,
    Mul,
    Pow,
    RShift,
    Sub,
    UAdd,
    USub,
    Variable,
    Wildcard,
    fresh_name,
    fresh_variable,
    promote,
    rank,
    symbol,
)

# Basic term construction tests


def test_variable_creation():
    """Variables have names."""
    var = Variable('X')
    assert var.name == 'X'
    assert str(var) == 'X'


def test_wildcard_singleton():
    """Wildcard is a singleton."""
    assert WILDCARD.name == '_'
    assert str(WILDCARD) == '_'


def test_atom_creation():
    """Atoms are symbolic constants."""
    atom = Atom('foo')
    assert atom.name == 'foo'
    assert str(atom) == 'foo'
    assert atom.indicator == ('foo', 0)


def test_atom_call_creates_functor():
    """Calling an Atom creates a Functor."""
    parent = Atom('parent')
    term = parent('alice', 'bob')
    assert isinstance(term, Functor)
    assert term.name == 'parent'
    assert len(term.args) == 2


def test_functor_creation():
    """Functors have name and arguments."""
    f = Functor('f', Atom('a'), Variable('X'))
    assert f.name == 'f'
    assert len(f.args) == 2
    assert f.indicator == ('f', 2)
    assert str(f) == 'f(a, X)'


def test_empty_list():
    """Empty is the nil list."""
    assert EMPTY.name == '[]'
    assert str(EMPTY) == '[]'
    assert EMPTY.indicator == ('[]', 0)


def test_cons_construction():
    """Cons builds list structure."""
    lst = Cons(Atom('a'), Cons(Atom('b'), EMPTY))
    assert lst.head == Atom('a')
    assert isinstance(lst.tail, Cons)
    assert str(lst) == '[a, b]'


def test_cons_with_tail_variable():
    """Cons can have variable tail."""
    lst = Cons(Atom('a'), Variable('T'))
    assert str(lst) == '[a | T]'


# Operator overloading tests


def test_unary_operators():
    """Unary operators construct correct terms."""
    x = Variable('X')
    assert isinstance(-x, USub)
    assert isinstance(+x, UAdd)
    assert isinstance(~x, Invert)


def test_arithmetic_operators():
    """Arithmetic operators construct terms."""
    x, y = Variable('X'), Variable('Y')

    assert isinstance(x + y, Add)
    assert isinstance(x - y, Sub)
    assert isinstance(x * y, Mul)
    assert isinstance(x / y, Div)
    assert isinstance(x // y, FloorDiv)
    assert isinstance(x % y, Mod)
    assert isinstance(x**y, Pow)


def test_bitwise_operators():
    """Bitwise operators construct terms."""
    x, y = Variable('X'), Variable('Y')

    assert isinstance(x << y, LShift)
    assert isinstance(x >> y, RShift)
    assert isinstance(x & y, BitAnd)
    assert isinstance(x ^ y, BitXor)
    assert isinstance(x | y, BitOr)


def test_reflected_operators():
    """Reflected operators work with Python primitives."""
    x = Variable('X')

    assert isinstance(5 + x, Add)
    assert isinstance(5 * x, Mul)
    assert str(5 + x) == '5 + X'


def test_operator_precedence_display():
    """Operators display with correct precedence."""
    x, y, z = Variable('X'), Variable('Y'), Variable('Z')

    # Multiplication binds tighter than addition
    expr = x + y * z
    assert str(expr) == 'X + Y * Z'

    # Power binds tighter than multiplication
    expr = x * y**z
    assert str(expr) == 'X * Y ** Z'


def test_operator_parenthesization():
    """Lower precedence operators get parenthesized."""
    x, y, z = Variable('X'), Variable('Y'), Variable('Z')

    expr = (x + y) * z
    assert str(expr) == '(X + Y) * Z'


# Rule construction tests


def test_rule_creation_with_when():
    """NonVariable.when() creates rules."""
    head = Atom('parent')('alice', Variable('X'))
    body = Atom('mother')('alice', Variable('X'))
    rule = head.when(body)

    assert isinstance(rule, HornetRule)
    assert rule.head == head
    assert isinstance(rule.body, AllOf)


def test_rule_with_multiple_goals():
    """Rules can have multiple body goals."""
    x = Variable('X')
    head = Atom('grandparent')('alice', x)
    rule = head.when(Atom('parent')('alice', Variable('Y')), Atom('parent')(Variable('Y'), x))

    assert isinstance(rule.body, AllOf)
    assert len(rule.body.args) == 2


# Promotion tests


def test_promote_primitives():
    """Primitives promote to themselves."""
    assert promote(42) == 42
    assert promote('hello') == 'hello'
    assert promote(3.14) == 3.14
    assert promote(True) is True


def test_promote_empty_list():
    """Empty list promotes to EMPTY."""
    assert promote([]) == EMPTY


def test_promote_python_list():
    """Python lists promote to Cons chains."""
    result = promote([1, 2, 3])
    assert isinstance(result, Cons)
    assert result.head == 1
    assert str(result) == '[1, 2, 3]'


def test_promote_list_with_tail():
    """List with | operator promotes correctly."""
    x = Variable('X')
    result = promote([1, 2 | x])
    assert str(result) == '[1, 2 | X]'


def test_promote_nested_structures():
    """Nested structures promote recursively."""
    result = promote([1, [2, 3]])
    assert isinstance(result, Cons)
    assert isinstance(result.tail.head, Cons)


def test_promote_functor_recursively():
    """Functors promote their arguments."""
    f = Functor('f', [1, 2], Variable('X'))
    result = promote(f)
    assert isinstance(result.args[0], Cons)


# Symbol parsing tests


def test_symbol_wildcard():
    """Underscore parses as wildcard."""
    result = symbol('_')
    assert isinstance(result, Wildcard)


def test_symbol_variable():
    """Uppercase starts variable."""
    result = symbol('X')
    assert isinstance(result, Variable)
    assert result.name == 'X'

    result = symbol('Var')
    assert isinstance(result, Variable)


def test_symbol_atom():
    """Lowercase starts atom."""
    result = symbol('foo')
    assert isinstance(result, Atom)
    assert result.name == 'foo'


def test_symbol_invalid():
    """Invalid names raise AttributeError."""
    with pytest.raises(AttributeError):
        symbol('123invalid')


# Fresh variable generation tests


def test_fresh_variable_uniqueness():
    """Fresh variables have unique names."""
    v1 = fresh_variable()
    v2 = fresh_variable()
    assert v1.name != v2.name


def test_fresh_name_with_prefix():
    """Fresh names can have custom prefix."""
    name1 = fresh_name('Temp')
    name2 = fresh_name('Temp')
    assert name1.startswith('Temp!')
    assert name1 != name2


# DCG expansion tests


def test_dcg_atom_expansion():
    """DCG expands atom to functor with difference list."""
    result = DCG(Atom('noun'))
    assert isinstance(result, Functor)
    assert result.name == 'noun'
    assert len(result.args) == 2


def test_dcg_functor_expansion():
    """DCG expands functor with added state arguments."""
    result = DCG(Functor('noun', Atom('cat')))
    assert isinstance(result, Functor)
    assert result.name == 'noun'
    assert len(result.args) == 3  # original arg + 2 state args


def test_dcg_rule_expansion():
    """DCG expands rules with body goals."""
    rule = Atom('sentence').when(Atom('noun'), Atom('verb'))
    result = DCG(rule)

    assert isinstance(result, HornetRule)
    assert isinstance(result.head, Functor)
    assert isinstance(result.body, AllOf)


def test_dcg_list_expansion():
    """DCG expands lists to unification goals."""
    rule = Atom('word').when([Atom('h'), Atom('i')])
    result = DCG(rule)

    assert isinstance(result.body, AllOf)


# Rank tests


def test_rank_ordering():
    """Operators have correct precedence ranks."""
    assert rank(Pow(None, None)) > rank(Mul(None, None))
    assert rank(Mul(None, None)) > rank(Add(None, None))
    assert rank(Add(None, None)) > rank(BitAnd(None, None))


# Hypothesis property tests


@given(st.integers(), st.integers())
def test_promote_preserves_integers(a: int, b: int):
    """Integers promote to themselves."""
    assert promote(a) == a
    assert promote(b) == b


@given(st.lists(st.integers(), max_size=10))
def test_promote_list_length(items: list[int]):
    """Promoted lists have correct length when expanded."""
    if not items:
        assert promote(items) == EMPTY
        return

    result = promote(items)
    count = 0
    tail = result
    while isinstance(tail, Cons):
        count += 1
        tail = tail.tail

    assert count == len(items)
    assert tail == EMPTY


@given(st.text(min_size=1, max_size=5, alphabet='XYZ'))
def test_symbolic_addition_is_symmetric(var_name: str):
    """Symbolic addition creates Add terms regardless of order."""
    x = Variable(var_name)
    y = Variable('Y')

    add1 = x + y
    add2 = y + x

    # Both create Add terms (though with different operand order)
    assert isinstance(add1, Add)
    assert isinstance(add2, Add)


@given(st.text(min_size=1, max_size=20))
def test_fresh_variable_always_variable(prefix: str):
    """Fresh variables are always Variable instances."""
    # Use valid prefix
    if not prefix[0].isalpha():
        prefix = 'V' + prefix

    var = fresh_variable(prefix)
    assert isinstance(var, Variable)
    assert prefix in var.name


@given(st.lists(st.integers()), st.integers())
def test_cons_head_tail_invariant(items: list[int], tail_val: int):
    """Cons preserves head/tail structure."""
    if not items:
        return

    result = promote(items)
    if isinstance(result, Cons):
        assert result.head == items[0]


def test_operator_str_no_extra_parens():
    """Simple expressions don't over-parenthesize."""
    x, y = Variable('X'), Variable('Y')

    # Simple binary ops shouldn't have parens
    expr = x + y
    assert '(' not in str(expr)

    expr = x * y
    assert '(' not in str(expr)


def test_compound_indicator_consistency():
    """Indicators reflect actual arity."""
    f0 = Functor('f')
    f1 = Functor('f', Variable('X'))
    f2 = Functor('f', Variable('X'), Variable('Y'))

    assert f0.indicator == ('f', 0)
    assert f1.indicator == ('f', 1)
    assert f2.indicator == ('f', 2)


def test_promote_tuple_preserves_structure():
    """Tuples are promoted element-wise."""
    result = promote((1, [2, 3], Variable('X')))
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert result[0] == 1
    assert isinstance(result[1], Cons)
    assert isinstance(result[2], Variable)


def test_variable_not_callable():
    """Variables cannot be called as functors."""
    x = Variable('X')
    with pytest.raises(TypeError):
        x('arg')


def test_allof_anyof_construction():
    """AllOf and AnyOf collect multiple goals."""
    goals = [Atom('a'), Atom('b'), Atom('c')]

    all_goals = AllOf(*goals)
    assert len(all_goals.args) == 3
    assert all_goals.name == 'all_of'

    any_goals = AnyOf(*goals)
    assert len(any_goals.args) == 3


# Simpler, more constrained property tests


@given(st.from_regex(r'[a-z][a-z0-9_]*', fullmatch=True))
def test_atom_symbol_roundtrip(name: str):
    """Valid atom names roundtrip correctly."""
    result = symbol(name)
    assert isinstance(result, Atom)
    assert result.name == name


@given(
    st.from_regex(r'[A-Z_][A-Za-z0-9_]*', fullmatch=True).filter(
        lambda s: s != '_' and not (s.startswith('__') and s.endswith('__'))
    )
)
def test_variable_symbol_roundtrip(name: str):
    """Valid variable names roundtrip correctly."""
    result = symbol(name)
    assert isinstance(result, Variable)
    assert result.name == name


@given(st.text(min_size=1, max_size=10, alphabet='XYZ'))
def test_symbolic_operators_always_symbolic(var_name: str):
    """Operations on symbolic terms always produce symbolic results."""
    x = Variable(var_name)
    y = Variable('Y')

    # All operators produce symbolic terms
    assert isinstance(x + y, Add)
    assert isinstance(x - y, Sub)
    assert isinstance(x * y, Mul)
    assert isinstance(x / y, Div)

    # Mixed with primitives still produces symbolic
    assert isinstance(x + 5, Add)
    assert isinstance(5 + x, Add)


def test_operator_creates_compound_structure():
    """Operators on symbolic terms create compound structures."""
    x = Variable('X')
    y = Variable('Y')

    # Operators on symbolic terms create operators
    add1 = x + y
    add2 = y + x

    assert isinstance(add1, Add)
    assert isinstance(add2, Add)
    assert type(add1) is type(add2)

    # Integers promote to themselves and use Python's operators
    assert promote(5) == 5
    assert promote(5) + promote(3) == 8  # Normal Python arithmetic

    # Only when at least one operand is Symbolic do we get Add terms
    assert isinstance(Variable('X') + 5, Add)
    assert isinstance(5 + Variable('X'), Add)


def test_reflected_sub():
    x = Variable('X')
    assert isinstance(5 - x, Sub)


def test_reflected_truediv():
    x = Variable('X')
    assert isinstance(5 / x, Div)


def test_reflected_floordiv():
    x = Variable('X')
    assert isinstance(5 // x, FloorDiv)


def test_reflected_mod():
    x = Variable('X')
    assert isinstance(5 % x, Mod)


def test_reflected_pow():
    x = Variable('X')
    assert isinstance(5**x, Pow)


def test_reflected_lshift():
    x = Variable('X')
    assert isinstance(5 << x, LShift)


def test_reflected_rshift():
    x = Variable('X')
    assert isinstance(5 >> x, RShift)


def test_reflected_and():
    x = Variable('X')
    assert isinstance(5 & x, BitAnd)


def test_reflected_xor():
    x = Variable('X')
    assert isinstance(5 ^ x, BitXor)


def test_reflected_or():
    x = Variable('X')
    assert isinstance(5 | x, BitOr)


def test_reflected_matmul():
    from hornet.terms import MatMul

    x = Variable('X')
    assert isinstance(x @ 5, MatMul)
    assert isinstance(5 @ x, MatMul)  # __rmatmul__


def test_unary_operator_str_parenthesized():
    # USub of a lower-rank expression gets parenthesized
    x, y = Variable('X'), Variable('Y')
    expr = -(x + y)  # Add has lower rank than USub
    assert '(' in str(expr)


def test_unary_operator_str_no_parens():
    x = Variable('X')
    expr = -x
    assert str(expr) == '-X'


def test_functor_zero_args_str():
    f = Functor('f')
    assert str(f) == 'f()'


def test_dcg_anyof_in_body():
    from hornet.terms import DCG, AllOf, AnyOf

    rule = Atom('a').when(AnyOf(Atom('b'), Atom('c')))
    result = DCG(rule)
    # body is AllOf wrapping the expanded AnyOf
    assert isinstance(result.body, AllOf)
    assert isinstance(result.body.args[0], AnyOf)


def test_dcg_functor_head():
    from hornet.terms import DCG

    rule = Functor('f', Atom('x')).when(Atom('g'))
    result = DCG(rule)
    assert result.head.name == 'f'
    assert len(result.head.args) == 3  # original arg + 2 state args


def test_promote_exception():
    e = ValueError('oops')
    assert promote(e) is e


def test_symbol_dunder_raises():
    with pytest.raises(AttributeError):
        symbol('__init__')
