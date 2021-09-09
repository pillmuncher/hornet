#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from hornet import Database, append

from hornet.symbols import (
    L1, L2
)


def main():

    db = Database()

    for subst in db.ask(append(L1, L2, [1, 2, 3, 4, 5])):
        print(subst[L1], "+", subst[L2])


if __name__ == '__main__':
    main()
