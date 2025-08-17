# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

import ast
import functools
import numbers
from typing import Callable

from astor import code_gen as codegen
from toolz.functoolz import flip, identity

from .util import compose, foldl, qualname, rpartial

__all__ = [
    # monad class:
    "Expression",
    # monadic functions:
    "unit",
    "bind",
    "mlift",
    "mcompose",
    # helper functions:
    "promote",
    "astify",
    # Expression factory functions:
    "Name",
    "Tuple",
    "List",
    "Set",
    "Wrapper",
    # Expression factory operators:
    "Subscript",
    "Call",
    "USub",
    "UAdd",
    "Invert",
    "Add",
    "Sub",
    "Mult",
    "Div",
    "FloorDiv",
    "Mod",
    "Pow",
    "LShift",
    "RShift",
    "BitAnd",
    "BitXor",
    "BitOr",
    # AST node instance test functions:
    "is_binop",
    "is_lshift",
    "is_rshift",
    "is_bitand",
    "is_bitor",
    "is_name",
    "is_str",
    "is_call",
    "is_list",
    "is_set",
    "is_tuple",
    "is_astwrapper",
    "is_operator",
]


class Expression:
    """
    An Expression object wraps around an AST node.
    """

    # See also .test.test_expresion.test_monad_laws()
    __slots__ = "node"

    def __init__(self, node):
        "Initialize an Expression object with an AST node."
        self.node = node

    def __repr__(self):
        return ast.dump(self.node)

    def __str__(self):
        return codegen.to_source(self.node)

    def __getitem__(self, subscript):
        return Expression(
            ast.Subscript(
                value=astify(self),
                slice=ast.Slice(lower=astify(subscript)),
            )
        )

    def __call__(self, *args):
        return Expression(
            ast.Call(
                func=astify(self),
                args=[astify(each) for each in args],
                keywords=[],
            )
        )

    def __neg__(self):
        return Expression(ast.UnaryOp(ast.USub(), astify(self)))

    def __pos__(self):
        return Expression(ast.UnaryOp(ast.UAdd(), astify(self)))

    def __invert__(self):
        return Expression(ast.UnaryOp(ast.Invert(), astify(self)))

    def __add__(self, other):
        return Expression(ast.BinOp(astify(self), ast.Add(), astify(other)))

    __radd__ = flip(__add__)

    def __sub__(self, other):
        return Expression(ast.BinOp(astify(self), ast.Sub(), astify(other)))

    __rsub__ = flip(__sub__)

    def __mul__(self, other):
        return Expression(ast.BinOp(astify(self), ast.Mult(), astify(other)))

    __rmul__ = flip(__mul__)

    def __truediv__(self, other):
        return Expression(ast.BinOp(astify(self), ast.Div(), astify(other)))

    __rtruediv__ = flip(__truediv__)

    def __floordiv__(self, other):
        return Expression(ast.BinOp(astify(self), ast.FloorDiv(), astify(other)))

    __rfloordiv__ = flip(__floordiv__)

    def __mod__(self, other):
        return Expression(ast.BinOp(astify(self), ast.Mod(), astify(other)))

    __rmod__ = flip(__mod__)

    def __pow__(self, other):
        return Expression(ast.BinOp(astify(self), ast.Pow(), astify(other)))

    __rpow__ = flip(__pow__)

    def __lshift__(self, other):
        return Expression(ast.BinOp(astify(self), ast.LShift(), astify(other)))

    __rlshift__ = flip(__lshift__)

    def __rshift__(self, other):
        return Expression(ast.BinOp(astify(self), ast.RShift(), astify(other)))

    __rrshift__ = flip(__rshift__)

    def __and__(self, other):
        return Expression(ast.BinOp(astify(self), ast.BitAnd(), astify(other)))

    __rand__ = flip(__and__)

    def __xor__(self, other):
        return Expression(ast.BinOp(astify(self), ast.BitXor(), astify(other)))

    __rxor__ = flip(__xor__)

    def __or__(self, other):
        return Expression(ast.BinOp(astify(self), ast.BitOr(), astify(other)))

    __ror__ = flip(__or__)


