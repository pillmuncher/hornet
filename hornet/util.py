#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from functools import partial, wraps, reduce as foldl
from inspect import signature, Signature
from itertools import chain, tee, zip_longest


noop = lambda *a, **k: None
wrap = lambda f: wraps(f)(lambda *a, **k: f(*a, **k))
flip = lambda f: wraps(f)(lambda *a: f(*reversed(a)))

identity = lambda x: x          # AKA: the I combinator
const = lambda x: lambda _: x   # AKA: the K combinator

first_arg = lambda x, *a, **k: x


def compose(*fs):

    # make me monoidal:
    #if not fs:
        #return identity

    f, *gs = fs

    def composed(*a, **k):
        x = f(*a, **k)
        for g in gs:
            x = g(x)
        return x

    return composed


rcompose = flip(compose)
compose2 = lambda f, g: lambda *a, **k: g(f(*a, **k))
rcompose2 = lambda f, g: lambda *a, **k: f(g(*a, **k))


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


rpartial = lambda f, *args, **kwargs: partial(flip(f), *args, **kwargs)


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


def coroutine(generator=None, *, clean_exit=True):

    if generator is None:
        return partial(coroutine, clean_exit=clean_exit)

    @wraps(generator)
    def starter(*args, **kwargs):
        @wraps(generator)
        def run():
            yield from generator(*args, **kwargs)
            if clean_exit:
                yield
        running = run()
        running.send(None)
        return running

    return starter


def receive_missing_args(procedure):

    @coroutine
    @wraps(procedure)
    def receiver(*args, **kwargs):
        sig = signature(procedure)
        ba = sig.bind_partial(*args, **kwargs)
        for name in sig.parameters:
            if name not in ba.arguments:
                ba.arguments[name] = (yield)
        procedure(*ba.args, **ba.kwargs)

    return receiver
