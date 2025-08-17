# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

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
