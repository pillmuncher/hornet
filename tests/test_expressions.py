#!/usr/bin/env pytest
# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


# import nose

import ast
import itertools

from toolz.functoolz import identity

from . import ast_eq


def test_monad_laws():
    "Test if the basic monadic functions conform to the three Monad Laws."

    from hornet.expressions import bind, mlift, unit

    x = ast.Name(id="x")
    y = ast.Name(id="y")
    z = ast.Name(id="z")
    mx = unit(x)

    mfuncs = [
        unit,
        mlift(identity),
        lambda u: unit(ast.BinOp(left=u, op=ast.BitAnd(), right=y)),
        lambda u: unit(ast.BinOp(left=u, op=ast.BitOr(), right=z)),
        lambda u: unit(ast.BinOp(left=y, op=ast.BitAnd(), right=u)),
        lambda u: unit(ast.BinOp(left=z, op=ast.BitOr(), right=u)),
    ]

    # left identity:
    for mf in mfuncs:
        ast_eq(bind(mx, mf), mf(x))

    # right identity:
    ast_eq(bind(mx, unit), mx)  # type: ignore

    # associativity:
    for mf, mg in itertools.product(mfuncs, repeat=2):
        ast_eq(bind(bind(mx, mf), mg), bind(mx, lambda v: bind(mf(v), mg)))


def test_expression_factories():
    "Test all Expression factory functions that are called directly."

    from hornet.expressions import (
        AstWrapper,
        Constant,
        List,
        Name,
        Set,
        Tuple,
        Wrapper,
        unit,
    )

    obj = object()
    name = "joe"
    num = 123
    keys = [Constant("a"), Constant("b"), Constant("c")]
    pairs = (
        [Name(name), ast.Name(id=name)],
        [Constant(name), ast.Constant(value=name)],
        [Constant(num), ast.Constant(value=num)],
        [Tuple(keys), ast.Tuple(elts=keys)],  # type: ignore
        [List(keys), ast.List(elts=keys)],  # type: ignore
        [Set(keys), ast.Set(elts=keys)],  # type: ignore
        [Wrapper(obj), AstWrapper(wrapped=obj)],
    )
    for expr, node in pairs:
        ast_eq(expr, unit(node))

    # def test_expression_operators():
    "Test all Expression factory functions that are called as operators."

    from hornet.expressions import Constant, unit
    from hornet.symbols import x, y  # type: ignore

    x_name = x.node
    y_name = y.node
    items = [Constant(1), Constant(2), Constant(3)]

    pairs = (
        [x[y], ast.Subscript(value=x_name, slice=ast.Slice(lower=y_name))],
        [
            x(1, 2, 3),
            ast.Call(
                func=x_name,
                args=items,  # type: ignore
                keywords=[],
            ),
        ],
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
        [x**y, ast.Pow],
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
