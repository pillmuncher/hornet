# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from itertools import count
from typing import ClassVar, Iterator

type Term[T: Term] = BaseTerm | Rule[T] | Primitive
type Indicator = tuple[str, int | None]


@property
def atomic_indicator(self) -> Indicator:
    return self.name, 0


@property
def compound_indicator(self) -> Indicator:
    return self.name, len(self.args)


@dataclass(frozen=True, slots=True, init=False)
class BaseTerm(ABC):
    pass


@dataclass(frozen=True, slots=True, init=False)
class Wildcard(BaseTerm):
    name: ClassVar[str] = "_"

    def __str__(self):
        return "_"


WILDCARD = Wildcard()


@dataclass(frozen=True, slots=True)
class Variable(BaseTerm):
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True, slots=True)
class Atom(BaseTerm):
    name: str
    args: tuple[Term, ...] = ()
    indicator = atomic_indicator

    def __str__(self):
        return self.name

    def __deepcopy__(self, memo):
        if id(self) in memo:
            return memo[id(self)]
        memo[id(self)] = self  # record first
        return self


@dataclass(frozen=True, slots=True)
class Structure(BaseTerm):
    args: tuple[Term, ...]
    indicator = compound_indicator

    def __init__(self, *args: Term):
        object.__setattr__(self, "args", args)


@dataclass(frozen=True, slots=True, init=False)
class Functor(Structure):
    name: str

    def __init__(self, name: str, *args: Term):
        object.__setattr__(self, "name", name)
        # object.__setattr__(self, "args", args)
        Structure.__init__(self, *args)

    def __str__(self):
        return f"{self.name}({', '.join(str(arg) for arg in self.args)})"


@dataclass(frozen=True, slots=True, init=False)
class UnaryOperator(Structure):
    name: ClassVar[str] = "_"

    def __init__(self, operand):
        Structure.__init__(self, operand)

    @property
    def operand(self):
        return self.args[0]

    def __str__(self):
        (operand,) = self.args
        if not isinstance(operand, (UnaryOperator, BinaryOperator)):
            return f"{self.name}{str(operand)}"
        elif rank(operand) < rank(self):
            return f"{self.name}{str(operand)}"
        else:
            return f"{self.name}({str(self.operand)})"


@dataclass(frozen=True, slots=True, init=False)
class BinaryOperator(Structure):
    name: ClassVar[str] = "_"

    def __init__(self, left, right):
        Structure.__init__(self, left, right)

    @property
    def left(self):
        return self.args[0]

    @property
    def right(self):
        return self.args[1]

    def __str__(self):
        left, right = self.args
        # left operand
        if isinstance(left, BinaryOperator) and rank(left) < rank(self):
            left_str = f"({left})"
        else:
            left_str = str(left)

        # right operand
        if isinstance(right, BinaryOperator) and rank(right) < rank(self):
            right_str = f"({right})"
        else:
            right_str = str(right)

        return f"{left_str} {self.name} {right_str}"


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
class Mul(BinaryOperator):
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


@dataclass(frozen=True, slots=True, init=False)
class Connective(BaseTerm):
    name: ClassVar[str]
    body: tuple[Term, ...]

    def __init__(self, *body: Term):
        object.__setattr__(self, "body", body)

    def __str__(self):
        return ", ".join(map(str, self.body))


@dataclass(frozen=True, slots=True, init=False)
class Conjunction(Connective):
    name: ClassVar[str] = ","


@dataclass(frozen=True, slots=True, init=False)
class Disjunction(Connective):
    name: ClassVar[str] = ";"


@dataclass(frozen=True, slots=True)
class Negation(BaseTerm):
    name: ClassVar[str] = "~"
    goal: Term


@dataclass(frozen=True, slots=True)
class Cons(BinaryOperator):
    name: ClassVar[str] = "."

    def __init__(self, head: Term, tail: Term):
        BinaryOperator.__init__(self, head, tail)

    @property
    def head(self) -> Term:
        return self.args[0]

    @property
    def tail(self) -> Term:
        return self.args[1]

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


@dataclass(frozen=True, slots=True)
class Empty(BaseTerm):
    name: ClassVar[str] = "[]"


EMPTY = Empty()


MatchTerm = Atom | Functor | UnaryOperator | BinaryOperator
QueryTerm = Atom | Functor | UnaryOperator | BinaryOperator | Conjunction | Disjunction


@dataclass(frozen=True, slots=True)
class Rule[T](BaseTerm):
    head: MatchTerm
    body: T

    @property
    def indicator(self):
        return self.head.indicator


@dataclass(frozen=True, slots=True)
class HornetRule(Rule[QueryTerm]):
    pass


_var_counter: Iterator[int] = count()


def fresh_name(canonical_name: str) -> str:
    return f"{canonical_name}!{next(_var_counter)}"


def fresh_variable(canonical_name: str = "S") -> Variable:
    return Variable(fresh_name(canonical_name))


RANK: dict[type[UnaryOperator | BinaryOperator], int] = {
    BitOr: 10,
    BitXor: 20,
    BitAnd: 30,
    LShift: 40,
    RShift: 40,
    Add: 50,
    Sub: 50,
    Mul: 60,
    Div: 60,
    FloorDiv: 60,
    Mod: 60,
    Invert: 70,
    UAdd: 70,
    USub: 70,
    Pow: 80,
    Cons: 0,
}


def rank(term: UnaryOperator | BinaryOperator) -> int:
    return RANK.get(type(term), 0)


Primitive = str | int | float | bool | complex | bytes | tuple
Atomic = Primitive | Atom
