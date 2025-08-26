# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from toolz.functoolz import identity

from hornet.expressions import mlift

from . import ast_eq, expression_all, expression_all_raise


def test_rearrange():
    from hornet.operators import ParseError, rearrange
    from hornet.symbols import a, b, c, d, e

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
