from functools import partial, wraps
from itertools import count
from operator import attrgetter, itemgetter
from string import ascii_uppercase
import re


def compose(f, *gs):
    def composed(x):
        x = f(x)
        for g in gs:
            x = g(x)
        return x
    return composed


noop = lambda *a, **k: None
flip = lambda f: lambda *a: f(*reversed(a))
identity = lambda x: x


def as_method(cls, wrapped=None):
    return wraps(wrapped or cls)(lambda *a, **k: cls(*a, **k))


next_suffix = map('_{}'.format, count()).__next__


comma_separated = compose(partial(map, str), ', '.join)
amp_separated = compose(partial(map, str), ' & '.join)


def params_format(params):
    params = tuple(params)
    return '({})'.format(comma_separated(params)) if params else ''


def body_format(body):
    body = list(body)
    return ' << {}'.format(amp_separated(body)) if body else ''


is_var_name = compose(itemgetter(0), set('_' + ascii_uppercase).__contains__)
is_special_name = compose(re.compile(pattern='__(\w|_)+__').match, bool)


first_param = compose(attrgetter('params'), itemgetter(0))
second_param = compose(attrgetter('params'), itemgetter(1))

first_goal = compose(attrgetter('goals'), itemgetter(0))
second_goal = compose(attrgetter('goals'), itemgetter(1))
