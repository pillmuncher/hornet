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
    queens, solution, noattack, Rest, S, X, Y, X1, Y1, Xs, Ys, Y0s, Qs,
)


def main():

    db = Database()

    nums = list(range(1, 9))

    db.tell(

        queens(S) <<
            solution(nums, nums, [], S),

        solution([X|Xs], Y0s, Qs, [X/Y|S]) <<
            select(Y, Y0s, Ys) &
            noattack(X/Y, Qs) &
            solution(Xs, Ys, [X/Y|Qs], S),
        solution([], _, _, []),

        noattack(X/Y, [X1/Y1|Rest]) <<
            arithmetic_not_equal(Y, Y1) &
            arithmetic_not_equal(Y1 - Y, X1 - X) &
            arithmetic_not_equal(Y1 - Y, X - X1) &
            noattack(X/Y, Rest),
        noattack(_, []),

    )

    for subst in db.ask(queens(S)):
        print(subst[S])
        #pass
        #break
        #if not input('more? ').lower().strip().startswith('y'):
            #break


if __name__ == '__main__':
    main()
