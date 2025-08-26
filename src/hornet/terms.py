# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from operator import attrgetter, itemgetter
from typing import ClassVar, Self, override

from toolz import compose


def fixity(name: str | None, lbp: int, rbp: int):
    "Attach class-level lbp and rbp to a Term subclasses."

    def decorator[T: type[Term]](cls: T) -> T:
        if name and issubclass(cls, Structure):
            cls.name = name
        cls.lbp = lbp
        cls.rbp = rbp
        return cls

    return decorator


def operator_x():
    return fixity(None, 0, 0)


def operator_fy(rank, name):
    return fixity(name, 0, rank)


def operator_xfx(rank, name):
    return fixity(name, rank, rank)


def operator_xfy(rank, name):
    return fixity(name, rank - 1, rank)


def operator_yfx(rank, name):
    return fixity(name, rank, rank - 1)


first_arg = property(compose(itemgetter(0), attrgetter("args")))
second_arg = property(compose(itemgetter(1), attrgetter("args")))


class Indicator:
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def arity(self) -> int | None: ...


@dataclass(frozen=True, slots=True)
class Term:
    lbp: ClassVar[int] = 0
    rbp: ClassVar[int] = 0

    @property  # pyright: ignore
    @override
    @dataclass(frozen=True, slots=True)
    class indicator(Indicator):
        term: Term

        @property
        def name(self) -> str:
            "The name property."
            return type(self.term).__name__

        @property
        def arity(self) -> int | None:
            "The arity property."
            return None

    def normalize(self, lbp: int, rbp: int) -> Self:
        return self


@operator_x()
@dataclass(frozen=True, slots=True)
class Variable(Term):
    name: str

    def __str__(self):
        return self.name


@operator_x()
@dataclass(frozen=True, slots=True)
class AnonVariable(Variable):
    def __init__(self):
        Variable.__init__(self, "_")

    def __eq__(self, _):
        return False


@dataclass(frozen=True, slots=True)
class Constant[T](Term):
    value: T

    def __str__(self):
        return str(self.value)


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


@dataclass(frozen=True, slots=True)
class Structure(Term):
    name: ClassVar[str]
    args: tuple[Term, ...]

    def __init__(self, *args: Term):
        object.__setattr__(
            self,
            "args",
            tuple(arg.normalize(arg.lbp, arg.rbp) for arg in args),
        )

    def __str__(self):
        return f"{self.name}({', '.join(str(arg) for arg in self.args)})"

    @property  # pyright: ignore
    @override
    @dataclass(frozen=True, slots=True)
    class indicator(Indicator):
        term: Structure

        @property
        @lru_cache
        def name(self) -> str:
            return self.term.name

        @property
        @lru_cache
        def arity(self) -> int | None:
            return len(self.term.args)


@dataclass(frozen=True, slots=True)
class UnaryOperator(Structure):
    arg = first_arg

    __init__ = Structure.__init__

    def __str__(self):
        return f"{self.name}{str(self.arg)}"


@operator_fy(70, "~")
@dataclass(frozen=True, slots=True)
class Invert(UnaryOperator):
    __init__ = UnaryOperator.__init__


@operator_fy(70, "+")
@dataclass(frozen=True, slots=True)
class UAdd(UnaryOperator):
    __init__ = UnaryOperator.__init__


@operator_fy(70, "-")
@dataclass(frozen=True, slots=True)
class USub(UnaryOperator):
    __init__ = UnaryOperator.__init__


@dataclass(frozen=True, slots=True)
class BinaryOperator(Structure):
    left = first_arg
    right = second_arg

    __init__ = Structure.__init__

    @override
    def normalize(self, lbp: int, rbp: int) -> Term:
        """
        Normalize a Term according to left/right binding powers so that the
        resulting tree reflects Prolog-style fixities.
        """
        # precedence parsing inspired by Pratt parsers
        left = self.left.normalize(lbp, self.lbp)
        right = self.right.normalize(self.rbp, rbp)
        # If the left child is a binary operator with *lower* rbp than our lbp,
        # rotate right: ((a ◁ b) ▷ c)  ==>  a ◁ (b ▷ c)
        if left.rbp == self.lbp and self.lbp == self.rbp:  # non-associative
            raise ValueError(
                f"Non-associative operator {type(self).__name__} used in chain"
            )
        if isinstance(left, BinaryOperator) and left.rbp < self.lbp:
            left_left, left_right = left.args
            return type(left)(left_left, type(self)(left_right, right))
        # otherwise keep as-is
        return type(self)(left, right)

    def __str__(self):
        return f"{str(self.left)} {self.name} {str(self.right)}"


@operator_x()
@dataclass(frozen=True, slots=True)
class Empty(Atom):
    def __init__(self):
        Atom.__init__(self, "[]")


EMPTY = Empty()


@operator_xfx(0, ".")
@dataclass(frozen=True, slots=True)
class Cons(BinaryOperator):
    head = first_arg
    tail = second_arg

    __init__ = Structure.__init__

    @override
    def normalize(self, lbp: int, rbp: int) -> Term:
        head = self.head.normalize(self.head.lbp, self.head.rbp)
        tail = self.tail.normalize(self.tail.lbp, self.tail.rbp)
        match head, tail:
            case BitOr((left, right)), Empty():
                return Cons(left, right)
            case _, BitOr((left, right)):
                return Cons(head, Cons(left, right))
            case _:
                return Cons(head, tail)

    def __str__(self):
        acc = []
        tail = self
        while isinstance(tail, Cons):
            acc.append(str(tail.head))
            tail = tail.tail
        if tail is EMPTY:
            return f"[{', '.join(acc)}]"
        else:
            return f"[{', '.join(acc)} | {tail}]"


@operator_xfx(5, "<<")
@dataclass(frozen=True, slots=True)
class LShift(BinaryOperator):
    head = first_arg
    body = second_arg

    __init__ = BinaryOperator.__init__


@operator_xfx(5, ">>")
@dataclass(frozen=True, slots=True)
class RShift(BinaryOperator):
    head = first_arg
    body = second_arg

    __init__ = BinaryOperator.__init__


@operator_xfy(10, "|")
@dataclass(frozen=True, slots=True)
class BitOr(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_xfy(20, "^")
@dataclass(frozen=True, slots=True)
class BitXor(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_xfy(30, "&")
@dataclass(frozen=True, slots=True)
class BitAnd(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_yfx(50, "+")
@dataclass(frozen=True, slots=True)
class Add(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_yfx(50, "-")
@dataclass(frozen=True, slots=True)
class Sub(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_yfx(60, "*")
@dataclass(frozen=True, slots=True)
class Mult(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_yfx(60, "/")
@dataclass(frozen=True, slots=True)
class Div(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_yfx(60, "//")
@dataclass(frozen=True, slots=True)
class FloorDiv(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_yfx(60, "%")
@dataclass(frozen=True, slots=True)
class Mod(BinaryOperator):
    __init__ = BinaryOperator.__init__


@operator_xfy(80, "**")
@dataclass(frozen=True, slots=True)
class Pow(BinaryOperator):
    __init__ = BinaryOperator.__init__


@dataclass(frozen=True, slots=True)
class Functor(Structure):
    name: str  # pyright: ignore

    def __init__(self, name: str, *args: Term):
        object.__setattr__(self, "name", name)
        Structure.__init__(self, *args)
