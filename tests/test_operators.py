#!/usr/bin/env pytest
# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


from . import expression_all, expression_all_raise, ast_eq
from toolz.functoolz import identity
from hornet.expressions import mlift


def test_rearrange():
    from hornet.operators import rearrange, ParseError

    from hornet.symbols import a, b, c, d, e  # type: ignore

    expression_all(
        ast_eq,
        rearrange,
        mlift(identity),
        (a, a),
        ((((a & b) & c) & d) & e, a & (b & (c & (d & e)))),
        ((((a << b) & c) & d) & e, a << (b & (c & (d & e)))),
        (a & (b | c), a & (b | c)),
    )

    expression_all_raise(
        ParseError,
        rearrange,
        a << b << c,
        a >> b >> c,
        a << b & c | d << e,
        a >> b & c | d >> e,
    )
