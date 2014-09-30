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
    queens, solution, noattack, Rest, Nums, S, X, Y, X1, Y1, Xs, Ys, Y1s, Qs,
)


def main():

    db = Database()

    db.tell(

        queens(S) <<
            equal([1, 2, 3, 4, 5, 6, 7, 8], Nums) &
            solution(Nums, Nums, [], Qs) &
            reverse(Qs, S),

        solution([X|Xs], Ys, Qs, S) <<
            select(Y, Ys, Y1s) &
            noattack(X/Y, Qs) &
            solution(Xs, Y1s, [X/Y|Qs], S),
        solution([], [], S, S),

        noattack(X/Y, [X1/Y1|Rest]) <<
            arithemtic_not_equal(Y, Y1) &
            arithemtic_not_equal(Y1 - Y, X1 - X) &
            arithemtic_not_equal(Y1 - Y, X - X1) &
            noattack(X/Y, Rest),
        noattack(_, []),

    )

    for subst in db.ask(queens(S)):
        print(subst[S])
        #if not input('more?').lower().strip().startswith('y'):
            #break


if __name__ == '__main__':
    main()
