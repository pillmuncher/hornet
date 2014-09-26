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


import nose

from hornet.test import *
from hornet.util import identity
from hornet.expressions import bind, lift


def test_rearrange():

    from hornet.operators import rearrange, ParseError

    from hornet.symbols import a, b, c, d, e

    ast_test_all(
        ast_eq,
        rearrange,
        lift(identity),
        (a, a),
        ((((a & b) & c) & d) & e, a & (b & (c & (d & e)))),
        ((((a << b) & c) & d) & e, a << (b & (c & (d & e)))),
        #(a & (b | c), a & (b | c)),
    )

    ast_test_all_raise(
        ValueError,
        rearrange,
        a.foo,
        a(1).foo[b, 2].bar,
        c({a:1, b:2}),
    )
    ast_test_all_raise(
        TypeError,
        rearrange,
        a.foo.bar((b & c) & d),
        a.foo[(b & c) & d],
        a[1],
    )
    ast_test_all_raise(
        ParseError,
        rearrange,
        a << b << c,
        #a << b >> c,
        a >> b >> c,
        #a >> b << c,
        #a << b & c | d << e,
        #a << b & c | d >> e,
        #a >> b & c | d >> e,
        #a >> b & c | d << e,
    )
