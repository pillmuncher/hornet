# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

"""
Hornet Term Algebra: A Deep EDSL for Logic Programming.

This module provides the structural building blocks for Hornet. Instead of
parsing Prolog strings, Hornet uses Python's own syntax—via operator
overloading and `__call__` implementation—to construct logic terms.

Key Concepts:
    - **Symbolic Construction**: Python expressions like `X + 5` or `f(X)`
      do not calculate values; they return nested `Symbolic` structures.
    - **Term Promotion**: The `promote()` utility (used internally)
      transparently converts Python primitives (int, str, list) into
      their Hornet equivalents (Literal, Atom, Cons).
    - **Rule Definition**: The `.when()` method on `NonVariable` terms
      provides a declarative syntax for defining Horn Clauses.
"""

from __future__ import annotations

import re as re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from itertools import count
from typing import Any, Callable, ClassVar, Iterator

from .states import StateOp, const, get_state, set_state, with_state

type PrimitiveType = str | int | float | bool | complex | bytes | tuple[Term, ...]
type AtomicType = PrimitiveType | Atom | Empty
type Term = Symbolic | PrimitiveType | Exception
type Indicator = tuple[str, int]


@dataclass(frozen=True, slots=True, init=False)
class Symbolic(ABC):
    """
    The root of the Hornet expression tree.

    Symbolic objects overload almost all Python dunder methods (arithmetic,
    bitwise, etc.). Instead of performing computation, these methods
    return `Operator` compounds, allowing the construction of arithmetic
    expressions that are evaluated later by predicates like `let`.
    """

    def __neg__(self: Term) -> USub:
        return USub(promote(self))

    def __pos__(self: Term) -> UAdd:
        return UAdd(promote(self))

    def __invert__(self: Term) -> Invert:
        return Invert(promote(self))

    def __add__(self, other: Term) -> Add:
        return Add(promote(self), promote(other))

    def __radd__(self, other: Term) -> Add:
        return Add(promote(other), promote(self))

    def __sub__(self, other: Term) -> Sub:
        return Sub(promote(self), promote(other))

    def __rsub__(self, other: Term) -> Sub:
        return Sub(promote(other), promote(self))

    def __mul__(self, other: Term) -> Mul:
        return Mul(promote(self), promote(other))

    def __rmul__(self, other: Term) -> Mul:
        return Mul(promote(other), promote(self))

    def __matmul__(self, other: Term) -> MatMul:
        return MatMul(promote(self), promote(other))

    def __rmatmul__(self, other: Term) -> MatMul:
        return MatMul(promote(other), promote(self))

    def __truediv__(self, other: Term) -> Div:
        return Div(promote(self), promote(other))

    def __rtruediv__(self, other: Term) -> Div:
        return Div(promote(other), promote(self))

    def __floordiv__(self, other: Term) -> FloorDiv:
        return FloorDiv(promote(self), promote(other))

    def __rfloordiv__(self, other: Term) -> FloorDiv:
        return FloorDiv(promote(other), promote(self))

    def __mod__(self, other: Term) -> Mod:
        return Mod(promote(self), promote(other))

    def __rmod__(self, other: Term) -> Mod:
        return Mod(promote(other), promote(self))

    def __pow__(self, other: Term) -> Pow:
        return Pow(promote(self), promote(other))

    def __rpow__(self, other: Term) -> Pow:
        return Pow(promote(other), promote(self))

    def __lshift__(self, other: Term) -> LShift:
        return LShift(promote(self), promote(other))

    def __rlshift__(self, other: Term) -> LShift:
        return LShift(promote(other), promote(self))

    def __rshift__(self, other: Term) -> RShift:
        return RShift(promote(self), promote(other))

    def __rrshift__(self, other: Term) -> RShift:
        return RShift(promote(other), promote(self))

    def __and__(self, other: Term) -> BitAnd:
        return BitAnd(promote(self), promote(other))

    def __rand__(self, other: Term) -> BitAnd:
        return BitAnd(promote(other), promote(self))

    def __xor__(self, other: Term) -> BitXor:
        return BitXor(promote(self), promote(other))

    def __rxor__(self, other: Term) -> BitXor:
        return BitXor(promote(other), promote(self))

    def __or__(self, other: Term) -> BitOr:
        return BitOr(promote(self), promote(other))

    def __ror__(self, other: Term) -> BitOr:
        return BitOr(promote(other), promote(self))

    def __call__(self, *_) -> Functor:
        raise TypeError(f'Atom required, not {self}')


