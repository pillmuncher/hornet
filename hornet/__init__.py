#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


def __load__():

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


__load__()

del __load__


from hornet.system import *


__all__ = [
    '_',
    'append',
    'arithmetic_equal',
    'arithmetic_not_equal',
    'atomic',
    'call',
    'cut',
    'equal',
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
    'real',
    'repeat',
    'reverse',
    'select',
    'smaller',
    'throw',
    'transpose',
    'true',
    'unequal',
    'univ',
    'var',
    'write',
    'writeln',
    'Database',
    'build_term',
    'expand_term',
    'pyfunc',
    'UnificationFailed',
    '_C_',
]
