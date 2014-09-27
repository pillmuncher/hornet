#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.0.2a'
__date__ = '2014-08-20'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from hornet import *

from hornet.symbols import A, B, C, C1, G, H, Q, U, V, W, X, Y, Z, cos, d, exp
from hornet.symbols import log, simp, sin, x, y, z


def diff_rules(db):

    db.assertz(

        d(X, X, 1) << cut,

        d(C, X, 0) << atomic(C) & cut,

        d(U + V, X, A + B) <<
            d(U, X, A) &
            d(V, X, B) & cut,

        d(U - V, X, A - B) <<
            d(U, X, A) &
            d(V, X, B) & cut,

        d(C * U, X, C * A) <<
            atomic(C) &
            unequal(C, X) &
            d(U, X, A) & cut,

        d(U * V, X, B * U + A * V) <<
            d(U, X, A) &
            d(V, X, B) & cut,

        d(U / V, X, (A * V - B * U) / (V * V)) <<
            d(U, X, A) &
            d(V, X, B) & cut,

        d(U ** C, X, C * A * U ** (C - 1)) <<
            atomic(C) &
            unequal(C, X) &
            d(U, X, A) & cut,

        d(U ** -C, X, -C * A * U ** (-C - 1)) <<
            d(U, X, A) & cut,

        d(U ** C, X, C * A * U ** (C - 1)) <<
            equal(C, -C1) &
            atomic(C1) &
            unequal(C1, X) &
            d(U, X, A) & cut,

        d(sin(W), X, Z * cos(W)) <<
            d(W, X, Z) & cut,

        d(exp(W), X, Z * exp(W)) <<
            d(W, X, Z) & cut,

        d(log(W), X, Z / W) <<
            d(W, X, Z) & cut,

        d(cos(W), X,  -(Z * sin(W))) <<
            d(W, X, Z) & cut,

    )


def simp_rules(db):

    db.assertz(

        simp(X, X) <<
            atomic(X) & cut,

        simp(--X, Y) <<
            simp(X, Y) & cut,

        simp(-A + -B, C) <<
            simp(A + B, C1) &
            simp(-C1, C) & cut,

        simp(-A + B, C) <<
            simp(B - A, C) & cut,

        simp(A + -B, C) <<
            simp(A - B, C) & cut,

        simp(-A - -B, C) <<
            simp(B - A, C) & cut,

        simp(-A - B, C) <<
            simp(-A + -B, C) & cut,

        simp(A - -B, C) <<
            simp(A + B, C) & cut,

        simp(-A * -B, C) <<
            simp(A * B, C) & cut,

        simp(-A * B, C) <<
            simp(A * B, C1) &
            simp(-C1, C) & cut,

        simp(A * -B, -C) <<
            simp(A * B, C1) &
            simp(-C1, C) & cut,

        simp(X + 0, Y) <<
            simp(X, Y) & cut,

        simp(0 + X, Y) <<
            simp(X, Y) & cut,

        simp(X - 0, Y) <<
            simp(X, Y) & cut,

        simp(0 - X, -Y) <<
            simp(X, Y) & cut,

        simp(A + B, C) <<
            numeric(A) &
            numeric(B) &
            let(C, A + B) & cut,

        simp(A - A, 0) << cut,

        simp(A - B, C) <<
            numeric(A) &
            numeric(B) &
            let(C, A - B) & cut,

        simp(X * 0, 0) << cut,

        simp(0 * X, 0) << cut,

        simp(0 / X, 0) << cut,

        simp(X * 1, X) << cut,

        simp(1 * X, X) << cut,

        simp(X / 1, X) << cut,

        simp(X / X, 1) << cut,

        simp(X ** 1, X) << cut,

        simp(X ** 0, 1) << cut,

        simp(A + A + B, Y) <<
            simp(2 * A + B, Y) & cut,

        simp(A + B + A, 2 * A + B) <<
            simp(2 * A + B, Y) & cut,

        simp(B + A + A, 2 * A + B) <<
            simp(2 * A + B, Y) & cut,

        simp(A + (B + C), Q) <<
            simp(A + B + C, Q) & cut,

        simp(A * (B * C), Q) <<
            simp(A * B * C, Q) & cut,

        simp(X * X, X ** 2) << cut,

        simp(X * X ** A, Y) <<
            simp(X ** (A + 1), Y) & cut,

        simp(X ** A * X, Y) <<
            simp(X ** (A + 1), Y) & cut,

        simp(A * B + A * C, Y) <<
            simp(A * (B + C), Y) & cut,

        simp(A * B + C * A, Y) <<
            simp(A * (B + C), Y) & cut,

        simp(A * B + B * C, Y) <<
            simp(B * (A + C), Y) & cut,

        simp(A * B + C * B, Y) <<
            simp(B * (A + C), Y) & cut,

        simp(A * (A + B), A ** 2 + A * Y) <<
            simp(B, Y) & cut,

        simp(A * (B + A), A ** 2 + A * Y) <<
            simp(B, Y) & cut,

        simp(A * B, X) <<
            numeric(A) &
            numeric(B) &
            let(X, A * B) & cut,

        simp(A * X + B * X, Z) <<
            unequal(A, X) &
            unequal(B, X) &
            simp((A + B) * X, Z) & cut,

        simp((A + B) * (A - B), X ** 2 - Y ** 2) <<
            simp(A, X) &
            simp(B, Y) & cut,

        simp(X ** A / X ** B, X ** C) <<
            numeric(A) &
            numeric(B) &
            let(C, A - B) & cut,

        simp(A / B, X) <<
            numeric(A) &
            numeric(B) &
            let(X, A / B) & cut,

        simp(A ** B, X) <<
            numeric(A) &
            numeric(B) &
            let(X, A ** B) & cut,

        simp(A + B, C) <<
            simp(A, X) &
            simp(B, Y) &
            unequal([A, B], [X, Y]) &
            simp(X + Y, C) & cut,

        simp(A - B, C) <<
            simp(A, X) &
            simp(B, Y) &
            unequal([A, B], [X, Y]) &
            simp(X - Y, C) & cut,

        simp(A * B, C) <<
            simp(A, X) &
            simp(B, Y) &
            unequal([A, B], [X, Y]) &
            simp(X * Y, C) & cut,

        simp(A / B, C) <<
            simp(A, X) &
            simp(B, Y) &
            unequal([A, B], [X, Y]) &
            simp(X / Y, C) & cut,

        simp(X ** A, C) <<
            simp(A, B) &
            unequal(A, B) &
            simp(X ** B, C) & cut,

        simp(X, X) << cut,

    )


def diff_test(db):
    F = x ** -3 + 2 * x ** 2 + 7 * (x + 9)
    #F = (2 + x) ** 3
    #F = (x * y) * (x + 3)
    print(build_term(F))

    for subst in db.query(d(F, x, G) & simp(G, H)):
        print(subst[G])
        print(subst[H])
    #for subst in db.query(listing(d)):
        #print('Yes.')
        #break
    #else:
        #print('No.')
    #print()


def main():
    db = Database()
    diff_rules(db)
    simp_rules(db)
    diff_test(db)


if __name__ == '__main__':
    main()
