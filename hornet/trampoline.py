import functools


def trampoline(bouncing, *args, **kwargs):
    while bouncing:
        result = bouncing(*args, **kwargs)
        results, bouncing, args, kwargs = result
        yield from results


zero = iter(())


def unit(item):
    yield item


def land(*args, **kwargs):
    return zero, None, args, kwargs


def throw(function, thrown, *args, **kwargs):
    return unit(thrown), function, args, kwargs


def bounce(function, *args, **kwargs):
    return zero, function, args, kwargs


def bouncy(f):
    return functools.partial(bounce, f)
