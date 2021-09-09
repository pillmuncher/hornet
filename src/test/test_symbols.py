#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import pytest

from . import ast_eq


def test_symbols_module():

    from hornet.expressions import Name
    from hornet.symbols import x

    ast_eq(x, Name('x'))


if __name__ == '__main__':
    pytest.main()