# In the Monad, unit is the same as Expression:
unit = Expression


def bind(expr: Expression, mfunc: Callable[[ast.AST], Expression]) -> Expression:
    """
    The function bind(expr, AST --> Expression) --> Expression is the monadic
    bind operator.  It takes an Expression object expr and a monadic function
    mfunc, passes the AST associated with expr to mfunc and returns whatever
    mfunc returns.
    """
    return mfunc(expr.node)


def mlift(func: Callable[..., ast.AST]) -> Callable[..., Expression]:
    """
    The function mlift(... --> AST) --> (... --> unit) "lifts" a normal
    function that returns an AST into a function that returns an Expression.
    It is mostly used as a function decorator.
    """
    return compose(Expression, func)


def mcompose(*mfuncs):
    """
    Make monadic functions AST --> Expression composable.
    """
    return functools.partial(foldl, bind, tuple(reversed(mfuncs)))


# Here come the Expression factory functions.
#
# The arguments they take are converted to AST objects if necessary. They
# return an AST node that gets wrapped in an Expression object by the mlift
# decorator.
# Their names don't conform to PEP-8 because they reflect the AST node types
# they represent.


@mlift
def Name(name, **kwargs):
    return ast.Name(id=name, **kwargs)


@mlift
def Constant(value):
    return ast.Constant(value=value)


@mlift
def Tuple(tuple_):
    return ast.Tuple(elts=[astify(each) for each in tuple_])


@mlift
def List(list_):
    return ast.List(elts=[astify(each) for each in list_])


@mlift
def Set(set_):
    return ast.Set(elts=[astify(each) for each in set_])


# Although the following functions do not represent AST node types, they are
# used in the same way and should follow the same conventions as the ones
# above.


class AstWrapper[T](ast.AST):
    def __init__(self, wrapped: T):
        self.wrapped: T = wrapped


@mlift
def Wrapper(wrapped):
    return AstWrapper(wrapped=wrapped)


Add = Expression.__add__
BitAnd = Expression.__and__
BitOr = Expression.__or__
BitXor = Expression.__xor__
Call = Expression.__call__
Div = Expression.__truediv__
FloorDiv = Expression.__floordiv__
Invert = Expression.__invert__
LShift = Expression.__lshift__
Mod = Expression.__mod__
Mult = Expression.__mul__
Pow = Expression.__pow__
RShift = Expression.__rshift__
Sub = Expression.__sub__
Subscript = Expression.__getitem__
UAdd = Expression.__pos__
USub = Expression.__neg__


# Any Python object 'obj' will be turned into an Expression object with its
# AST created if necessary:
@functools.singledispatch
def promote(obj) -> Expression:
    return Wrapper(obj)


promote.register(Expression)(identity)
promote.register(numbers.Number)(Constant)
promote.register(str)(Constant)
promote.register(tuple)(Tuple)
promote.register(list)(List)
promote.register(set)(Set)


# Given any Python object 'obj', return its AST (and create it if necessary):
def astify(obj):
    return promote(obj).node


def is_binop(node, op):
    return isinstance(node, ast.BinOp) and isinstance(node.op, op)


is_lshift = rpartial(is_binop, ast.LShift)
is_rshift = rpartial(is_binop, ast.RShift)
is_bitand = rpartial(is_binop, ast.BitAnd)
is_bitor = rpartial(is_binop, ast.BitOr)

is_name = rpartial(isinstance, ast.Name)
is_str = rpartial(isinstance, ast.Constant)
is_call = rpartial(isinstance, ast.Call)
is_list = rpartial(isinstance, ast.List)
is_set = rpartial(isinstance, ast.Set)
is_tuple = rpartial(isinstance, ast.Tuple)
is_astwrapper = rpartial(isinstance, AstWrapper)
is_operator = rpartial(isinstance, (ast.BinOp, ast.UnaryOp))
is_terminal = rpartial(isinstance, (ast.Name, ast.Constant))
