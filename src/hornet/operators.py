#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.5a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import ast
import collections
import numbers
import operator
from dataclasses import dataclass

from toolz.functoolz import compose, curry, identity

from .util import pairwise, const
from .expressions import is_name, is_operator, is_tuple, is_astwrapper
from .expressions import mlift, promote, Expression


decrement = (-1).__add__


class ParseError(Exception):
    pass


parse_error = compose(ParseError, 'Precedence conflict: ({}) {} ({})'.format)


@dataclass(frozen=True)
class Token:

    left_rank: int
    right_rank: int
    node: Expression

    def __lt__(self, other):
        return self.right_rank < other.left_rank

    def __gt__(self, other):
        return self.right_rank > other.left_rank

    @classmethod
    @curry
    def fixity(cls, left, right, rank, node):
        return cls(left(rank), right(rank), node)


class Nofix(Token):

    __slots__ = ()

    def nud(self, parse):
        return self.node


class Prefix(Token):

    __slots__ = ()

    def nud(self, parse):
        right = parse(self.right_rank)
        check_right(self, right)
        return ast.UnaryOp(self.node, right)


class Infix(Token):

    __slots__ = ()

    def led(self, left, parse):
        check_left(self, left)
        right = parse(self.right_rank)
        check_right(self, right)
        return ast.BinOp(left, self.node, right)


f = Nofix.fixity(identity, identity)
fx = Prefix.fixity(identity, identity)
fy = Prefix.fixity(identity, decrement)
fz = Prefix.fixity(const(0), decrement)
xfx = Infix.fixity(identity, identity)
xfy = Infix.fixity(identity, decrement)
yfx = Infix.fixity(decrement, identity)


HORNET_FIXITIES = {
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


NON_OP = f(0)
END = NON_OP(None)


def make_token(fixities, node):
    return fixities.get(type(node), NON_OP)(node)


def check_left(op, left_node):
    if is_operator(left_node):
        left = make_token(HORNET_FIXITIES, left_node.op)
        if left.right_rank == op.left_rank:
            raise parse_error(left.right_rank, op.node, op.left_rank)


def check_right(op, right_node):
    if is_operator(right_node):
        right = make_token(HORNET_FIXITIES, right_node.op)
        if op.right_rank == right.left_rank:
            raise parse_error(op.right_rank, right_node, right.left_rank)


def pratt_parse(nodes):

    tokens = (make_token(HORNET_FIXITIES, node) for node in nodes)
    token_pairs = pairwise(tokens, fillvalue=END)
    token = None

    def parse(right_rank):

        nonlocal token

        t, token = next(token_pairs)
        left = t.nud(parse)

        while right_rank < token.left_rank:
            t, token = next(token_pairs)
            left = t.led(left, parse)

        return left

    return parse(0)


def inherit_fixity(node):
    return make_token(PYTHON_FIXITIES, node.op)


# see: https://docs.python.org/3/reference/expressions.html#operator-precedence
PYTHON_FIXITIES = {
    ast.BitOr: yfx(10),
    ast.BitXor: yfx(20),
    ast.BitAnd: yfx(30),
    ast.LShift: yfx(45),  # yeah, i know that's cheating...
    ast.RShift: yfx(40),
    ast.Add: yfx(50),
    ast.Sub: yfx(50),
    ast.Mult: yfx(60),
    ast.Div: yfx(60),
    ast.FloorDiv: yfx(60),
    ast.Mod: yfx(60),
    ast.USub: fz(70),
    ast.UAdd: fz(70),
    ast.Invert: fz(70),
    ast.Pow: xfy(80),
    ast.UnaryOp: inherit_fixity,
    ast.BinOp: inherit_fixity,
}


unaryop_fields = operator.attrgetter('op', 'operand')
binop_fields = operator.attrgetter('left', 'op', 'right')


class ASTFlattener(ast.NodeVisitor):

    def __init__(self, nodes):
        self.append = nodes.append

    def visit_Name(self, node):
        self.append(node)

    def visit_Constant(self, node):
        if isinstance(node.value, numbers.Number):
            if node.n >= 0:
                self.append(node)
            else:
                self.visit((-promote(-node.n)).node)
        elif isinstance(node.value, str):
            self.append(node)
        else:
            raise ValueError("node must be of type str or Number!")

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
        if is_tuple(node.slice.lower):
            elts = node.slice.lower.elts
            if all(callable(each.wrapped) for each in elts):
                actions = [each.wrapped for each in elts]
            else:
                raise TypeError('Subscript must be one or more callables!')
        elif is_astwrapper(node.slice.lower):
            actions = [node.slice.lower.wrapped]
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

    def visit_UnaryOp(self, node):

        op, operand = unaryop_fields(node)

        op_fixity = make_token(PYTHON_FIXITIES, op)
        operand_fixity = make_token(PYTHON_FIXITIES, operand)

        self.append(op)

        if op_fixity < operand_fixity:
            self.visit(operand)
        else:
            self.append(_rearrange(operand))

    def visit_BinOp(self, node):

        left, op, right = binop_fields(node)

        op_fixity = make_token(PYTHON_FIXITIES, op)
        left_fixity = make_token(PYTHON_FIXITIES, left)
        right_fixity = make_token(PYTHON_FIXITIES, right)

        if left_fixity > op_fixity:
            self.visit(left)
        else:
            self.append(_rearrange(left))

        self.append(op)

        if op_fixity < right_fixity:
            self.visit(right)
        else:
            self.append(_rearrange(right))


def _rearrange(node):
    flattened = []
    ASTFlattener(flattened).visit(node)
    return pratt_parse(flattened)


rearrange = mlift(_rearrange)
