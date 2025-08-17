# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


import collections
import copy
import functools
import itertools

from toolz.functoolz import identity

from .expressions import (
    Name,
    is_bitand,
    is_call,
    is_list,
    is_name,
    is_rshift,
    is_set,
    is_terminal,
    unit,
)
from .util import foldr, rotate, split_pairs

_C_ = Name("'C'")


def numbered_vars(prefix):
    for i in itertools.count():
        yield Name(prefix + str(i)).node


def rule(head, body):
    if body:
        return head << body

    else:
        return head


def conjunction(left, right):
    if left and right:
        return left & right

    else:
        return left or right


class Expander:
    def __init__(self):
        self.left = []
        self.right = collections.deque()

    def collect_functor(self, call):
        args = call.node.args
        self.left.append(args.append)
        self.left.append(args.append)
        return call

    def collect_terminal(self, call):
        args = call.node.args
        self.left.append(functools.partial(args.insert, -1))
        self.left.append(args.append)
        return call

    def collect_pushback(self, call):
        args = call.node.args
        self.right.appendleft(functools.partial(args.insert, -2))
        self.right.appendleft(args.append)
        return call

    def expand_call(self, node):
        if is_name(node):
            return self.collect_functor(unit(node)())

        elif is_call(node):
            return self.collect_functor(unit(copy.deepcopy(node)))

        else:
            raise TypeError(f"Name or Call node expected, not {node}")

    def expand_terminals(self, node, cont):
        if not node.elts:
            return cont(None)

        elif all(is_terminal(each) for each in node.elts):
            *elts, last = (self.collect_terminal(_C_(unit(each))) for each in node.elts)
            return foldr(conjunction, elts, cont(last))

        else:
            raise TypeError(f"Non-terminal in DCG terminal list found: {node}")

    def expand_pushbacks(self, node):
        if not node.elts:
            return None

        elif all(is_terminal(each) for each in node.elts):
            elts = [self.collect_pushback(_C_(unit(each))) for each in node.elts]
            return foldr(conjunction, elts)

        else:
            raise TypeError(f"Non-terminal in DCG pushback list found: {node}")

    def expand_body(self, node, cont):
        if is_bitand(node):

            def right_side(rightmost_of_left_side):
                return conjunction(
                    rightmost_of_left_side, self.expand_body(node.right, cont)
                )

            return self.expand_body(node.left, right_side)

        elif is_list(node):
            return self.expand_terminals(node, cont)

        elif is_set(node):
            assert len(node.elts) == 1  # noqa: S101
            return cont(unit(node.elts[0]))

        else:
            return cont(self.expand_call(node))

    def expand_clause(self, node):
        head = node.left
        body = node.right

        if is_bitand(head):

            def pushback(rightmost_of_body):
                return conjunction(rightmost_of_body, self.expand_pushbacks(head.right))

            return rule(self.expand_call(head.left), self.expand_body(body, pushback))

        else:
            return rule(self.expand_call(head), self.expand_body(body, identity))

    def __call__(self, root):
        clause = self.expand_clause(root)

        pairs = split_pairs(rotate(itertools.chain(self.left, self.right)))

        for (set_left, set_right), var in zip(pairs, numbered_vars("_")):
            set_left(var)
            set_right(var)

        return clause


def expand(root):
    if not is_rshift(root):
        return unit(root)

    else:
        return Expander()(root)
