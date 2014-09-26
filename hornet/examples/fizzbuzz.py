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


from hornet import *

from hornet.symbols import fizzbuzz, word, show, divisible, W, Ws, N, N1, Max
from hornet.symbols import D, S


def main():

    db = Database()

    db.assertz(

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
        for subst in db.query(fizzbuzz(1, 1000)):
            break
    except RuntimeError:
        print('oops!')


if __name__ == '__main__':
    main()
