# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from functools import partial, reduce
from typing import Any, Callable

from toolz.functoolz import compose, flip

from . import terms
from .terms import Term


@dataclass(frozen=True, slots=True)
class Expression[T: Term]:
    """
    An Expression object wraps around a Term node and normalizes it automatically.
    """

    node: T

    def __post_init__(self):
        object.__setattr__(
            self,
            "node",
            self.node.normalize(self.node.lbp, self.node.rbp),
        )

    def __repr__(self):
        return repr(self.node)

    def __str__(self):
        return str(self.node)

    def __neg__(self):
        return Expression(terms.USub(self.node))

    def __pos__(self):
        return Expression(terms.UAdd(self.node))

    def __invert__(self):
        return Expression(terms.Invert(self.node))

    def __add__(self, other):
        rhs = other.node if isinstance(other, Expression) else other
        return Expression(terms.Add(self.node, rhs))

    __radd__ = flip(__add__)

    def __sub__(self, other):
        return Expression(terms.Sub(self.node, promote(other)))

    __rsub__ = flip(__sub__)

    def __mul__(self, other):
        return Expression(terms.Mult(self.node, promote(other)))

    __rmul__ = flip(__mul__)

    def __truediv__(self, other):
        return Expression(terms.Div(self.node, promote(other)))

    __rtruediv__ = flip(__truediv__)

    def __floordiv__(self, other):
        return Expression(terms.FloorDiv(self.node, promote(other)))

    __rfloordiv__ = flip(__floordiv__)

    def __mod__(self, other):
        return Expression(terms.Mod(self.node, promote(other)))

    __rmod__ = flip(__mod__)

    def __pow__(self, other):
        return Expression(terms.Pow(self.node, promote(other)))

    __rpow__ = flip(__pow__)

    def __lshift__(self, other):
        return Expression(terms.LShift(self.node, promote(other)))

    __rlshift__ = flip(__lshift__)

    def __rshift__(self, other):
        return Expression(terms.RShift(self.node, promote(other)))

    __rrshift__ = flip(__rshift__)

    def __and__(self, other):
        return Expression(terms.BitAnd(self.node, promote(other)))

    __rand__ = flip(__and__)

    def __xor__(self, other):
        return Expression(terms.BitXor(self.node, promote(other)))

    __rxor__ = flip(__xor__)

    def __or__(self, other):
        return Expression(terms.BitOr(self.node, promote(other)))

    __ror__ = flip(__or__)

    def __call__(self, *args):
        match self.node:
            case terms.Atom(name):
                return Expression(terms.Functor(name, *(promote(arg) for arg in args)))
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
        case _:
            raise TypeError(f"{type(obj)}")


# In the Monad, unit is the same as Expression:
unit = Expression


def bind(expr: Expression, mfunc: Callable[[Term], Expression]) -> Expression:
    """
    The function bind(expr, Term --> Expression) --> Expression is the monadic
    bind operator.  It takes an Expression object expr and a monadic function
    mfunc, passes the Term associated with expr to mfunc and returns whatever
    mfunc returns.
    """
    return mfunc(expr.node)


def lift(func: Callable[..., Term]) -> Callable[..., Expression]:
    """
    The function lift(... --> Term) --> (... --> Expression) "lifts" a normal
    function that returns an Term into a function that returns an Expression.
    It is typically used as a function decorator.
    """
    return compose(Expression, func)


def chain(*mfuncs: Callable[[Term], Expression]) -> Expression:
    """
    Compose monadic functions of type Term --> Expression.
    """
    return partial(reduce, bind, tuple(reversed(mfuncs)))  # pyright: ignore
