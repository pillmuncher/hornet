# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.5a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from functools import wraps


def trampoline(bounce, *args, **kwargs):
    while bounce:
        result, bounce, args, kwargs = bounce(*args, **kwargs)
        yield from result

def tailcall(function):
    @wraps(function)
    def launch(*args, **kwargs):
        return (), function, args, kwargs
    return launch


def emit(*values):
    def emitter(cont, *args, **kwargs):
        return values, cont, args, kwargs
    return emitter


def abort(*args, **kwargs):
    return (), None, args, kwargs
