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
const = lambda x: lambda _: x   # AKA: the K combinator (with currying)

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


def method_of(cls):
    def attach(func):
        setattr(cls, func.__name__, func)
        return func
    return attach


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


def receive_missing_args(func):
    sig = signature(func)
    @wraps(func)
    @coroutine
    def receiver(*args, **kwargs):
        ba = sig.bind_partial(*args, **kwargs)
        for name in sig.parameters:
            if name not in ba.arguments:
                ba.arguments[name] = (yield)
        func(*ba.args, **ba.kwargs)
    return receiver


#from functools import singledispatch as _singledispatch
#class singledispatch:

    #def __init__(self, func):
        #self._dispatcher = _singledispatch(func)

    #def __call__(self, *args, **kwargs):
        #return self._dispatcher(*args, **kwargs)

    #def register(self, func):
        #param = next(iter(signature(func).parameters.values()))
        #return self._dispatcher.register(param.annotation)(func)


#_singledispatch_reg = {}

#def singledispatch(func):
    #funcname = func.__qualname__
    #if funcname in _singledispatch_reg:
        #param = next(iter(signature(func).parameters.values()))
        #_singledispatch_reg[funcname].register(param.annotation)(func)
    #else:
        #_singledispatch_reg[funcname] = _singledispatch(func)
    #return _singledispatch_reg[funcname]


#import abc


#class Trait(abc.ABCMeta):

    #traits = {}

    #def __new__(cls, cname, cbases, cdict, template):
        #new_trait = super(Trait, cls).__new__(cls, cname, cbases, cdict)
        #Trait.traits[new_trait] = template
        #return new_trait

    #def __init__(cls, cname, cbases, cdict, template):
        #super().__init__(cname, cbases, cdict)



#def trait(cls):
    #return Trait(cls.__name__, (), {}, cls)


#def with_traits(*traits):

    #assert all(isinstance(each, Trait) for each in traits)

    #def cls_with_traits(cls):

        #try:
        #except AttributeError:

        #__dict__ = {}

        #for each in traits:

            #try:
            #except AttributeError:
                #pass

            #trait_dict = dict(Trait.traits[each].__dict__)
            #trait_dict.pop('__slot__', None)

            #__dict__.update((k, v) for k, v in trait_dict.items() if k not in __slots__)

        #__dict__.update(cls.__dict__)

        #cls_init = cls.__init__

        #def __init__(self, *args, **kwargs):
            #for each in traits:
                #try:
                    #Trait.traits[each].__init__(self, kwargs)
                #except TypeError:
                    #pass
            #cls_init(self, *args, **kwargs)

        #__dict__['__init__'] = __init__
        #__dict__['__slots__'] = tuple(set(__slots__))

        #new_cls = type(cls.__name__, cls.__bases__, __dict__)
        #for each in traits:
            #each.register(new_cls)
        #return new_cls


    #return cls_with_traits


#@trait
#class HasEnvironment:


    #def __init__(self, kwargs):
        #self.env = kwargs.pop('env')


#@trait
#class HasInstanceName:


    #def __init__(self, kwargs):
        #self.Name = kwargs.pop('name')


#@trait
#class Resolvable:

    #def resolve(self, db):
        #raise NotImplementedError



