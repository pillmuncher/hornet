#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import collections
import copy
import itertools

from hornet.util import identity, foldr, pairwise, receive_missing_args
from hornet.expressions import unit, Name, is_rshift, is_bitand, is_name
from hornet.expressions import is_set, is_list, is_call, is_terminal


_C_ = Name("'C'")


def numbered_vars(prefix):
    for n in itertools.count():
        yield Name(prefix + str(n)).node


@receive_missing_args
def goal_setter(node, first, second):
    node.args.append(first)
    node.args.append(second)


@receive_missing_args
def terminal_setter(node, first, second):
    node.args.insert(-1, first)
    node.args.append(second)


@receive_missing_args
def pushback_setter(node, first, second):
    node.args.insert(-1, second)
    node.args.append(first)


class NodeCollector:

    def __enter__(self):
        self.left_side = []
        self.right_side = collections.deque()
        return self

    def __exit__(self, *args):
        chained_sides = itertools.chain(self.left_side, self.right_side)
        setter_pairs = pairwise(chained_sides, rotate=True)
        for (left, right), s_var in zip(setter_pairs, numbered_vars('_')):
            left.send(s_var)
            right.send(s_var)
        del self.left_side
        del self.right_side

    def as_goal(self, call):
        self.left_side.append(goal_setter(call.node))
        return call

    def as_terminal(self, call):
        self.left_side.append(terminal_setter(call.node))
        return call

    def as_pushback(self, call):
        self.right_side.appendleft(pushback_setter(call.node))
        return call


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


def expand_call(node, collect):

    if is_name(node):
        return collect(unit(node)())

    elif is_call(node):
        return collect(unit(copy.deepcopy(node)))

    else:
        raise TypeError('Name or Call node expected, not {}'.format(node))


def expand_list(node, collect, cont=identity):

    if not node.elts:
        return cont(None)

    elif all(is_terminal(each) for each in node.elts):
        *elts, last = (collect(_C_(unit(each))) for each in node.elts)
        return foldr(conjunction, elts, cont(last))

    else:
        raise TypeError(
            'Non-terminal in DCG terrminal list found: {}'.format(node))


def expand_body(node, collect, cont=identity):

    if is_bitand(node):

        def right_side(rightmost_of_left_side):
            return conjunction(
                rightmost_of_left_side,
                expand_body(node.right, collect, cont))

        return expand_body(node.left, collect, right_side)

    elif is_list(node):
        return expand_list(node, collect.as_terminal, cont)

    elif is_set(node):
        assert len(node.elts) == 1
        return cont(unit(node.elts[0]))

    else:
        return cont(expand_call(node, collect.as_goal))


def expand_clause(node):

    head, body = node.left, node.right

    with NodeCollector() as collect:

        if is_bitand(head):

            def pushback(rightmost_of_body):
                return conjunction(
                    rightmost_of_body,
                    expand_list(head.right, collect.as_pushback))

            return rule(
                expand_call(head.left, collect.as_goal),
                expand_body(body, collect, pushback))

        else:
            return rule(
                expand_call(head, collect.as_goal),
                expand_body(body, collect))


def expand(node):
    return expand_clause(node) if is_rshift(node) else unit(node)
