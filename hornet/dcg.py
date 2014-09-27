#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.0.2a'
__date__ = '2014-08-20'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import collections
import copy
import itertools

from .util import identity, foldr, pairwise, receive_missing_args
from .expressions import unit, extract, Name
from .operators import is_rshift, is_bitand, is_name, is_list, is_set, is_call
from .operators import is_str



_C_ = Name("'C'")



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



def numbered_vars(prefix):

    for n in itertools.count():
        yield extract(Name(prefix + str(n)))



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



class NodeTagger:

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
        self.left_side.append(goal_setter(extract(call)))
        return call

    def as_terminal(self, call):
        self.left_side.append(terminal_setter(extract(call)))
        return call

    def as_pushback(self, call):
        self.right_side.appendleft(pushback_setter(extract(call)))
        return call



def dcg_call(node, tagged):

    if is_name(node):
        return tagged(unit(node)())

    elif is_call(node):
        return tagged(unit(copy.deepcopy(node)))

    else:
        raise TypeError('Name or Call node expected, not {}'.format(node))



def dcg_list(node, tagged, cont=identity):

    if not node.elts:
        return cont(None)

    elif all(is_name(each) or is_str(each) for each in node.elts):
        *elts, last = (tagged(_C_(unit(each))) for each in node.elts)
        return foldr(conjunction, elts, cont(last))

    else:
        raise TypeError(
            'Non-terminal in DCG terrminal list found: {}'.format(left))



def dcg_body(node, tag, cont=identity):

    if is_bitand(node):

        def right_side(rightmost_of_left_side):
            return conjunction(
                rightmost_of_left_side,
                dcg_body(node.right, tag, cont))

        return dcg_body(node.left, tag, right_side)

    elif is_list(node):
        return dcg_list(node, tag.as_terminal, cont)

    elif is_set(node):
        assert len(node.elts) == 1
        return cont(unit(node.elts[0]))

    else:
        return cont(dcg_call(node, tag.as_goal))



def dcg_clause(node):

    head, body = node.left, node.right

    with NodeTagger() as tag:

        if is_bitand(head):

            def pushback(rightmost_of_body):
                return conjunction(
                    rightmost_of_body,
                    dcg_list(head.right, tag.as_pushback))

            return rule(
                dcg_call(head.left, tag.as_goal),
                dcg_body(body, tag, pushback))

        else:
            return rule(
                dcg_call(head, tag.as_goal),
                dcg_body(body, tag))



def dcg_expand(node):

    return dcg_clause(node) if is_rshift(node) else unit(node)
