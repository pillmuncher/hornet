# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

import re as __re__
from functools import cache as __cache__

from .terms import BaseTerm as __BaseTerm__

__all__ = []

__scan__ = __re__.compile(
    r"""
    (?P<dunder>__.*__)       |   # matches dunder names
    (?P<atom>[a-z].*)        |   # starts with lowercase
    (?P<variable>[A-Z_].*)      # starts with uppercase or _
    """,
    __re__.VERBOSE,
).fullmatch


# @__cache__
def __getattr__(name: str) -> __BaseTerm__:
    """
    Convert a string into a Term according to Prolog conventions:
      - "_" becomes the anonymous variable
      - strings starting with uppercase or "_" become Variables
      - strings starting with lowercase become Atoms
    """
    from .terms import Atom as Atom
    from .terms import Variable as Variable

    if (m := __scan__(name)) is None:
        raise AttributeError(f"Invalid symbol name: {name}")
    match m.lastgroup:
        case "variable":
            return Variable(name=name)
        case "atom":
            return Atom(name=name)
        case _:
            raise AttributeError(f"Invalid symbol name: {name}")
