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


def test_dcg_transformation():

    from hornet.expressions import promote, mcompose
    from hornet.operators import rearrange
    from hornet.dcg import dcg_expand, _C_

    from hornet.symbols import s, np, vp, _0, _1, _2, _3, _4, _5, _6, _7, _8
    from hornet.symbols import it_is, tell, me, it, aint, so, very, different
    from hornet.symbols import a, b, c, u, v, X

    ast_test_all(
        ast_eq,
        mcompose(rearrange, dcg_expand),
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
            s >> np(a) & vp(a, b),
            s(_0, _2) << np(a, _0, _1) & vp(a, b, _1, _2),
        ),
        (
            s >> a & b & c,
            s(_0, _3) << a(_0, _1) & b(_1, _2) & c(_2, _3),
        ),
        (
            it_is(X) >> [] & [],
            it_is(X, _0, _0),
        ),
        (
            it_is(X) >> [],
            it_is(X, _0, _0),
        ),
        (
            it_is(X) >> [] & so,
            it_is(X, _0, _1) <<
                so(_0, _1),
        ),
        (
            it_is(X) >> so & [],
            it_is(X, _0, _1) <<
                so(_0, _1),
        ),
        (
            it_is(X) >> [] & so & [],
            it_is(X, _0, _1) <<
                so(_0, _1),
        ),
        (
            it_is(X) >> tell & [] & so,
            it_is(X, _0, _2) <<
                tell(_0, _1) &
                so(_1, _2),
        ),
        (
            it_is(X) >> [tell],
            it_is(X, _0, _1) <<
                _C_(_0, tell, _1),
        ),
        (
            it_is(X) >> [tell, me],
            it_is(X, _0, _2) <<
                _C_(_0, tell, _1) &
                _C_(_1, me, _2),
        ),
        (
            it_is(X) >> [tell, me, it],
            it_is(X, _0, _3) <<
                _C_(_0, tell, _1) &
                _C_(_1, me, _2) &
                _C_(_2, it, _3),
        ),
        (
            it_is(X) >> [tell, me, it, aint],
            it_is(X, _0, _4) <<
                _C_(_0, tell, _1) &
                _C_(_1, me, _2) &
                _C_(_2, it, _3) &
                _C_(_3, aint, _4),
        ),
        (
            it_is(X) >> [tell, me, it, aint, so],
            it_is(X, _0, _5) <<
                _C_(_0, tell, _1) &
                _C_(_1, me, _2) &
                _C_(_2, it, _3) &
                _C_(_3, aint, _4) &
                _C_(_4, so, _5),
        ),
        (
            (it_is(X) & [c, tell, me, it]) >>
                [aint, so, a, b],
            it_is(X, _0, _8) <<
                _C_(_0, aint, _1) &
                _C_(_1, so, _2) &
                _C_(_2, a, _3) &
                _C_(_3, b, _4) &
                _C_(_8, c, _7) &
                _C_(_7, tell, _6) &
                _C_(_6, me, _5) &
                _C_(_5, it, _4),
        ),
        (
            (it_is(X) & [tell, me]) >>
                [very, different],
            it_is(X, _0, _4) <<
                _C_(_0, very, _1) &
                _C_(_1, different, _2) &
                _C_(_4, tell, _3) &
                _C_(_3, me, _2),
        ),
        (
            it_is(X) & [me] >>
                it & [very] & so,
            it_is(X, _0, _4) <<
                it(_0, _1) &
                _C_(_1, very, _2) &
                so(_2, _3) &
                _C_(_4, me, _3),
        ),
        (
            it_is(X) & [me] >>
                it & [very] & so & [different],
            it_is(X, _0, _5) <<
                it(_0, _1) &
                _C_(_1, very, _2) &
                so(_2, _3) &
                _C_(_3, different, _4) &
                _C_(_5, me, _4),
        ),
        (
            it_is(X) & [me] >>
                promote([it]) & [very] & [tell] & [different] & so,
            it_is(X, _0, _6) <<
                _C_(_0, it, _1) &
                _C_(_1, very, _2) &
                _C_(_2, tell, _3) &
                _C_(_3, different, _4) &
                so(_4, _5) &
                _C_(_6, me, _5),
        ),
        (
            it_is(X) & [me] >>
                it & [very, tell] & so & [different],
            it_is(X, _0, _6) <<
                it(_0, _1) &
                _C_(_1, very, _2) &
                _C_(_2, tell, _3) &
                so(_3, _4) &
                _C_(_4, different, _5) &
                _C_(_6, me, _5),
        ),
        (
            it_is(X) >> {tell(X)} & me,
            it_is(X, _0, _1) <<
                tell(X) &
                me(_0, _1),
        ),
    )
