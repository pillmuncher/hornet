# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from . import ast_eq


def test_symbols_module():
    from hornet.expressions import Atom
    from hornet.symbols import x

    ast_eq(x, Atom("x"))
