#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.5a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from functools import wraps


def tco(function):
    @wraps(function)
    def launch(*args, **kwargs):
        return function, (), args, kwargs
    return launch

def abort(*args, **kwargs):
    return None, (), args, kwargs

def emit(cont, *args, **kwargs):
    return cont, [None], args, kwargs

def trampoline(bounce, *args, **kwargs):
    while bounce:
        bounce, result, args, kwargs = bounce(*args, **kwargs)
        yield from result
