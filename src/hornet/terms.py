# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from itertools import count
from typing import Any, Callable, ClassVar, Iterator

from .states import StateGenerator, const, get_state, set_state, with_state

type Term[T: Term] = BaseTerm | Rule[T] | Primitive
type Indicator = tuple[str, int | None]


@dataclass(frozen=True, slots=True, init=False)
class BaseTerm(ABC):
    def when(self, *args: BaseTerm | list[Term]) -> Rule:
        raise TypeError(f"Only atoms or functors allowed, not {self}")

    def __neg__(self):
        return USub(promote(self))

    def __pos__(self):
        return UAdd(promote(self))

    def __invert__(self):
        return Invert(promote(self))

    def __add__(self, other):
        return Add(promote(self), promote(other))

    def __radd__(self, other):
        return Add(promote(other), promote(self))

    def __sub__(self, other):
        return Sub(promote(self), promote(other))

    def __rsub__(self, other):
        return Sub(promote(other), promote(self))

    def __mul__(self, other):
        return Mul(promote(self), promote(other))

    def __rmul__(self, other):
        return Sub(promote(other), promote(self))

    def __truediv__(self, other):
        return Div(promote(self), promote(other))

    def __rtruediv__(self, other):
        return Sub(promote(other), promote(self))

    def __floordiv__(self, other):
        return FloorDiv(promote(self), promote(other))

    def __rfloordiv__(self, other):
        return Sub(promote(other), promote(self))

    def __mod__(self, other):
        return Mod(promote(self), promote(other))

    def __rmod__(self, other):
        return Sub(promote(other), promote(self))

    def __pow__(self, other):
        return Pow(promote(self), promote(other))

    def __rpow__(self, other):
        return Sub(promote(other), promote(self))

    def __lshift__(self, other):
        return LShift(promote(self), promote(other))

    def __rlshift__(self, other):
        return Sub(promote(other), promote(self))

    def __rshift__(self, other):
        return RShift(promote(self), promote(other))

    def __rrshift__(self, other):
        return Sub(promote(other), promote(self))

    def __and__(self, other):
        return BitAnd(promote(self), promote(other))

    def __rand__(self, other):
        return Sub(promote(other), promote(self))

    def __xor__(self, other):
        return BitXor(promote(self), promote(other))

    def __rxor__(self, other):
        return Sub(promote(other), promote(self))

    def __or__(self, other):
        return BitOr(promote(self), promote(other))

    def __ror__(self, other):
        return Sub(promote(other), promote(self))

    def __call__(self, *args) -> Functor:
        raise TypeError(f"Atom required, not {self}")


@dataclass(frozen=True, slots=True)
class Symbolic(BaseTerm):
    def when(self, *args: BaseTerm | list[Term]) -> Rule:
        body = Conjunction(*(promote(arg) for arg in args))
        return HornetRule(head=self, body=body)


@dataclass(frozen=True, slots=True)
class Atom(Symbolic):
    name: str
    args: tuple[Term, ...] = ()

    @property
    def indicator(self) -> Indicator:
        return self.name, 0

    def __str__(self):
        return self.name

    def __call__(self, *args) -> Functor:
        return Functor(self.name, *(promote(arg) for arg in args))


@dataclass(frozen=True, slots=True)
class Structure(Symbolic):
    args: tuple[Term, ...] = ()

    @property
    def indicator(self) -> Indicator:
        return self.name, len(self.args)

    def __init__(self, *args: Term):
        object.__setattr__(self, "args", args)


@dataclass(frozen=True, slots=True, init=False)
class Functor(Structure):
    name: str

    def __init__(self, name: str, *args: Term):
        object.__setattr__(self, "name", name)
        Structure.__init__(self, *args)

    def __str__(self):
        return f"{self.name}({', '.join(str(arg) for arg in self.args)})"


@dataclass(frozen=True, slots=True, init=False)
class UnaryOperator(Structure):
    name = ""

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
    name = ""

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


@dataclass(frozen=True, slots=True)
class Variable(BaseTerm):
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True, slots=True, init=False)
class Connective(BaseTerm):
    name: ClassVar[str]
    args: tuple[Term, ...]

    def __init__(self, *args: Term):
        object.__setattr__(self, "args", args)

    def __str__(self):
        return ", ".join(map(str, self.args))


