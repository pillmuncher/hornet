#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import codegen

import ast
import functools
import numbers
import operator
import weakref

from .util import identity, flip, foldl, qualname, compose2 as compose


__all__ = [
    # classes:
    'Expression',
    'ExpressionTransformer',
    'ExpressionVisitor',
    # monadic functions:
    'unit',
    'bind',
    'lift',
    'mapply',
    'mcompose',
    'copy',
    # helper functions:
    'promote',
    'astify',
    # Expression factory functions:
    'Name',
    'Bytes',
    'Str',
    'Num',
    'Tuple',
    'List',
    'Set',
    'Dict',
    'Wrapper',
    # Expression factory operators:
    'Subscript',
    'Call',
    'USub',
    'UAdd',
    'Invert',
    'Add',
    'Sub',
    'Mult',
    'Div',
    'FloorDiv',
    'Mod',
    'Pow',
    'LShift',
    'RShift',
    'BitAnd',
    'BitXor',
    'BitOr',
]


# The Expression class is a wrapper for ASTs. These aren't held by Expression
# objects directly because of the reasons and by the means mentioned above.
#
# Together, Expression and the bind function below constitute a Monad.
# See also .test.test_expresion.test_monad_laws()

class Expression:

    __slots__ = 'node'

    def __init__(self, node):
        "Initialize an Expression object with an AST node."
        self.node = node

    def __repr__(self):
        return ast.dump(self.node)

    def __str__(self):
        return codegen.to_source(self.node)


# In the Monad, unit is the same as Expression:

unit = Expression


# The function bind(expr:Expression, mfunc:AST --> Expression) --> Expression
# is the monadic bind operator.  It takes an Expression object expr and a
# monadic function mfunc, passes the AST associated with expr to mfunc and
# returns whatever mfunc returns.

def bind(expr, mfunc):
    return mfunc(expr.node)


# The function lift(func:T --> AST) --> (T --> Expression) "lifts" a normal
# function that returns an AST into a function that returns an Expression.
# It is also used as a function decorator.

def lift(func):
    return compose(func, unit)


# Turn a monadic function mf:AST --> Expression into one that can be called
# directly on an Expression object. The resulting function therefor has the
# signature Expression --> Expression.

def mapply(mfunc):
    return lambda expr: mfunc(expr.node)


# Make monadic functions mf:AST --> Expression composable:

def mcompose(*mfuncs):
    return compose(unit, functools.partial(foldl, bind, mfuncs))


# Here come the Expression factory functions.
#
# The arguments they take are converted to AST objects if necessary. They
# return an AST node that gets wrapped in an Expression object by the lift
# decorator.
# Their names don't conform to PEP-8 because they reflect the AST node types
# they represent.

@lift
def Name(name, **kwargs):
    return ast.Name(id=name, ctx=ast.Load(), **kwargs)


@lift
def Str(str_):
    return ast.Str(s=str_)


@lift
def Bytes(bytes_):
    return ast.Bytes(s=bytes_)


@lift
def Num(num):
    return ast.Num(n=num)


@lift
def Tuple(tuple_):
    return ast.Tuple(
        elts=[astify(each) for each in tuple_],
        ctx=ast.Load(),
    )


@lift
def List(list_):
    return ast.List(
        elts=[astify(each) for each in list_],
        ctx=ast.Load(),
    )


@lift
def Set(set_):
    return ast.Set(elts=[astify(each) for each in set_])


@lift
def Dict(dict_):
    keys, values = zip(*dict_.items())
    return ast.Dict(
        keys=[astify(key) for key in keys],
        values=[astify(value) for value in values]
    )


# Although the following functions do not represent AST node types, they are
# used in the same way and should follow the same conventions as the ones
# above.


class AstWrapper(ast.AST):
    pass


@lift
def Wrapper(wrapped):
    return AstWrapper(wrapped=wrapped)


# The last set of factory functions are used as operator methods of  Expression
# objects.  They are bound to the Expression class below.
#
# When trying to understand what's going on in these functions, some questions
# may arise: Where come the arguments from and, if   these are supposed to be
# operator methods in the Expression class, then where the heck is self?
#
# Let's see an example:

# x = Name('x')
# y = x + 3
# z = y + 5

# Here x is an Expression object created by Name('x'). It wraps around an AST
# node ast.Name(id='x', ctx='ast.Load())
#
# x + 3 triggers Expression.__add__ to be called with arguments x and 3.
# Expression.__add__ is bound to the Add factory function which has two
# parameters left and right.  So, x gets passed as left and 3 gets passed as
# right.  Add now calles astify on each argument. For left this just extracts
# the already existing AST node, but for right (which is 3), astify first calls
# the factory function Num, which in turn creates an Expression wrapped around
# an AST node ast.Num(n=3) and then unwraps it again and returns just the AST.
# Then Add attaches both AST nodes as children to an ast.BinOp node which it
# returns.  Since Add was decorated with the lift function, the result gets
# wrapped in an Expression node, which is returned.  The return value then gets
# bound to y.  In the next line, y + 5 triggers Expression.__add__ again and
# the same thing as before happens, but with arguments y and 5.
#
# But what if we change the last line to:

