#!/bin/env python3
# -*- coding: utf-8 -*-


__all__ = ['include', 'MetaTOS']


import warnings

from itertools import combinations


class OverridingError(NameError):
    pass


class OverridingWarning(Warning):
    pass


class Super:
    # this is needed to fix a shortcoming of unbound super objects,
    # i.e. this is how the unbound version of super should work

    def __init__(self, thisclass):
        self.__thisclass__ = thisclass

    def __get__(self, obj, objcls):
        return super(self.__thisclass__, obj or objcls)


def set_super(cls, name):
    setattr(cls, '_{}__super'.format(name), Super(cls))


class Namespace(dict):

    "A named dictionary containing the attributes of a class and its ancestors"

    @classmethod
    def from_cls(klass, cls):
        mro = cls.__mro__[:-1:-1]  # all except object
        dic = merge(subc.__dict__ for subc in mro)
        return klass(cls.__name__, dic)

    def __init__(self, name, attrs):
        self.__name__ = name
        self.update(attrs)


def merge(dicts):
    """Merge a sequence of dictionaries. In case of name clashes,
    the last dict in the sequence wins."""
    return {k:v for d in dicts for k, v in d.items()}


class MetaTOS(type):
    "The metaclass of the Trait Object System"

    def __new__(mcl, name, bases, dic):
        if len(bases) > 1:
            raise TypeError(
                'Multiple inheritance of bases {} is forbidden for TOS classes'
                .format(bases)
            )
        cls = mcl.__super.__new__(mcl, name, bases, dic)
        set_super(cls, name)
        return cls


set_super(MetaTOS, 'MetaTOS')


def check_overridden(namespaces, exclude=frozenset(), raise_='error'):
    "Raise an OverridingError for common names not in the exclude set"
    for n1, n2 in combinations(namespaces, r=2):
        common = n1.keys() & n2
        if not common:
            continue
        common -= exclude
        if common:
            msg = '{} overrides names in {}: {}'.format(
                n1.__name__, n2.__name__, common)
            if raise_ == 'error':
                raise OverridingError(msg)
            elif raise_ == 'warning':
                warnings.warn(msg, OverridingWarning, stacklevel=2)


known_metas = [MetaTOS]


def get_right_meta(metatos, bases):
    # there is only one base because of the single-inheritance constraint
    meta = type(bases[0])
    if meta is type:  # is a builtin meta
        return metatos
    elif issubclass(meta, known_metas):
        return meta
    # meta is independent from all known_metas, make a new one with
    # __new__ method coming from MetaTOS
    newmeta = type(
        '_TOS' + meta.__name__, (meta,), dict(__new__=metatos.__new__))
    set_super(newmeta, metatos.__name__)
    known_metas.append(newmeta)
    return newmeta


exclude_attrs = set('__doc__ __module__ __dict__ __weakref__'.split()).union


def new(metatos, name, bases, attrs, traits):
    # traits as in Squeak take the precedence over the base class
    # but they are overridden by attributes in the class
    namespaces = [Namespace.from_cls(trait) for trait in traits]
    check_overridden(namespaces, exclude=exclude_attrs(attrs))
    meta = get_right_meta(metatos, bases)
    cls = meta(name, bases, merge(namespaces + [Namespace(name, attrs)]))
    cls.__traits__ = traits
    for t in traits:
        set_super(cls, t.__name__)
    return cls


def include(*traits, **kw):
    "Class decorator factory"
    metatos = kw.get('MetaTOS', MetaTOS)  # other kw free for future extensions
    def makecls(name, bases, dic):
        return new(metatos, name, bases, dic, traits)
    makecls.__name__ = 'include_{}'.format('_'.join(m.__name__ for m in traits))
    return makecls
