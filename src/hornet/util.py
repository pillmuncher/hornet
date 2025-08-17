# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

from functools import partial
from functools import reduce as foldl
from itertools import count, tee, zip_longest
from typing import Any, Callable, Self

from toolz.functoolz import flip

decrement = (-1).__add__


def noop(*a, **k):
    return None


def const[T](x: T) -> Callable[..., T]:
    "The K combinator"
    return lambda *a, **k: x


def first_arg(x, *a, **k):
    return x


def compose(*fs):
    f, *gs = reversed(fs)

    def composed(*args, **kwargs):
        result = f(*args, **kwargs)
        for g in gs:
            result = g(result)
        return result

    return composed


def tabulate(function, start=0):
    "Return function(0), function(1), ..."
    return map(function, count(start))


_sentinel = object()


def foldr(func, seq, start=_sentinel):
    if start is _sentinel:
        return foldl(flip(func), reversed(seq))
    return foldl(flip(func), reversed(seq), start)


def rpartial(f, *args, **kwargs):
    return partial(flip(f), *args, **kwargs)


def pairwise(iterable, *, fillvalue=_sentinel):
    a, b = tee(iterable)
    next(b, None)  # advance b by one position
    if fillvalue is _sentinel:
        return zip(a, b)
    else:
        return zip_longest(a, b, fillvalue=fillvalue)


def rotate(iterable):
    iterable = iter(iterable)
    tmp = next(iterable)
    yield from iterable
    yield tmp


def split_pairs(iterable):
    iterable = iter(iterable)
    for left in iterable:
        right = next(iterable)
        yield left, right
