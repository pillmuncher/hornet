#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from functools import partial, wraps, reduce as foldl
from itertools import chain, count, tee, zip_longest


def noop(*a, **k):
    return None


def wrap(f):
    return wraps(f)(lambda *a, **k: f(*a, **k))


def flip(f):
    return wraps(f)(lambda *a: f(*reversed(a)))


def increment(x):
    return x + 1


def decrement(x):
    return x - 1


def identity(x):
    return x          # AKA: the I combinator


def const(x):
    return lambda _: x   # AKA: the K combinator


def first_arg(x, *a, **k):
    return x


def tabulate(function, start=0):
    "Return function(0), function(1), ..."
    return map(function, count(start))


def compose(*fs):

    # make me monoidal:
    # if not fs:
        # return identity

    f, *gs = fs

    def composed(*a, **k):
        x = f(*a, **k)
        for g in gs:
            x = g(x)
        return x

    return composed


rcompose = flip(compose)


def compose2(f, g): return lambda *a, **k: g(f(*a, **k))


def rcompose2(f, g): return lambda *a, **k: f(g(*a, **k))


_sentinel = object()


def foldr(func, seq, start=_sentinel):
    if start is _sentinel:
        return foldl(flip(func), reversed(seq))
    return foldl(flip(func), reversed(seq), start)


def rfoldl(func, seq, start=_sentinel):
    if start is _sentinel:
        return foldl(flip(func), seq)
    return foldl(flip(func), seq, start)


def rfoldr(func, seq, start=_sentinel):
    if start is _sentinel:
        return foldl(func, reversed(seq))
    return foldl(func, reversed(seq), start)


def rpartial(f, *args, **kwargs):
    return partial(flip(f), *args, **kwargs)


def pairwise(iterable, *, rotate=False, fillvalue=_sentinel):
    if rotate and fillvalue is not _sentinel:
        raise ValueError(
            'The parameters rotate and fillvalue are mutually exclusive.')
    a, b = tee(iterable)
    last = next(b, None)
    if rotate:
        return zip(a, chain(b, [last]))
    elif fillvalue is _sentinel:
        return zip(a, b)
    else:
        return zip_longest(a, b, fillvalue=fillvalue)


def qualname(fullname):

    name = fullname.rsplit('.', 1).pop()

    def name_setter(func):
        func.__name__ = name
        func.__qualname__ = fullname
        return func

    return name_setter


def rotate(iterable):
    iterable = iter(iterable)
    tmp = next(iterable)
    yield from iterable
    yield tmp


def splitpairs(iterable):
    iterable = iter(iterable)
    for left in iterable:
        right = next(iterable)
        yield left, right
