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
    fizzbuzz, word, show, divisible, W, Ws, N, N1, Max, D, S,
)


def main():

    db = Database()

    db.tell(

        fizzbuzz(N, Max) <<
            ~greater(N, Max) &
            findall(W, word(W, N), Ws) &
            show(N, Ws) &
            let(N1, N + 1) &
            fizzbuzz(N1, Max),

        word('fizz', N) << divisible(N, 3),
        word('buzz', N) << divisible(N, 5),
        word('blub', N) << divisible(N, 7),

        divisible(N, D) << let(0, N % D),

        show(N, Ws) <<
            equal(Ws, []) >> writeln(N) | join(Ws, S) & writeln(S),

    )

    try:
        for subst in db.ask(fizzbuzz(1, 1111)):
            break
    except RuntimeError:
        print('oops!')


if __name__ == '__main__':
    main()