# z = 5 + y

# 5 (an int) doesn't know how to add an Expression object to itself, so it
# returns NotImplemented which causes Python to call the right argument's
# reversed add method Expression.__radd__.  All reversed operator methods are
# called with swapped operands, like so: Expression.__radd__(right, left). But
# since we used the flip decorator when we bound Add to Expression.__radd__,
# the order in which the arguments are passed are reversed again and we're back
# at Expression.__radd__(left, right).  left is bound to 5 and right to y, as
# we would expect when we saw 5 + y. When we construct our AST node, it comes
# out correctly:

# ast.BinOp(
#         left=ast.Num(n=5),
#         op=ast.Add(),
#         right=ast.Name(id='y', ctx=ast.Load())
#     )

# For more complex cases like e.g.:

# x - y * z + 1

# we rely on the priority and associativity rules that Python imposes on us.
# Then this expression is the same as ((x - (y * z)) + 1).

@qualname('Expression.__getitem__')
@lift
def Subscript(target, subscript):
    return ast.Subscript(
        value=astify(target),
        slice=ast.Index(value=astify(subscript)),
        ctx=ast.Load(),
    )


@qualname('Expression.__call__')
@lift
def Call(target, *args, **kwargs):
    return ast.Call(
        func=astify(target),
        args=[astify(each) for each in args],
        keywords=[ast.keyword(arg=arg, value=astify(value))
                    for arg, value in kwargs.items()],
        starargs=None,
        kwargs=None,
    )


def _unary_op(op, name):
    @qualname(name)
    @lift
    def op_method(right):
        return ast.UnaryOp(op(), astify(right))
    return op_method


USub = _unary_op(ast.USub, 'Expression.__neg__')
UAdd = _unary_op(ast.UAdd, 'Expression.__pos__')
Invert = _unary_op(ast.Invert, 'Expression.__invert__')


def _binary_op(op, name):
    @qualname(name)
    @lift
    def op_method(left, right):
        return ast.BinOp(astify(left), op(), astify(right))
    return op_method


Add = _binary_op(ast.Add, 'Expression.__add__')
Sub = _binary_op(ast.Sub, 'Expression.__sub__')
Mult = _binary_op(ast.Mult, 'Expression.__mul__')
Div = _binary_op(ast.Div, 'Expression.__truediv__')
FloorDiv = _binary_op(ast.FloorDiv, 'Expression.__floordiv__')
Mod = _binary_op(ast.Mod, 'Expression.__mod__')
Pow = _binary_op(ast.Pow, 'Expression.__pow__')
LShift = _binary_op(ast.LShift, 'Expression.__lshift__')
RShift = _binary_op(ast.RShift, 'Expression.__rshift__')
BitAnd = _binary_op(ast.BitAnd, 'Expression.__and__')
BitXor = _binary_op(ast.BitXor, 'Expression.__xor__')
BitOr = _binary_op(ast.BitOr, 'Expression.__or__')


# Here the Expression factory operator functions get finally bound to the
# Expression class:

Expression.__getitem__ = Subscript
Expression.__call__ = Call
Expression.__neg__ = USub
Expression.__pos__ = UAdd
Expression.__invert__ = Invert
Expression.__add__ = Add
Expression.__radd__ = flip(Add)
Expression.__sub__ = Sub
Expression.__rsub__ = flip(Sub)
Expression.__mul__ = Mult
Expression.__rmul__ = flip(Mult)
Expression.__truediv__ = Div
Expression.__rtruediv__ = flip(Div)
Expression.__floordiv__ = FloorDiv
Expression.__rfloordiv__ = flip(FloorDiv)
Expression.__mod__ = Mod
Expression.__rmod__ = flip(Mod)
Expression.__pow__ = Pow
Expression.__rpow__ = flip(Pow)
Expression.__lshift__ = LShift
Expression.__rlshift__ = flip(LShift)
Expression.__rshift__ = RShift
Expression.__rrshift__ = flip(RShift)
Expression.__and__ = BitAnd
Expression.__rand__ = flip(BitAnd)
Expression.__xor__ = BitXor
Expression.__rxor__ = flip(BitXor)
Expression.__or__ = BitOr
Expression.__ror__ = flip(BitOr)


# Any Python object 'item' will be turned into an Expression object with its
# AST created if necessary:

_promotions = [
    (Expression, identity),
    (bytes, Bytes),
    (str, Str),
    (numbers.Number, Num),
    (tuple, Tuple),
    (list, List),
    (set, Set),
    (dict, Dict),
    (object, Wrapper),
]

def promote(item):
    for T, F in _promotions:
        if isinstance(item, T):
            return F(item)


# Given any Python object 'item', return its AST (and create it if necessary):

def astify(item):
    return promote(item).node
