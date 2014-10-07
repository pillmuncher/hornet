#!/usr/bin/env python3
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
        results, bouncing, args, kwargs = bouncing(*args, **kwargs)
        yield from results


zero = iter(())


def unit(item):
    yield item


def land(*args, **kwargs):
    return zero, None, args, kwargs


def throw(thrown, function, *args, **kwargs):
    return unit(thrown), function, args, kwargs


def bounce(function, *args, **kwargs):
    return zero, function, args, kwargs


def bouncy(f):
    return functools.partial(bounce, f)
