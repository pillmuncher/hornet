#!/usr/bin/env pytest
# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = "0.2.7"
__date__ = "2014-09-27"
__author__ = "Mick Krippendorf <m.krippendorf@freenet.de>"
__license__ = "MIT"


from . import ast_eq


def test_symbols_module():
    from hornet.expressions import Name
    from hornet.symbols import x  # type: ignore

    ast_eq(x, Name("x"))
