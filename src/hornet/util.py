# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.5a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from functools import partial, reduce as foldl
from itertools import count, tee, zip_longest


from toolz.functoolz import flip


decrement = (-1).__add__


def noop(*a, **k):
    return None


def const(x):
    "The K combinator"
    return lambda _: x


def first_arg(x, *a, **k):
    return x


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


def split_pairs(iterable):
    iterable = iter(iterable)
    for left in iterable:
        right = next(iterable)
        yield left, right


def install_symbols_module(name, factory):

    import sys

    from functools import lru_cache
    from importlib.abc import MetaPathFinder, Loader
    from importlib.machinery import ModuleSpec
    from types import ModuleType

    class SymbolsModule(ModuleType):
        __all__ = []
        __file__ = None  # needed so nose doesn't bark at us
        __getattr__ = staticmethod(lru_cache()(factory))

    class SymbolsImporter(MetaPathFinder, Loader):

        exec_module = noop

        def find_spec(self, fullname, path=None, target=None):
            if fullname == name:
                return ModuleSpec(fullname, self)

        def create_module(self, spec):
            return sys.modules.setdefault(spec.name, SymbolsModule(spec.name))


    sys.meta_path.insert(0, SymbolsImporter())