@dataclass(repr=False, frozen=True, slots=True)
class Variable(Symbolic):
    name: str

    def __str__(self):
        return self.name


@dataclass(repr=False, frozen=True, slots=True)
class Wildcard(Symbolic):
    name: ClassVar[str] = '_'

    def __str__(self):
        return '_'


WILDCARD = Wildcard()


@dataclass(frozen=True, slots=True, init=False)
class NonVariable(Symbolic, ABC):
    def when(self, *args: Term | list[str]) -> Rule[Term]:
        return HornetRule(self, AllOf(*(promote(a) for a in args)))

    @property
    @abstractmethod
    def indicator(self) -> Indicator: ...


@dataclass(frozen=True, slots=True)
class Atom(NonVariable):
    """
    A symbolic constant or predicate head.

    In Hornet, an Atom is both a constant value and a 'functor factory'.
    Example:
        >>> parent = Atom('parent')
        >>> term = parent('bob', Variable('X'))
        >>> # 'term' is now a Functor(name='parent', args=(Atom('bob'), Variable('X')))
    """

    name: str

    @property
    def indicator(self) -> Indicator:
        return self.name, 0

    def __str__(self):
        return self.name

    def __call__(self, *args: Term) -> Functor:
        return Functor(self.name, *(promote(arg) for arg in args))


@dataclass(frozen=True, slots=True, init=False)
class Compound(NonVariable, ABC):
    """
    An N-ary logic structure.

    Represents a functor and its arguments. This is the primary way
    data (like lists) and goals (like predicates) are represented.
    """

    name: ClassVar[str]
    args: tuple[Term, ...] = ()

    @property
    def indicator(self) -> Indicator:
        return self.name, len(self.args)

    def __init__(self, *args: Term):
        object.__setattr__(self, 'args', args)


@dataclass(frozen=True, slots=True, init=False)
class Functor(Compound):
    name: str  # type: ignore

    def __init__(self, name: str, *args: Term):
        object.__setattr__(self, 'name', name)
        Compound.__init__(self, *args)

    def __str__(self):
        return f'{self.name}({", ".join(str(arg) for arg in self.args)})'


@dataclass(frozen=True, slots=True, init=False)
class Operator(Compound, ABC):
    """A specialized Compound representing a symbolic operation.

    Operators maintain the structure of an expression (e.g., A + B)
    so it can be printed in infix notation or evaluated arithmetically.
    """


@dataclass(frozen=True, slots=True, init=False)
class UnaryOperator(Operator, ABC):
    def __init__(self, operand: Term):
        Operator.__init__(self, operand)

    @property
    def indicator(self) -> Indicator:
        return self.name, 1

    @property
    def operand(self):
        return self.args[0]

    def __str__(self):
        if not isinstance(self.operand, (UnaryOperator, BinaryOperator)):
            return f'{self.name}{str(self.operand)}'
        elif rank(self.operand) < rank(self):
            return f'{self.name}{str(self.operand)}'
        else:
            return f'{self.name}({str(self.operand)})'


@dataclass(frozen=True, slots=True, init=False)
class BinaryOperator(Operator, ABC):
    def __init__(self, left: Term, right: Term):
        Operator.__init__(self, left, right)

    @property
    def indicator(self) -> Indicator:
        return self.name, 2

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        return self.args[1]

    def __str__(self):
        left, right = self.args
        if isinstance(left, BinaryOperator) and rank(left) < rank(self):
            left_str = f'({left})'
        else:
            left_str = str(left)
        if isinstance(right, BinaryOperator) and rank(right) < rank(self):
            right_str = f'({right})'
        else:
            right_str = str(right)
        return f'{left_str} {self.name} {right_str}'


@dataclass(frozen=True, slots=True, init=False)
class Invert(UnaryOperator):
    name: ClassVar[str] = '~'


@dataclass(frozen=True, slots=True, init=False)
class UAdd(UnaryOperator):
    name: ClassVar[str] = '+'


@dataclass(frozen=True, slots=True, init=False)
class USub(UnaryOperator):
    name: ClassVar[str] = '-'


@dataclass(frozen=True, slots=True, init=False)
class LShift(BinaryOperator):
    name: ClassVar[str] = '<<'


@dataclass(frozen=True, slots=True, init=False)
class RShift(BinaryOperator):
    name: ClassVar[str] = '>>'


@dataclass(frozen=True, slots=True, init=False)
class BitOr(BinaryOperator):
    name: ClassVar[str] = '|'


