# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from itertools import count
from typing import ClassVar, Iterator, Self, override

type Indicator = tuple[str, int | None]


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

    def normalize(self) -> Self:
        return self


@dataclass(frozen=True, slots=True)
class Structure(Term):
    args: tuple[Term, ...]

    def __init__(self, *args: Term):
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
    def normalize(self: Functor) -> Term:
        return type(self)(self.name, *(arg.normalize() for arg in self.args))


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
    def normalize(self) -> Term:
        return type(self)(self.operand.normalize())


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

    @override
    def normalize(self) -> Term:
        return type(self)(self.left.normalize(), self.right.normalize())


@dataclass(frozen=True, slots=True, init=False)
class AnonVariable(Term):
    name: ClassVar[str] = "_"

    def __eq__(self, _):
        return False

    def __deepcopy__(self, _):
        return self


@dataclass(frozen=True, slots=True, eq=False)
class Variable(Term):
    _counter: ClassVar[Iterator[int]] = count()
    name: str

    def __str__(self):
        return self.name

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __deepcopy__(self, memo):
        if self.name in memo:
            return memo[self.name]
        new_var = memo[self.name] = self.fresh(self.name)
        return new_var

    @classmethod
    def fresh(cls, name: str):
        return cls(f"{name}!{next(cls._counter)}")


@dataclass(frozen=True, slots=True)
class Atomic(Term):
    pass


@dataclass(frozen=True, slots=True)
class Constant[T](Atomic):
    value: T

    def __str__(self):
        return str(self.value)

    def __deepcopy__(self, _):
        return self


@dataclass(frozen=True, slots=True)
class Bytes(Constant[bytes]):
    pass


class Integer(Constant[int]):
    pass


@dataclass(frozen=True, slots=True)
class Bool(Constant[bool]):
    pass


@dataclass(frozen=True, slots=True)
class Float(Constant[float]):
    pass


@dataclass(frozen=True, slots=True)
class Complex(Constant[complex]):
    pass


@dataclass(frozen=True, slots=True)
class String(Constant[str]):
    def __str__(self):
        return f"'{self.value}'"


@dataclass(frozen=True, slots=True)
class Atom(Atomic):
    name: str

    def __str__(self):
        return self.name

    @property
    @cache
    @override
    def indicator(self) -> Indicator:
        return self.name, None


@dataclass(frozen=True, slots=True, init=False)
class Invert(UnaryOperator):
    name: ClassVar[str] = "~"


@dataclass(frozen=True, slots=True, init=False)
class UAdd(UnaryOperator):
    name: ClassVar[str] = "+"


@dataclass(frozen=True, slots=True, init=False)
class USub(UnaryOperator):
    name: ClassVar[str] = "-"


@dataclass(frozen=True, slots=True, init=False)
class LShift(BinaryOperator):
    name: ClassVar[str] = "<<"


@dataclass(frozen=True, slots=True, init=False)
class RShift(BinaryOperator):
    name: ClassVar[str] = ">>"


@dataclass(frozen=True, slots=True, init=False)
class BitOr(BinaryOperator):
    name: ClassVar[str] = "|"


@dataclass(frozen=True, slots=True, init=False)
class BitXor(BinaryOperator):
    name: ClassVar[str] = "^"


@dataclass(frozen=True, slots=True, init=False)
class BitAnd(BinaryOperator):
    name: ClassVar[str] = "&"


@dataclass(frozen=True, slots=True, init=False)
class Add(BinaryOperator):
    name: ClassVar[str] = "+"


@dataclass(frozen=True, slots=True, init=False)
class Sub(BinaryOperator):
    name: ClassVar[str] = "-"


@dataclass(frozen=True, slots=True, init=False)
class Mult(BinaryOperator):
    name: ClassVar[str] = "*"


@dataclass(frozen=True, slots=True, init=False)
class Div(BinaryOperator):
    name: ClassVar[str] = "/"


@dataclass(frozen=True, slots=True, init=False)
class FloorDiv(BinaryOperator):
    name: ClassVar[str] = "//"


@dataclass(frozen=True, slots=True, init=False)
class Mod(BinaryOperator):
    name: ClassVar[str] = "%"


@dataclass(frozen=True, slots=True, init=False)
class Pow(BinaryOperator):
    name: ClassVar[str] = "**"


@dataclass(frozen=True, slots=True)
class Empty(Term):
    name: ClassVar[str] = "[]"

    def __str__(self):
        return "[]"


EMPTY = Empty()


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
    def normalize(self) -> Term:
        match self.head.normalize(), self.tail.normalize():
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
