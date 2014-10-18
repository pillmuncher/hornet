#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import functools
import importlib.abc
import importlib.machinery
import sys
import types

import hornet.expressions


class SymbolsFactory(types.ModuleType):
    __all__ = []
    __file__ = __file__
    __getattr__ = staticmethod(functools.lru_cache()(hornet.expressions.Name))


class SymbolsImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):

    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'hornet.symbols':
            return importlib.machinery.ModuleSpec(fullname, self)

    def create_module(self, spec):
        return sys.modules.setdefault(spec.name, SymbolsFactory(spec.name))

    def exec_module(self, module):
        pass


sys.meta_path.insert(0, SymbolsImporter())


from hornet.terms import *
from hornet.system import *