@dataclass(frozen=True, slots=True, init=False)
class BitXor(BinaryOperator):
    name: ClassVar[str] = '^'


@dataclass(frozen=True, slots=True, init=False)
class BitAnd(BinaryOperator):
    name: ClassVar[str] = '&'


@dataclass(frozen=True, slots=True, init=False)
class Add(BinaryOperator):
    name: ClassVar[str] = '+'


@dataclass(frozen=True, slots=True, init=False)
class Sub(BinaryOperator):
    name: ClassVar[str] = '-'


@dataclass(frozen=True, slots=True, init=False)
class Mul(BinaryOperator):
    name: ClassVar[str] = '*'


@dataclass(frozen=True, slots=True, init=False)
class MatMul(BinaryOperator):
    name: ClassVar[str] = '@'


@dataclass(frozen=True, slots=True, init=False)
class Div(BinaryOperator):
    name: ClassVar[str] = '/'


@dataclass(frozen=True, slots=True, init=False)
class FloorDiv(BinaryOperator):
    name: ClassVar[str] = '//'


@dataclass(frozen=True, slots=True, init=False)
class Mod(BinaryOperator):
    name: ClassVar[str] = '%'


@dataclass(frozen=True, slots=True, init=False)
class Pow(BinaryOperator):
    name: ClassVar[str] = '**'


@dataclass(frozen=True, slots=True)
class Cons(Operator):
    name: ClassVar[str] = '.'

    def __init__(self, head: Term, tail: Term):
        Operator.__init__(self, head, tail)

    @property
    def head(self) -> Term:
        return self.args[0]

    @property
    def tail(self) -> Term:
        return self.args[1]

    def __str__(self):
        acc: list[str] = []
        tail = self
        while isinstance(tail, Cons):
            acc.append(str(tail.head))
            tail = tail.tail
        if tail == EMPTY:
            return f'[{", ".join(acc)}]'
        else:
            return f'[{", ".join(acc)} | {tail}]'


@dataclass(frozen=True, slots=True)
class Empty(NonVariable):
    name: ClassVar[str] = '[]'

    @property
    def indicator(self) -> Indicator:
        return self.name, 0

    def __repr__(self):
        return '[]'

    def __str__(self):
        return '[]'


EMPTY = Empty()


@dataclass(frozen=True, slots=True, init=False)
class AllOf(Operator):
    name: ClassVar[str] = 'all_of'


@dataclass(frozen=True, slots=True, init=False)
class AnyOf(Operator):
    name: ClassVar[str] = 'any_of'


@dataclass(frozen=True, slots=True)
class Rule[T: Term | Callable[..., Term]](NonVariable):
    head: NonVariable
    body: T

    @property
    def indicator(self):
        return self.head.indicator


@dataclass(frozen=True, slots=True)
class HornetRule(Rule[Term]):
    pass


type VarCount = tuple[int, Iterator[int]]
_var_counter: Iterator[int] = count()


@with_state
def current_variable() -> StateOp[VarCount, Variable]:
    i, _ = yield get_state()
    return Variable(f'S${i}')


@with_state
def advance_variables() -> StateOp[VarCount, tuple[Variable, Variable]]:
    i, counter = yield get_state()
    j = next(counter)
    yield set_state(const((j, counter)))
    return Variable(f'S${i}'), Variable(f'S${j}')


@with_state
def dcg_expand_cons(term: Term) -> StateOp[VarCount, Term]:
    result_terms: list[Term] = []
    tail = term
    while True:
        match tail:
            case Cons(head=head, tail=tail):
                Sout, Sin = yield advance_variables()
                result_terms.append(Functor('equal', Sout, Cons(head, Sin)))
            case Empty():
                break
            case _:
                raise TypeError(f'Expected Cons or Empty, got {tail}')
    return AllOf(*result_terms)


@with_state
def walk_dcg_body(term: Term) -> StateOp[VarCount, Term]:
    match term:
        case Atom(name=name):
            Sout, Sin = yield advance_variables()
            return Functor(name, Sout, Sin)

        case Functor(name='inline', args=inlined):
            return AllOf(*inlined)

        case AllOf(args=goals):
            new_goals: list[Term] = []
            for goal in goals:
                new_goal = yield walk_dcg_body(goal)
                new_goals.append(new_goal)
            return AllOf(*new_goals)

        case AnyOf(args=goals):
            new_goals: list[Term] = []
            for goal in goals:
                new_goal = yield walk_dcg_body(goal)
                new_goals.append(new_goal)
            return AnyOf(*new_goals)

        case Functor(name=name, args=args):
            Sout, Sin = yield advance_variables()
            return Functor(name, *args, Sout, Sin)

        case Cons():
            return (yield dcg_expand_cons(term))

        case _:
            raise TypeError(f'Expected query term in DCG body, got: {term!r}')


