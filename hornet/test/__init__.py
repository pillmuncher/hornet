#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.0.2a'
__date__ = '2014-08-20'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from nose.tools import eq_, nottest, assert_raises

from hornet.expressions import bind


def ast_eq(a, b):
    return eq_(repr(a), repr(b))


def ast_neq(a, b):
    assert repr(a) != repr(b)


@nottest
def ast_test_all(test, mf_result, mf_expected, *term_pairs):
    for term, expected in term_pairs:
        result = bind(term, mf_result)
        expected = bind(expected, mf_expected)
        try:
            test(result, expected)
        except:
            print(term)
            print(result)
            print(expected)
            print()
            raise


@nottest
def ast_test_all_raise(error, test, *invalid):
    for each in invalid:
        try:
            with assert_raises(error):
                bind(each, test)
        except:
            print(each)
            raise
