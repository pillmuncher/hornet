#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from hornet import *

from hornet.symbols import (
    queens, solution, noattack, template, Others,
    X, Y, Z, X1, Y1, Y2, Y3, Y4, Y5, Y6, Y7, Y8, S, Ys, Zs,
)


def main():

    db = Database()

    db.tell(

        queens(S) <<
            template(S) &
            solution(S, _),

        solution([_/Y], Ys) << select(Y, [1, 2, 3, 4, 5, 6, 7, 8], Ys),

        solution([X/Y|Others], Ys) <<
            solution(Others, Zs) &
            select(Y, Zs, Ys) &
            noattack(X/Y, Others),

        noattack(_,[]),

        noattack(X/Y,[X1/Y1|Others]) <<
            arithemtic_not_equal(Y, Y1) &
            arithemtic_not_equal(Y1 - Y, X1 - X) &
            arithemtic_not_equal(Y1 - Y, X - X1) &
            noattack(X/Y,Others),

        template([1/Y1, 2/Y2, 3/Y3, 4/Y4, 5/Y5, 6/Y6, 7/Y7, 8/Y8]),

    )

    for subst in db.ask(queens(S)):
        print(subst[S])
        #if not input('more?').lower().strip().startswith('y'):
            #break


if __name__ == '__main__':
    main()