@with_state
def _dcg_expand(term: NonVariable | HornetRule) -> StateOp[VarCount, Functor | Rule[Term]]:
    Sout = yield current_variable()
    match term:
        case Atom(name=name):
            return Functor(name, Sout, Sout)
        case Functor(name=name, args=args):
            return Functor(name, *args, Sout, Sout)
        case HornetRule(head=head, body=body):
            match head:
                case Atom(name=name):
                    body_expanded = yield walk_dcg_body(body)
                    Sin = yield current_variable()
                    head_expanded = Functor(name, Sout, Sin)
                    return HornetRule(head_expanded, body_expanded)
                case Functor(name=name, args=args):
                    body_expanded = yield walk_dcg_body(body)
                    Sin = yield current_variable()
                    head_expanded = Functor(name, *args, Sout, Sin)
                    return HornetRule(head_expanded, body_expanded)
                case _:
                    raise TypeError(f' {term!r}')
        case _:
            raise TypeError(f' {term!r}')


def DCG(term: Term) -> Functor | Rule[Term]:
    expanded_term, _ = _dcg_expand(term).run((next(_var_counter), _var_counter))
    return expanded_term


def DCGs(*terms: Term) -> Iterator[Functor | Rule[Term]]:
    for term in terms:
        yield DCG(term)


def fresh_name(canonical_name: str) -> str:
    return f'{canonical_name}!{next(_var_counter)}'


def fresh_variable(canonical_name: str = 'S') -> Variable:
    return Variable(fresh_name(canonical_name))


RANK: dict[type[Term], int] = {
    BitOr: 10,
    BitXor: 20,
    BitAnd: 30,
    LShift: 40,
    RShift: 40,
    Add: 50,
    Sub: 50,
    Mul: 60,
    MatMul: 60,
    Div: 60,
    FloorDiv: 60,
    Mod: 60,
    Invert: 70,
    UAdd: 70,
    USub: 70,
    Pow: 80,
}


def rank(term: Term) -> int:
    return RANK.get(type(term), 0)


def promote(obj: Any) -> Term | tuple[Term, ...]:
    match obj:
        case (
            Variable()
            | Wildcard()
            | Atom()
            | Empty()
            | str()
            | bytes()
            | int()
            | bool()
            | float()
            | complex()
            | Exception()
        ):
            return obj

        case Functor(name=name, args=args):
            return Functor(name, *(promote(arg) for arg in args))

        case Operator(args=args):
            return type(obj)(*(promote(arg) for arg in args))

        case tuple():
            return tuple(promote(each) for each in obj)

        case Cons(head=BitOr(left=left, right=right)):
            return Cons(promote(left), promote(right))

        case []:
            return EMPTY

        case [BitOr(left=left, right=right), *tail]:
            assert not tail
            return Cons(promote(left), promote(right))

        case [head, *tail]:
            return Cons(promote(head), promote(list(tail)))

        case _:
            raise TypeError(str(type(obj)))  # type: ignore[arg-type]


Primitive = str, int, float, bool, complex, bytes, tuple
Atomic = Primitive, Atom, Empty
scan = re.compile(
    r"""
    (?P<dunder>__.*__)      |  # dunder names
    (?P<wildcard>_)         |  # anonymous variable
    (?P<atom>[a-z].*)       |  # starts with lowercase
    (?P<variable>[A-Z_].*)     # starts with uppercase or _
    """,
    re.VERBOSE,
).fullmatch


@cache
def symbol(name: str) -> Atom | Variable | Wildcard:
    """
    Convert a string into a Term according to Prolog conventions:
      - "_" becomes the anonymous variable
      - strings starting with uppercase or "_" become Variables
      - strings starting with lowercase become Atoms
    """
    if (m := scan(name)) is None:
        raise AttributeError(f'Invalid symbol name: {name}')
    match m.lastgroup:
        case 'wildcard':
            return WILDCARD
        case 'variable':
            return Variable(name)
        case 'atom':
            return Atom(name)
        case _:
            raise AttributeError(f'Invalid symbol name: {name}')
