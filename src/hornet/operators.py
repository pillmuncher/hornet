# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = "0.2.7"
__date__ = "2014-09-27"
__author__ = "Mick Krippendorf <m.krippendorf@freenet.de>"
__license__ = "MIT"


import ast
import numbers
import operator

from dataclasses import (
    dataclass,
)
from typing import (
    Callable,
    Protocol,
    Self,
    cast,
)

from toolz.functoolz import (
    identity,
)

from .expressions import (
    is_astwrapper,
    is_name,
    is_operator,
    is_tuple,
    mlift,
    promote,
)
from .util import (
    const,
    compose,
    decrement,
    pairwise,
)

# The following parser is based on the paper "Top Down Operator Precedence"
# by Vaughan R. Pratt (1973). See https://tdop.github.io


class ParseError(Exception):
    pass


parse_error = compose(ParseError, "Precedence conflict: ({}) {} ({})".format)


class NudLed(Protocol):
    def nud(self, parse) -> ast.expr: ...
    def led(self, left, parse) -> ast.expr: ...


@dataclass(frozen=True)
class Token[Op]:
    left_rank: int
    right_rank: int
    node: Op

    def __lt__(self, other):
        return self.right_rank < other.left_rank

    def __gt__(self, other):
        return self.right_rank > other.left_rank

    @classmethod
    def fixity(cls, left: Callable[[int], int], right: Callable[[int], int]):
        def with_rank(rank: int):
            def with_node(node: Op) -> Self:
                return cls(left(rank), right(rank), node)

            return with_node

        return with_rank


class Nofix(Token[ast.expr]):
    __slots__ = ()

    def nud(self, parse) -> ast.expr:
        return self.node


class Prefix(Token[ast.unaryop]):
    __slots__ = ()

    def nud(self, parse) -> ast.expr:
        right = parse(self.right_rank)
        check_right(self, right)
        return ast.UnaryOp(self.node, right)


class Infix(Token[ast.operator]):
    __slots__ = ()

    def led(self, left, parse) -> ast.expr:
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
END = NON_OP(None)  # type: ignore


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


def pratt_parse(nodes) -> ast.expr:
    tokens = (make_token(HORNET_FIXITIES, node) for node in nodes)
    token_pairs = pairwise(tokens, fillvalue=END)
    token = None

    def parse(right_rank) -> ast.expr:
        nonlocal token

        t, token = cast(tuple[NudLed, Token], next(token_pairs))
        left = t.nud(parse)

        while right_rank < token.left_rank:
            t, token = cast(tuple[NudLed, Token], next(token_pairs))
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
    # yeah, i know that's cheating:
    ast.LShift: yfx(45),
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


unaryop_fields = operator.attrgetter("op", "operand")
binop_fields = operator.attrgetter("left", "op", "right")


class ASTFlattener(ast.NodeVisitor):
    def __init__(self, nodes):
        self.node = nodes
        self.append = nodes.append

    def visit_Name(self, node):
        self.append(node)

    def visit_Constant(self, node):
        if isinstance(node.value, numbers.Number):
            if node.value >= 0:  # type: ignore
                self.append(node)
            else:
                self.visit((-promote(-node.n)).node)  # type: ignore
        elif isinstance(node.value, str):
            self.append(node)
        else:
            raise ValueError("node must be of type str or Number!")

    def visit_Tuple(self, node):
        self.append(ast.Tuple(elts=[_rearrange(each) for each in node.elts]))

    def visit_List(self, node):
        self.append(ast.List(elts=[_rearrange(each) for each in node.elts]))

    def visit_Set(self, node):
        if len(node.elts) != 1:
            raise TypeError(f"Only sets with exactly one item allowed, not {node}")
        self.append(ast.Set(elts=[_rearrange(each) for each in node.elts]))

    def visit_Dict(self, node):
        raise TypeError("Dicts not allowed: ")

    def visit_AstWrapper(self, node):
        self.append(node)

    def visit_Subscript(self, node: ast.Subscript):
        if is_tuple(node.slice.lower):  # type: ignore
            elts = node.slice.lower.elts  # type: ignore
            if all(callable(each.wrapped) for each in elts):
                actions = [each.wrapped for each in elts]
            else:
                raise TypeError("Subscript must be one or more callables!")
        elif is_astwrapper(node.slice.lower):  # type: ignore
            actions = [node.slice.lower.wrapped]  # type: ignore
        else:
            raise TypeError("Subscript must be one or more callables!")
        self.append(ast.Subscript(value=_rearrange(node.value), slice=actions))  # type: ignore

    def visit_Call(self, node):
        if not is_name(node.func):
            raise TypeError(f"{node.func} is not a valid functor name.")
        if node.keywords:
            raise TypeError(f"Keyword arguments are not allowed: {node}")
        if any(isinstance(arg, ast.Starred) for arg in node.args):
            raise TypeError(f"Starred arguments are not allowed: {node}")
        self.append(
            ast.Call(
                func=node.func,
                args=[_rearrange(arg) for arg in node.args],
                keywords=[],
            )
        )

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
