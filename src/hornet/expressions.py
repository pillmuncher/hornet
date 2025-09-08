# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from functools import partial, reduce
from typing import Any, Callable, cast

from toolz.functoolz import compose, flip

from . import terms
from .terms import Term


def normalize(term: Term) -> Term:
    return term.normalize(term.lbp, term.rbp)


@dataclass(frozen=True, slots=True)
class Expression[T: Term]:
    """
    An Expression object is a monadic wrapper around a Term.
    """

    term: T

    def __eq__(self, other):
        return isinstance(other, Expression) and self.term == other.term

    def __hash__(self) -> int:
        return hash((Expression, self.term))

    def __repr__(self):
        return repr(self.term)

    def __str__(self):
        return str(self.term)

    def __neg__(self):
        return Expression(normalize(terms.USub(promote(self))))

    def __pos__(self):
        return Expression(normalize(terms.UAdd(promote(self))))

    def __invert__(self):
        return Expression(normalize(terms.Invert(promote(self))))

    def __add__(self, other):
        rhs = other.term if isinstance(other, Expression) else other
        return Expression(normalize(terms.Add(promote(self), rhs)))

    __radd__ = flip(__add__)

    def __sub__(self, other):
        return Expression(normalize(terms.Sub(promote(self), promote(other))))

    __rsub__ = flip(__sub__)

    def __mul__(self, other):
        return Expression(normalize(terms.Mult(promote(self), promote(other))))

    __rmul__ = flip(__mul__)

    def __truediv__(self, other):
        return Expression(normalize(terms.Div(promote(self), promote(other))))

    __rtruediv__ = flip(__truediv__)

    def __floordiv__(self, other):
        return Expression(normalize(terms.FloorDiv(promote(self), promote(other))))

    __rfloordiv__ = flip(__floordiv__)

    def __mod__(self, other):
        return Expression(normalize(terms.Mod(promote(self), promote(other))))

    __rmod__ = flip(__mod__)

    def __pow__(self, other):
        return Expression(normalize(terms.Pow(promote(self), promote(other))))

    __rpow__ = flip(__pow__)

    def __lshift__(self, other):
        return Expression(normalize(terms.LShift(promote(self), promote(other))))

    __rlshift__ = flip(__lshift__)

    def __rshift__(self, other):
        return Expression(normalize(terms.RShift(promote(self), promote(other))))

    __rrshift__ = flip(__rshift__)

    def __and__(self, other):
        return Expression(normalize(terms.BitAnd(promote(self), promote(other))))

    __rand__ = flip(__and__)

    def __xor__(self, other):
        return Expression(normalize(terms.BitXor(promote(self), promote(other))))

    __rxor__ = flip(__xor__)

    def __or__(self, other):
        return Expression(normalize(terms.BitOr(promote(self), promote(other))))

    __ror__ = flip(__or__)

    def __call__(self, *args):
        match promote(self):
            case terms.Atom(name):
                return Expression(
                    normalize(terms.Functor(name, *(promote(arg) for arg in args)))
                )
            case _:
                raise TypeError(f"Atom required, not {self}")


def promote(obj: Any) -> Term:
    """
    Convert a Python object to a Term.
    """
    match obj:
        case terms.Term():
            return obj
        case Expression(node):
            return node
        case str():
            return terms.String(obj)
        case bytes():
            return terms.Bytes(obj)
        case int():
            return terms.Integer(obj)
        case bool():
            return terms.Bool(obj)
        case float():
            return terms.Float(obj)
        case complex():
            return terms.Complex(obj)
        case []:
            return terms.EMPTY
        case [head, *tail]:
            return terms.Cons(promote(head), promote(tail))
        case set() if len(obj) == 1:
            return terms.Inline(promote(obj.pop()))
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
