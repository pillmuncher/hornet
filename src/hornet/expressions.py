# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from functools import cache, partial, reduce
from typing import Any, Callable, ClassVar, Protocol, cast, override

from toolz.functoolz import compose, flip

from .terms import (
    EMPTY,
    Add,
    Atom,
    BitAnd,
    BitOr,
    BitXor,
    Bool,
    Bytes,
    Complex,
    Cons,
    Div,
    Float,
    FloorDiv,
    Functor,
    Indicator,
    Integer,
    Invert,
    LShift,
    Mod,
    Mult,
    Pow,
    RShift,
    String,
    Sub,
    Term,
    UAdd,
    USub,
)


class ExpressionLike[T: Term](Protocol):
    @property
    def term(self) -> T: ...


@dataclass(frozen=True, slots=True)
class BaseRuleTerm(Term):
    name: ClassVar[str]
    term: Term
    args: tuple[Term, ...]

    @property
    @cache
    @override
    def indicator(self) -> Indicator:
        return self.name, 1

    @override
    def normalize(self) -> Term:
        return type(self)(
            self.term.normalize(),
            tuple(arg.normalize() for arg in self.args),
        )


@dataclass(frozen=True, slots=True, init=False)
class RuleTerm(BaseRuleTerm):
    name: ClassVar[str] = "RuleTerm"


@dataclass(frozen=True, slots=True, init=False)
class DCGRuleTerm(BaseRuleTerm):
    name: ClassVar[str] = "DCGRuleTerm"
    pass


@dataclass(frozen=True, slots=True)
class Rule:
    term: Term


@dataclass(frozen=True, slots=True)
class DCG:
    expr: Expression[Atom | Functor]

    def when(self, *args):
        return Rule(
            term=DCGRuleTerm(
                term=self.expr.term,
                args=tuple(promote(arg) for arg in args),
            )
        )


@dataclass(frozen=True, slots=True)
class Expression[T: Term]:
    """
    An Expression object is a monadic wrapper around a Term.
    """

    term: T

    def when(self, *args) -> Rule:
        assert isinstance(self.term, Atom | Functor)
        return Rule(
            term=RuleTerm(
                term=self.term,
                args=tuple(promote(arg) for arg in args),
            )
        )

    def __eq__(self, other):
        return isinstance(other, Expression) and self.term == other.term

    def __hash__(self) -> int:
        return hash((Expression, self.term))

    def __repr__(self):
        return repr(self.term)

    def __str__(self):
        return str(self.term)

    def __neg__(self):
        return Expression(USub(promote(self)))

    def __pos__(self):
        return Expression(UAdd(promote(self)))

    def __invert__(self):
        return Expression(Invert(promote(self)))

    def __add__(self, other):
        return Expression(Add(promote(self), promote(other)))

    __radd__ = flip(__add__)

    def __sub__(self, other):
        return Expression(Sub(promote(self), promote(other)))

    __rsub__ = flip(__sub__)

    def __mul__(self, other):
        return Expression(Mult(promote(self), promote(other)))

    __rmul__ = flip(__mul__)

    def __matmul__(self, other):
        return Expression(Mult(promote(self), promote(other)))

    __rmatmul__ = flip(__mul__)

    def __truediv__(self, other):
        return Expression(Div(promote(self), promote(other)))

    __rtruediv__ = flip(__truediv__)

    def __floordiv__(self, other):
        return Expression(FloorDiv(promote(self), promote(other)))

    __rfloordiv__ = flip(__floordiv__)

    def __mod__(self, other):
        return Expression(Mod(promote(self), promote(other)))

    __rmod__ = flip(__mod__)

    def __pow__(self, other):
        return Expression(Pow(promote(self), promote(other)))

    __rpow__ = flip(__pow__)

    def __lshift__(self, other):
        return Expression(LShift(promote(self), promote(other)))

    __rlshift__ = flip(__lshift__)

    def __rshift__(self, other):
        return Expression(RShift(promote(self), promote(other)))

    __rrshift__ = flip(__rshift__)

    def __and__(self, other):
        return Expression(BitAnd(promote(self), promote(other)))

    __rand__ = flip(__and__)

    def __xor__(self, other):
        return Expression(BitXor(promote(self), promote(other)))

    __rxor__ = flip(__xor__)

    def __or__(self, other):
        return Expression(BitOr(promote(self), promote(other)))

    __ror__ = flip(__or__)

    def __call__(self, *args):
        match promote(self):
            case Atom(name):
                return Expression((Functor(name, *(promote(arg) for arg in args))))
            case _:
                raise TypeError(f"Atom required, not {self}")


def promote(obj: Any) -> Term:
    """
    Convert a Python object to a Term.
    """
    match obj:
        case Term():
            return obj
        case Expression(node):
            return node
        case str():
            return String(obj)
        case bytes():
            return Bytes(obj)
        case int():
            return Integer(obj)
        case bool():
            return Bool(obj)
        case float():
            return Float(obj)
        case complex():
            return Complex(obj)
        case []:
            return EMPTY
        case [head, *tail]:
            return Cons(promote(head), promote(tail))
        case _:
            raise TypeError(f"{type(obj)}")


# In the Monad, unit is the same as Expression:
unit = Expression


type MFunc = Callable[[Term], Expression]


def bind(expr: Expression, mfunc: MFunc) -> Expression:
    """
    The function bind(expr, Term --> Expression) --> Expression is the monadic
    bind operator.  It takes an Expression object expr and a monadic function
    mfunc, passes the Term associated with expr to mfunc and returns whatever
    mfunc returns.
    """
    return mfunc(expr.term)


def lift(func: Callable[..., Term]) -> Callable[..., Expression]:
    """
    The function lift(... --> Term) --> (... --> Expression) "lifts" a normal
    function that returns an Term into a function that returns an Expression.
    It is typically used as a function decorator.
    """
    return compose(Expression, func)


def chain(*mfuncs: MFunc) -> MFunc:
    """
    Chain monadic functions of type Term --> Expression.
    """
    return cast(MFunc, partial(reduce, bind, tuple(reversed(mfuncs))))
