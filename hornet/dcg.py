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

from hornet.util import identity, foldr, rotate, splitpairs
from hornet.expressions import (
    unit, Name, is_rshift, is_bitand, is_name, is_set, is_list, is_call,
    is_terminal
)


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


def expand(root):

    if not is_rshift(root):
        return unit(root)

    def expand_call(node):

        if is_name(node):
            return collect_functor(unit(node)())

        elif is_call(node):
            return collect_functor(unit(copy.deepcopy(node)))

        else:
            raise TypeError('Name or Call node expected, not {}'.format(node))

    def expand_terminals(node, cont):

        if not node.elts:
            return cont(None)

        elif all(is_terminal(each) for each in node.elts):
            *elts, last = (
                collect_terminal(_C_(unit(each))) for each in node.elts)
            return foldr(conjunction, elts, cont(last))

        else:
            raise TypeError(
                'Non-terminal in DCG terrminal list found: {}'.format(node))

    def expand_pushbacks(node):

        if not node.elts:
            return None

        elif all(is_terminal(each) for each in node.elts):
            elts = [collect_pushback(_C_(unit(each))) for each in node.elts]
            return foldr(conjunction, elts)

        else:
            raise TypeError(
                'Non-terminal in DCG pushback list found: {}'.format(node))

    def expand_body(node, cont):

        if is_bitand(node):

            def right_side(rightmost_of_left_side):
                return conjunction(
                    rightmost_of_left_side,
                    expand_body(node.right, cont))

            return expand_body(node.left, right_side)

        elif is_list(node):
            return expand_terminals(node, cont)

        elif is_set(node):
            assert len(node.elts) == 1
            return cont(unit(node.elts[0]))

        else:
            return cont(expand_call(node))

    def expand_clause(node):

        head = node.left
        body = node.right

        if is_bitand(head):

            def pushback(rightmost_of_body):
                return conjunction(
                    rightmost_of_body,
                    expand_pushbacks(head.right))

            return rule(
                expand_call(head.left),
                expand_body(body, pushback))

        else:
            return rule(
                expand_call(head),
                expand_body(body, identity))

    from_left = []
    from_right = collections.deque()

    def collect_functor(call):
        args = call.node.args
        from_left.append(args.append)
        from_left.append(args.append)
        return call

    def collect_terminal(call):
        args = call.node.args
        from_left.append(functools.partial(args.insert, -1))
        from_left.append(args.append)
        return call

    def collect_pushback(call):
        args = call.node.args
        from_right.appendleft(functools.partial(args.insert, -2))
        from_right.appendleft(args.append)
        return call

    clause = expand_clause(root)

    pairs = splitpairs(rotate(itertools.chain(from_left, from_right)))
    for (set_left, set_right), var in zip(pairs, numbered_vars('_')):
        set_left(var)
        set_right(var)

    return clause
