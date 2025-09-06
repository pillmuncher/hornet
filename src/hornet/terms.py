# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from itertools import count
from typing import ClassVar, Iterator, Self, override

type Indicator = tuple[str, int | None]


def _fixity(lbp: int, rbp: int):
    "Attach class-level lbp and rbp to a Term subclasses."

    def decorator[T: type[Term]](cls: T) -> T:
        cls.lbp = lbp
        cls.rbp = rbp
        return cls

    return decorator


def operator_x():
    return _fixity(0, 0)


def operator_fy(rank):
    return _fixity(rank, 0)


def operator_xfx(rank):
    return _fixity(rank, rank)


def operator_xfy(rank):
    return _fixity(rank - 1, rank)


def operator_yfx(rank):
    return _fixity(rank, rank - 1)


@property
@cache
def _first_arg(self: Structure):
    return self.args[0]


@property
@cache
def _second_arg(self: Structure):
    return self.args[1]


@dataclass(frozen=True, slots=True)
class Term:
    lbp: ClassVar[int] = 0
    rbp: ClassVar[int] = 0

    @property
    @cache
    def indicator(self) -> Indicator:
        return type(self).__name__, None

    def normalize(self, lbp: int, rbp: int) -> Self:
        return self


@dataclass(frozen=True, slots=True)
class Structure(Term):
    args: tuple[Term, ...]

    def __init__(self, *args):
        object.__setattr__(self, "args", args)


@dataclass(frozen=True, slots=True)
class Functor(Structure):
    name: str

    def __init__(self, name: str, *args: Term):
        object.__setattr__(self, "name", name)
        Structure.__init__(self, *args)

    def __str__(self):
        return f"{self.name}({', '.join(str(arg) for arg in self.args)})"

    @property
    @cache
    @override
    def indicator(self) -> Indicator:
        return self.name, len(self.args)

    @override
    def normalize(self: Functor, lbp: int, rbp: int) -> Term:
        return type(self)(self.name, *(arg.normalize(0, 0) for arg in self.args))


@dataclass(frozen=True, slots=True)
class UnaryOperator(Structure):
    name: ClassVar[str]
    operand = _first_arg

    def __init__(self, operand: Term):
        Structure.__init__(self, operand)

    def __str__(self):
        return f"{self.name}{str(self.operand)}"

    @property
    @cache
    @override
    def indicator(self) -> Indicator:
        return self.name, 1

    @override
    def normalize(self, lbp: int, rbp: int) -> Term:
        return type(self)(self.operand.normalize(0, 0))


@dataclass(frozen=True, slots=True)
class BinaryOperator(Structure):
    name: ClassVar[str]
    left = _first_arg
    right = _second_arg

    def __init__(self, left: Term, right: Term):
        Structure.__init__(self, left, right)

    def __str__(self):
        return f"{str(self.left)} {self.name} {str(self.right)}"

    @property
    @cache
    @override
    def indicator(self) -> Indicator:
        return self.name, 2

    # precedence-based operator reordering inspired by Pratt parsers
    @override
    def normalize(self, lbp: int, rbp: int) -> Term:
        """
        Normalize a Term according to left/right binding powers so that the
        resulting tree reflects Prolog-style fixities.
        """
        # first descend:
        left = self.left.normalize(lbp, self.lbp)
        right = self.right.normalize(self.rbp, rbp)
        # assure we're not non-associative:
        if left.rbp == self.lbp and self.lbp == self.rbp:
            raise ValueError(
                f"Non-associative operator {type(self).__name__} used in chain"
            )
        match left:
            # If the left child is a binary operator with *lower* rbp than our lbp,
            # rotate right: ((a ◁ b) ▷ c)  ==>  a ◁ (b ▷ c)
            case BinaryOperator() if left.rbp < self.lbp:
                left_left, left_right = left.args
                return type(left)(left_left, type(self)(left_right, right))
            # otherwise keep as-is
            case _:
                return type(self)(left, right)


@operator_x()
@dataclass(frozen=True, slots=True, init=False)
class AnonVariable(Term):
    name: ClassVar[str] = "_"

    def __eq__(self, _):
        return False

    def __deepcopy__(self, memo):
        return self


@operator_x()
@dataclass(frozen=True, slots=True, eq=False)
class Variable(Term):
    name: str
    _counter: ClassVar[Iterator[int]] = count()

    def __str__(self):
        return self.name

    __eq__ = object.__eq__  # pyright: ignore
    __hash__ = object.__hash__

    def __deepcopy__(self, memo):
        if self.name in memo:
            return memo[self.name]
        new_var = memo[self.name] = Variable(f"{self.name}!{next(Variable._counter)}")
        return new_var

    def normalize(self, lbp: int, rbp: int) -> Self:
        return self


