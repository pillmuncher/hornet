#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

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
