# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


def trampoline(bounce, *args, **kwargs):
    while bounce:
        result, bounce, args, kwargs = bounce(*args, **kwargs)
        yield from result


def tailcall(function):
    return lambda *args, **kwargs: ((), function, args, kwargs)


def emit(*values):
    return lambda cont, *args, **kwargs: (values, cont, args, kwargs)


def abort(*args, **kwargs):
    return (), None, args, kwargs