@dataclass(frozen=True, slots=True, init=False)
class Conjunction(Connective):
    name: ClassVar[str] = ","


@dataclass(frozen=True, slots=True, init=False)
class Disjunction(Connective):
    name: ClassVar[str] = ";"


# @dataclass(frozen=True, slots=True)
# class Negation(BaseTerm):
#     name = "~"
#     goal: Term
#


EMPTY = Empty()


MatchTerm = Atom | Functor | UnaryOperator | BinaryOperator | Symbolic
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


type VarCount = tuple[int, Iterator[int]]
_var_counter: Iterator[int] = count()


def DCG(term: Term) -> Functor | Rule:
    @with_state
    def current_variable() -> StateGenerator[VarCount, Variable]:
        i, _ = yield get_state()
        return Variable(f"S${i}")

    @with_state
    def advance_variables() -> StateGenerator[VarCount, tuple[Variable, Variable]]:
        i, counter = yield get_state()
        j = next(counter)
        yield set_state(const((j, counter)))
        return Variable(f"S${i}"), Variable(f"S${j}")

    @with_state
    def dcg_expand_cons(term: Term) -> StateGenerator[VarCount, tuple[Term, Variable]]:
        result_terms = []

        while True:
            match term:
                case Cons(head=head, tail=tail):
                    Sout, Sin = yield advance_variables()
                    result_terms.append(Functor("equal", Sout, Cons(head, Sin)))
                    term = tail
                case Empty():
                    break

        Sin = yield current_variable()
        return Conjunction(*result_terms), Sin

    @with_state
    def walk_body(
        term: Term,
    ) -> StateGenerator[VarCount, Term]:
        match term:
            case Atom(name=name):
                Sout, Sin = yield advance_variables()
                return Functor(name, Sout, Sin), Sin

            case Functor(name="inline", args=inlined):
                Sin = yield current_variable()
                return Conjunction(*tuple(inlined)), Sin

            case Functor(name=name, args=args):
                Sout, Sin = yield advance_variables()
                return Functor(name, *args, Sout, Sin), Sin

            case Cons():
                return (yield dcg_expand_cons(term))

            case Conjunction(args=goals):
                new_goals = []
                for goal in goals:
                    new_goal, _ = yield walk_body(goal)
                    new_goals.append(new_goal)
                Sin = yield current_variable()
                return Conjunction(*new_goals), Sin

            case Disjunction(body=goals):
                new_goals = []
                for goal in goals:
                    new_goal, _ = yield walk_body(goal)
                    new_goals.append(new_goal)
                Sin = yield current_variable()
                return Disjunction(*new_goals), Sin

        raise TypeError(f"Expected query term in DCG body, got: {term!r}")

    @with_state
    def _dcg_expand(
        term: Symbolic | HornetRule,
    ) -> StateGenerator[VarCount, Functor | Rule]:
        Sout = yield current_variable()
        match term:
            case Atom(name=name, args=args) | Functor(name=name, args=args):
                return Functor(name, *args, Sout, Sout)
            case HornetRule(head=head, body=body):
                match head:
                    case Atom(name=name, args=args):
                        body_expanded, Sin = yield walk_body(body)
                        head_expanded = Functor(name, *args, Sout, Sin)
                        return HornetRule(head=head_expanded, body=body_expanded)
                    case Functor(name=name, args=args):
                        body_expanded, Sin = yield walk_body(body)
                        head_expanded = Functor(name, *args, Sout, Sin)
                        return HornetRule(head=head_expanded, body=body_expanded)
        raise TypeError(f" {term!r}")

    expanded_term, _ = _dcg_expand(term).run((next(_var_counter), _var_counter))
    return expanded_term


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


def promote(obj: Any) -> Term | tuple:
    """
    Convert a Python object to a Term.
    """
    match obj:
        case (
            Variable()
            | Atom()
            | Empty()
            | str()
            | bytes()
            | int()
            | bool()
            | float()
            | complex()
        ):
            return obj
        case Functor(name=name, args=args):
            return Functor(name, *(promote(arg) for arg in args))
        case Structure(args):
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
            raise TypeError(f"{type(obj)}")


Primitive = str | int | float | bool | complex | bytes | tuple
Atomic = Primitive | Atom
unit = Atom

type MFunc = Callable[[Term], Term]
