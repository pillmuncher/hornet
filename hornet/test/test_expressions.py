#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


# import nose

import ast
import collections
import itertools
import operator

from hornet.test import *
from hornet.util import identity, compose2 as compose


load = ast.Load()


def test_monad_laws():
    "Test if the basic monadic functions conform to the three Monad Laws."

    from hornet.expressions import unit, bind, mlift

    x = ast.Name(id='x', ctx=load)
    y = ast.Name(id='y', ctx=load)
    z = ast.Name(id='z', ctx=load)
    mx = unit(x)

    binop = lambda u, op, v: unit(ast.BinOp(left=u, op=op(), right=v))
    and_y = lambda u: binop(u, ast.BitAnd, y)
    or_z = lambda u: binop(u, ast.BitOr, z)
    y_and = lambda v: binop(y, ast.BitAnd, v)
    z_or = lambda v: binop(z, ast.BitOr, v)
    mfuncs = [unit, mlift(identity), and_y, or_z, y_and, z_or]

    # left identity:
    for mf in mfuncs:
        ast_eq(bind(mx, mf), mf(x))

    # right identity:
    ast_eq(bind(mx, unit), mx)

    # associativity:
    for mf, mg in itertools.product(mfuncs, repeat=2):
        ast_eq(
            bind(bind(mx, mf), mg),
            bind(mx, lambda v: bind(mf(v), mg))
        )


def test_expression_factories():
    "Test all Expression factory functions that are called directly."

    from hornet.expressions import (
        unit, Name, Str, Bytes, Num, Tuple, List, Set, Wrapper, AstWrapper
    )

    class Callable:
        def __call__(self):
            pass

    obj = object()
    name = 'joe'
    num = 123
    keys = [Str('a'), Str('b'), Str('c')]
    values = [Num(1), Num(2), Num(3)]
    pairs = (
        [Name(name), ast.Name(id=name, ctx=load)],
        [Str(name), ast.Str(s=name)],
        [Bytes(name), ast.Bytes(s=name)],
        [Num(num), ast.Num(n=num)],
        [Tuple(keys), ast.Tuple(elts=keys, ctx=load)],
        [List(keys), ast.List(elts=keys, ctx=load)],
        [Set(keys), ast.Set(elts=keys)],
        [Wrapper(obj), AstWrapper(wrapped=obj)],
    )
    for expr, node in pairs:
        ast_eq(expr, unit(node))


def test_expression_operators():
    "Test all Expression factory functions that are called as operators."

    from hornet.expressions import unit, Num
    from hornet.symbols import x, y

    x_name = x.node
    y_name = y.node
    name = 'joe'
    num = 123
    items = [Num(1), Num(2), Num(3)]

    pairs = (
        [x[y], ast.Subscript(value=x_name, slice=ast.Index(y_name), ctx=load)],
        [x(1, 2, 3),
         ast.Call(
            func=x_name,
            args=items,
            keywords=[],
            starargs=None,
            kwargs=None,
        )],
    )
    for expr, node in pairs:
        ast_eq(expr, unit(node))

    pairs = (
        [-x, ast.USub],
        [+x, ast.UAdd],
        [~x, ast.Invert],
    )
    for expr, op in pairs:
        ast_eq(expr, unit(ast.UnaryOp(op(), x_name)))

    pairs = (
        [x ** y, ast.Pow],
        [x * y, ast.Mult],
        [x / y, ast.Div],
        [x // y, ast.FloorDiv],
        [x % y, ast.Mod],
        [x + y, ast.Add],
        [x - y, ast.Sub],
        [x << y, ast.LShift],
        [x >> y, ast.RShift],
        [x & y, ast.BitAnd],
        [x ^ y, ast.BitXor],
        [x | y, ast.BitOr],
    )
    for expr, op in pairs:
        ast_eq(expr, unit(ast.BinOp(x_name, op(), y_name)))
