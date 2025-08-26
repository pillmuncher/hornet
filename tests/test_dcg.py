# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from . import ast_eq, expression_all


def test_dcg_transformation():
    from toolz.functoolz import compose

    from hornet.dcg import _C_, expand
    from hornet.expressions import mcompose, promote, unit
    from hornet.operators import rearrange
    from hornet.symbols import (
        X,
        _0,
        _1,
        _2,
        _3,
        _4,
        _5,
        _6,
        _7,
        _8,
        a,
        b,
        c,
        d,
        e,
        f,
        g,
        h,
        np,
        s,
        vp,
        x,
        y,
        z,
    )

    expression_all(
        ast_eq,
        compose(mcompose(expand, rearrange), unit),
        rearrange,
        (
            s >> vp,
            s(_0, _1) << vp(_0, _1),
        ),
        (
            s >> np & vp,
            s(_0, _2) << np(_0, _1) & vp(_1, _2),
        ),
        (
            s >> np(x) & vp(x, y),
            s(_0, _2) << np(x, _0, _1) & vp(x, y, _1, _2),
        ),
        (
            s >> x & y & z,
            s(_0, _3) << x(_0, _1) & y(_1, _2) & z(_2, _3),
        ),
        (
            a(X) >> [] & [],
            a(X, _0, _0),
        ),
        (
            a(X) >> [],
            a(X, _0, _0),
        ),
        (
            a(X) >> [] & f,
            a(X, _0, _1) << f(_0, _1),
        ),
        (
            a(X) >> f & [],
            a(X, _0, _1) << f(_0, _1),
        ),
        (
            a(X) >> [] & f & [],
            a(X, _0, _1) << f(_0, _1),
        ),
        (
            a(X) >> b & [] & f,
            a(X, _0, _2) << b(_0, _1) & f(_1, _2),
        ),
        (
            a(X) >> [b],
            a(X, _0, _1) << _C_(_0, b, _1),
        ),
        (
            a(X) >> [b, c],
            a(X, _0, _2) << _C_(_0, b, _1) & _C_(_1, c, _2),
        ),
        (
            a(X) >> [b, c, d],
            a(X, _0, _3) << _C_(_0, b, _1) & _C_(_1, c, _2) & _C_(_2, d, _3),
        ),
        (
            a(X) >> [b, c, d, e],
            a(X, _0, _4) << _C_(_0, b, _1)
            & _C_(_1, c, _2)
            & _C_(_2, d, _3)
            & _C_(_3, e, _4),
        ),
        (
            a(X) >> [b, c, d, e, f],
            a(X, _0, _5) << _C_(_0, b, _1)
            & _C_(_1, c, _2)
            & _C_(_2, d, _3)
            & _C_(_3, e, _4)
            & _C_(_4, f, _5),
        ),
        (
            (a(X) & [z, b, c, d]) >> [e, f, x, y],
            a(X, _0, _8) << _C_(_0, e, _1)
            & _C_(_1, f, _2)
            & _C_(_2, x, _3)
            & _C_(_3, y, _4)
            & _C_(_8, z, _7)
            & _C_(_7, b, _6)
            & _C_(_6, c, _5)
            & _C_(_5, d, _4),
        ),
        (
            (a(X) & [b, c]) >> [g, h],
            a(X, _0, _4) << _C_(_0, g, _1)
            & _C_(_1, h, _2)
            & _C_(_4, b, _3)
            & _C_(_3, c, _2),
        ),
        (
            a(X) & [c] >> d & [g] & f,
            a(X, _0, _4) << d(_0, _1) & _C_(_1, g, _2) & f(_2, _3) & _C_(_4, c, _3),
        ),
        (
            a(X) & [c] >> d & [g] & f & [h],
            a(X, _0, _5) << d(_0, _1)
            & _C_(_1, g, _2)
            & f(_2, _3)
            & _C_(_3, h, _4)
            & _C_(_5, c, _4),
        ),
        (
            a(X) & [c] >> promote([d]) & [g] & [b] & [h] & f,
            a(X, _0, _6) << _C_(_0, d, _1)
            & _C_(_1, g, _2)
            & _C_(_2, b, _3)
            & _C_(_3, h, _4)
            & f(_4, _5)
            & _C_(_6, c, _5),
        ),
        (
            a(X) & [c] >> d & [g, b] & f & [h],
            a(X, _0, _6) << d(_0, _1)
            & _C_(_1, g, _2)
            & _C_(_2, b, _3)
            & f(_3, _4)
            & _C_(_4, h, _5)
            & _C_(_6, c, _5),
        ),
        (
            a(X) >> {b(X)} & c,
            a(X, _0, _1) << b(X) & c(_0, _1),
        ),
    )
