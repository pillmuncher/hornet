# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from functools import cache as __cache__

from .expressions import Expression as __Expression__

__all__ = []


@__cache__
def __getattr__(name: str) -> __Expression__:
    """
    Convert a string into a Term according to Prolog conventions:
      - "_" becomes the anonymous variable
      - strings starting with uppercase or "_" become Variables
      - strings starting with lowercase become Atoms
    """

    from . import terms
    from .expressions import promote

    match tuple(name):
        case "_", "_", *_, "_", "_":
            raise AttributeError(f"Invalid identifier: {name}")
        case ("_",):
            return __Expression__(promote(terms.AnonVariable()))
        case "_", *_:
            return __Expression__(promote(terms.Variable(name=name)))
        case h, *_ if h.isupper():
            return __Expression__(promote(terms.Variable(name=name)))
        case h, *_ if h.islower():
            return __Expression__(promote(terms.Atom(name=name)))
        case _:
            raise AttributeError(f"Invalid identifier: {name}")
