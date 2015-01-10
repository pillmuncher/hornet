#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import collections
import contextlib
import copy
import functools
import itertools

from hornet.util import identity, foldr, rotate, crocodile
from hornet.expressions import unit, Name, is_rshift, is_bitand, is_name
from hornet.expressions import is_set, is_list, is_call, is_terminal


_C_ = Name("'C'")


def numbered_vars(prefix):
    for n in itertools.count():
        yield Name(prefix + str(n)).node


@contextlib.contextmanager
def node_collector():

    from_left = []
    from_right = collections.deque()

    class NodeCollector:

        def collect_goal(self, call):
            args = call.node.args
            from_left.append(args.append)
            from_left.append(args.append)
            return call

        def collect_terminal(self, call):
            args = call.node.args
            from_left.append(functools.partial(args.insert, -1))
            from_left.append(args.append)
            return call

        def collect_pushback(self, call):
            args = call.node.args
            from_right.appendleft(functools.partial(args.insert, -2))
            from_right.appendleft(args.append)
            return call

    yield NodeCollector()

    pairs = crocodile(rotate(itertools.chain(from_left, from_right)))
    for (set_left, set_right), var in zip(pairs, numbered_vars('_')):
        set_left(var)
        set_right(var)

    del from_left
    del from_right


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


def expand_body(node, collector, cont=identity):

    if is_bitand(node):

        def right_side(rightmost_of_left_side):
            return conjunction(
                rightmost_of_left_side,
                expand_body(node.right, collector, cont))

        return expand_body(node.left, collector, right_side)

    elif is_list(node):
        return expand_list(node, collector.collect_terminal, cont)

    elif is_set(node):
        assert len(node.elts) == 1
        return cont(unit(node.elts[0]))

    else:
        return cont(expand_call(node, collector.collect_goal))


def expand_clause(node, collector):

    head, body = node.left, node.right

    if is_bitand(head):

        def pushback(rightmost_of_body):
            return conjunction(
                rightmost_of_body,
                expand_list(head.right, collector.collect_pushback))

        return rule(
            expand_call(head.left, collector.collect_goal),
            expand_body(body, collector, pushback))

    else:
        return rule(
            expand_call(head, collector.collect_goal),
            expand_body(body, collector))


def expand(node):
    if is_rshift(node):
        with node_collector() as collector:
            return expand_clause(node, collector)
    else:
        return unit(node)
