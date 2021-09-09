#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.5a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from . import expression_all, expression_all_raise, ast_eq
from toolz.functoolz import identity
from hornet.expressions import mlift


def test_rearrange():

    from hornet.operators import rearrange, ParseError

    from hornet.symbols import a, b, c, d, e

    expression_all(
        ast_eq,
        rearrange,
        mlift(identity),
        (
            a,
            a
        ),
        (
            (((a & b) & c) & d) & e,
            a & (b & (c & (d & e)))
        ),
        (
            (((a << b) & c) & d) & e,
            a << (b & (c & (d & e)))
        ),
        (
            a & (b | c),
            a & (b | c)
        ),
    )

    expression_all_raise(
        ParseError,
        rearrange,
        a << b << c,
        a >> b >> c,
        a << b & c | d << e,
        a >> b & c | d >> e,
    )
