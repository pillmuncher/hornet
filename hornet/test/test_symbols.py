#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.0.2a'
__date__ = '2014-08-20'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import nose

import ast

from hornet.test import *


def test_symbols_module():

    from hornet.expressions import Name
    from hornet.symbols import x

    ast_eq(x, Name('x'))


#def test_strings_module():

    #from hornet.strings import x

    #assert x == 'x'


if __name__ == '__main__':
    nose.main()
