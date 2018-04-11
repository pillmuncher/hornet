r!/ usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import functools


def trampoline(bouncing, *args, **kwargs):
    while bouncing:
        bouncing, result, args, kwargs = bouncing(*args, **kwargs)
        yield from result


def abort(*args, **kwargs):
    return None, (), args, kwargs


def emit(cont, *args, _=None, **kwargs):
    return cont, [_], args, kwargs


def bounce(cont, *args, **kwargs):
    return cont, (), args, kwargs


def tco(function):
    return functools.partial(bounce, function)
