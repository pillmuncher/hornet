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


def test_builder():

    from hornet.expressions import bind
    from hornet.terms import build_term

    from hornet.symbols import _, f, g, h, a, b, c, d, e, X, Y, Z, s, vp, np, S0, S1

    print(build_term(a))
    print(build_term(f(a, b) << b & c & d))
    print(build_term(f(X, Y) << b(X) & c(Y) & d))
    print(build_term(f(X, Y) << b(X) & c(Y) & d(_, Z, [e, d | a])))
    print(build_term(f(X, Y) << b(X) & c(Y) & d(_, Z, [e, d | [a]])))
    print(build_term(a * (b + c)))
    #ast_test_all(
        #ast_eq,
        #build_term,
        #rearrange,
        #(
            #s >> vp,
            #s(S0, S1) << vp(S0, S1),
        #),
    #)


def test_resolver():

    from pprint import pprint

    from hornet import Database
    from hornet.symbols import _, f, g, h, a, b, c, d, e, X, Y, Z, U, V, W

    db = Database()
    db.assertz(
        a,
        f(a, b, c),
        f(a, a, a),
        f(c, b, a),
        f(X, Y, Z) << g(X, a) & h(Y, b) & c,
        g(X, X, Y),
        h(X) << g(X, a, _) | g(X, b, _),
    )
    pprint(db)

    for subst in db.query(g(a, Z, Z)):
        pprint(subst)

    for subst in db.query(g([a, b | c], Z, Z)):
        pprint(subst)

    for subst in db.query(f(X, Y, Z)):
        pprint(subst)

    for subst in db.query(h(X)):
        pprint(subst)

    for subst in db.query(~g(a, b, Y)):
        print(subst)
