# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

from . import ast_eq


def test_symbols_module():
    from hornet.expressions import Name
    from hornet.symbols import x

    ast_eq(x, Name("x"))