@dataclass(frozen=True, slots=True)
class Constant[T](Term):
    value: T

    def __str__(self):
        return str(self.value)

    def __deepcopy__(self, memo):
        return self

    def normalize(self, lbp: int, rbp: int) -> Self:
        return self


@operator_x()
@dataclass(frozen=True, slots=True)
class Bytes(Constant[bytes]):
    pass


@operator_x()
@dataclass(frozen=True, slots=True)
class Integer(Constant[int]):
    pass


@operator_x()
@dataclass(frozen=True, slots=True)
class Bool(Constant[bool]):
    pass


@operator_x()
@dataclass(frozen=True, slots=True)
class Float(Constant[float]):
    pass


@operator_x()
@dataclass(frozen=True, slots=True)
class Complex(Constant[complex]):
    pass


@operator_x()
@dataclass(frozen=True, slots=True)
class String(Constant[str]):
    def __str__(self):
        return f"'{self.value}'"


@dataclass(frozen=True, slots=True)
@operator_x()
class Atom(Term):
    name: str

    def __str__(self):
        return self.name


@operator_fy(70)
@dataclass(frozen=True, slots=True, init=False)
class Invert(UnaryOperator):
    name: ClassVar[str] = "~"


@operator_fy(70)
@dataclass(frozen=True, slots=True, init=False)
class UAdd(UnaryOperator):
    name: ClassVar[str] = "+"


@operator_fy(70)
@dataclass(frozen=True, slots=True, init=False)
class USub(UnaryOperator):
    name: ClassVar[str] = "-"


@operator_xfx(5)
@dataclass(frozen=True, slots=True, init=False)
class LShift(BinaryOperator):
    name: ClassVar[str] = "<<"
    head = _first_arg
    body = _second_arg


@operator_xfx(5)
@dataclass(frozen=True, slots=True, init=False)
class RShift(BinaryOperator):
    name: ClassVar[str] = ">>"
    head = _first_arg
    body = _second_arg


@operator_xfy(10)
@dataclass(frozen=True, slots=True, init=False)
class BitOr(BinaryOperator):
    name: ClassVar[str] = "|"


@operator_xfy(20)
@dataclass(frozen=True, slots=True, init=False)
class BitXor(BinaryOperator):
    name: ClassVar[str] = "^"


@operator_xfy(30)
@dataclass(frozen=True, slots=True, init=False)
class BitAnd(BinaryOperator):
    name: ClassVar[str] = "&"


@operator_yfx(50)
@dataclass(frozen=True, slots=True, init=False)
class Add(BinaryOperator):
    name: ClassVar[str] = "+"


@operator_yfx(50)
@dataclass(frozen=True, slots=True, init=False)
class Sub(BinaryOperator):
    name: ClassVar[str] = "-"


@operator_yfx(60)
@dataclass(frozen=True, slots=True, init=False)
class Mult(BinaryOperator):
    name: ClassVar[str] = "*"


@operator_yfx(60)
@dataclass(frozen=True, slots=True, init=False)
class Div(BinaryOperator):
    name: ClassVar[str] = "/"


@operator_yfx(60)
@dataclass(frozen=True, slots=True, init=False)
class FloorDiv(BinaryOperator):
    name: ClassVar[str] = "//"


@operator_yfx(60)
@dataclass(frozen=True, slots=True, init=False)
class Mod(BinaryOperator):
    name: ClassVar[str] = "%"


@operator_xfy(80)
@dataclass(frozen=True, slots=True, init=False)
class Pow(BinaryOperator):
    name: ClassVar[str] = "**"


@operator_x()
@dataclass(frozen=True, slots=True)
class Empty(Term):
    name: ClassVar[str] = "[]"

    def __str__(self):
        return "[]"


EMPTY = Empty()


@operator_xfx(0)
@dataclass(frozen=True, slots=True)
class Cons(BinaryOperator):
    name: ClassVar[str] = "."
    head = _first_arg
    tail = _second_arg

    def __init__(self, head: Term, tail: Term):
        BinaryOperator.__init__(self, head, tail)

    def __str__(self):
        acc = []
        tail = self
        while isinstance(tail, Cons):
            acc.append(str(tail.head))
            tail = tail.tail
        if tail == EMPTY:
            return f"[{', '.join(acc)}]"
        else:
            return f"[{', '.join(acc)} | {tail}]"

    @override
    def normalize(self, lbp: int, rbp: int) -> Term:
        match self.head.normalize(0, 0), self.tail.normalize(0, 0):
            case BitOr(left=BitOr(), right=_), _:
                raise SyntaxError("Invalid list head in `[Head|Tail]`")

            case BitOr(left=left, right=right), Empty():
                return Cons(head=left, tail=right)

            case BitOr(), _:
                raise SyntaxError("Invalid list head in `[Head|Tail]`")

            case head, BitOr(head=left, tail=right):
                return Cons(head=head, tail=Cons(head=left, tail=right))

            case head, tail:
                return Cons(head=head, tail=tail)
