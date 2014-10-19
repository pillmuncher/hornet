#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


def _install_symbols_module():

    import sys

    from functools import lru_cache
    from importlib.abc import MetaPathFinder, Loader
    from importlib.machinery import  ModuleSpec
    from types import ModuleType

    from hornet.expressions import Name

    class SymbolsFactory(ModuleType):
        __all__ = []
        __file__ = __file__
        __getattr__ = staticmethod(lru_cache()(Name))

    class SymbolsImporter(MetaPathFinder, Loader):

        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'hornet.symbols':
                return ModuleSpec(fullname, self)

        def create_module(self, spec):
            return sys.modules.setdefault(spec.name, SymbolsFactory(spec.name))

        def exec_module(self, module):
            pass

    sys.meta_path.insert(0, SymbolsImporter())


_install_symbols_module()

del _install_symbols_module


from hornet.system import *


__all__ = [
    'Database',
    'UnificationFailed',
    '_',
    '_C_',
    'append',
    'arithmetic_equal',
    'arithmetic_not_equal',
    'atomic',
    'build_term',
    'call',
    'cut',
    'equal',
    'expand_term',
    'fail',
    'findall',
    'greater',
    'ignore',
    'integer',
    'join',
    'length',
    'let',
    'listing',
    'lwriteln',
    'maplist',
    'member',
    'nl',
    'numeric',
    'once',
    'pyfunc',
    'real',
    'repeat',
    'reverse',
    'select',
    'smaller',
    'throw',
    'transpose',
    'true',
    'unequal',
    'unify',
    'univ',
    'var',
    'write',
    'writeln',
]
