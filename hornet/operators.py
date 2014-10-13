#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import ast
import collections
import enum
import functools
import operator

from .util import pairwise, compose2 as compose
from .expressions import lift, promote, AstWrapper, is_tuple, is_astwrapper
from .expressions import is_name, is_operator


class ParseError(Exception):
    pass


parse_error = compose('Precedence conflict: ({}) {} ({})'.format, ParseError)


class Token(collections.namedtuple('BaseToken', 'lbp rbp node')):

    __slots__ = ()

    def __lt__(left, right):
        return left.rbp < right.lbp

    def __gt__(left, right):
        return left.rbp > right.lbp

    def __le__(left, right):
        return left.rbp <= right.lbp

    def __ge__(left, right):
        return left.rbp >= right.lbp


class Nofix(Token):

    __slots__ = ()

    def nud(self, parse, table):
        return self.node


class Prefix(Token):

    __slots__ = ()

    def __new__(cls, lbp, rbp, node):
        return Token.__new__(cls, 0, rbp, node)

    def nud(self, parse, table):
        right = parse(self.rbp)
        check_right(self, right, table)
        return ast.UnaryOp(self.node, right)


class Infix(Token):

    __slots__ = ()

    def led(self, left, parse, table):
        check_left(self, left, table)
        right = parse(self.rbp)
        check_right(self, right, table)
        return ast.BinOp(left, self.node, right)


END = Nofix(0, 0, None)


def check_left(op, left, table):
    if is_operator(left):
        left_token = make_token(table, left.op)
        if left_token.rbp == op.lbp:
            raise parse_error(left_token.rbp, op.node, op.lbp)


def check_right(op, right, table):
    if is_operator(right):
        right_token = make_token(table, right.op)
        if op.rbp == right_token.lbp:
            raise parse_error(op.rbp, right, right_token.lbp)


class Fix(enum.IntEnum):

    Left = -1
    Non = 0
    Right = 1

    def __call__(self, num):
        return self + num, num


def fixity(factory, fix):
    def apply_binding_power(bp):
        return functools.partial(factory, *fix(bp))
    return apply_binding_power


f = fixity(Nofix, Fix.Non)
fx = fixity(Prefix, Fix.Non)
fy = fixity(Prefix, Fix.Right)
xfx = fixity(Infix, Fix.Non)
xfy = fixity(Infix, Fix.Right)
yfx = fixity(Infix, Fix.Left)


F0 = f(0)


def make_token(table, node):
    return table.get(type(node), F0)(node)


def operator_fixity(table):
    return lambda node: make_token(table, node.op)


def pratt_parse(nodes, table):

    tokens = (make_token(table, node) for node in nodes)
    token_pairs = pairwise(tokens, fillvalue=END)
    token = None

    def parse(rbp):

        nonlocal token

        t, token = next(token_pairs)
        left = t.nud(parse, table)

        while rbp < token.lbp:
            t, token = next(token_pairs)
            left = t.led(left, parse, table)

        return left

    return parse(0)


# see: https://docs.python.org/3/reference/expressions.html#operator-precedence
python_fixities = {
    ast.BitOr: yfx(10),
    ast.BitXor: yfx(20),
    ast.BitAnd: yfx(30),
    ast.LShift: xfx(45),  # yeah, i know that's cheating...
    ast.RShift: xfx(40),
    ast.Add: yfx(50),
    ast.Sub: yfx(50),
    ast.Mult: yfx(60),
    ast.Div: yfx(60),
    ast.FloorDiv: yfx(60),
    ast.Mod: yfx(60),
    ast.USub: fy(70),
    ast.UAdd: fy(70),
    ast.Invert: fy(70),
    ast.Pow: xfy(80),
}


