#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
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
