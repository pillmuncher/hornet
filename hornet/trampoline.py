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
        bouncing, result, args, kwargs = bouncing(*args, **kwargs)
        yield from result


def land(*args, **kwargs):
    return None, (), args, kwargs


def throw(cont, result=None, *args, **kwargs):
    return cont, [result], args, kwargs


def bounce(cont, *args, **kwargs):
    return cont, (), args, kwargs


def bouncy(function):
    return functools.wraps(function)(functools.partial(bounce, function))