hornet_fixities = {
    ast.BitOr: xfy(10),
    ast.BitXor: xfy(20),
    ast.BitAnd: xfy(30),
    ast.LShift: xfx(4),
    ast.RShift: xfx(7),
    ast.Add: yfx(50),
    ast.Sub: yfx(50),
    ast.Mult: yfx(60),
    ast.Div: yfx(60),
    ast.FloorDiv: yfx(60),
    ast.Mod: yfx(60),
    ast.USub: fy(70),
    ast.UAdd: fy(70),
    ast.Invert: fy(70),
    ast.Pow: xfy(80),
}


python_fixities[ast.UnaryOp] = operator_fixity(python_fixities)
python_fixities[ast.BinOp] = operator_fixity(python_fixities)


unaryop_fields = operator.attrgetter('op', 'operand')
binop_fields = operator.attrgetter('left', 'op', 'right')


class ASTFlattener(ast.NodeVisitor):

    def __init__(self, nodes, fixities):
        self.append = nodes.append
        self.fixities = fixities

    def visit_Name(self, node):
        self.append(node)

    def visit_Str(self, node):
        self.append(node)

    def visit_Bytes(self, node):
        self.append(node)

    def visit_Num(self, node):
        if node.n >= 0:
            self.append(node)
        else:
            self.visit((-promote(-node.n)).node)

    def visit_Tuple(self, node):
        self.append(
            ast.Tuple(
                elts=[_rearrange(each) for each in node.elts],
                ctx=ast.Load()))

    def visit_List(self, node):
        self.append(
            ast.List(
                elts=[_rearrange(each) for each in node.elts],
                ctx=ast.Load()))

    def visit_Set(self, node):
        if len(node.elts) != 1:
            raise TypeError('Only sets with exactly one item allowed, not {}'
                            .format(node))
        self.append(
            ast.Set(
                elts=[_rearrange(each) for each in node.elts]))

    def visit_Dict(self, node):
        raise TypeError('Dicts not allowed: ')

    def visit_AstWrapper(self, node):
        self.append(node)

    def visit_Subscript(self, node):
        if is_tuple(node.slice.value):
            elts = node.slice.value.elts
            if all(callable(each.wrapped) for each in elts):
                actions = [each.wrapped for each in elts]
            else:
                raise TypeError('Subscript must be one or more callables!')
        elif is_astwrapper(node.slice.value):
            actions = [node.slice.value.wrapped]
        else:
            raise TypeError('Subscript must be one or more callables!')
        self.append(
            ast.Subscript(
                value=_rearrange(node.value),
                slice=actions,
                ctx=ast.Load()))

    def visit_Call(self, node):
        if not is_name(node.func):
            raise TypeError('{} is not a valid functor name.'
                            .format(node.func))
        if node.keywords:
            raise TypeError('Keyword arguments are not allowed: {}'
                            .format(node))
        if node.starargs:
            raise TypeError('Starred arguments are not allowed: {}'
                            .format(node))
        if node.kwargs:
            raise TypeError('Starred keyword arguments are not allowed: {}'
                            .format(node))
        self.append(
            ast.Call(
                func=node.func,
                args=[_rearrange(arg) for arg in node.args],
                keywords=[],
                starargs=None,
                kwargs=None))

    def visit_BinOp(self, node):

        left, op, right = binop_fields(node)

        op_fixity = make_token(self.fixities, op)
        left_fixity = make_token(self.fixities, left)
        right_fixity = make_token(self.fixities, right)

        if left_fixity > op_fixity:
            self.visit(left)
        else:
            self.append(_rearrange(left))

        self.append(op)

        if op_fixity < right_fixity:
            self.visit(right)
        else:
            self.append(_rearrange(right))

    def visit_UnaryOp(self, node):

        op, operand = unaryop_fields(node)

        op_fixity = make_token(self.fixities, op)
        operand_fixity = make_token(self.fixities, operand)

        self.append(op)

        if op_fixity < operand_fixity:
            self.visit(operand)
        else:
            self.append(_rearrange(operand))


def _rearrange(node):
    flattened = []
    ASTFlattener(flattened, python_fixities).visit(node)
    return pratt_parse(flattened, hornet_fixities)


rearrange = lift(_rearrange)
