# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

import re as __re__
from functools import cache as __cache__

from .expressions import lift as __lift__
from .terms import Atom as __Atom__
from .terms import Variable as __Variable__
from .terms import Wildcard as __Wildcard__

__all__ = []

__scan__ = __re__.compile(
    r"""
    (?P<dunder>__.*__)       |   # matches dunder names
    (?P<wildcard>_)          |   # matches exactly "_"
    (?P<variable>[A-Z_].*)   |   # starts with uppercase or _
    (?P<atom>[a-z].*)            # starts with lowercase
    """,
    __re__.VERBOSE,
).fullmatch


@__cache__
@__lift__
def __getattr__(name: str) -> __Atom__ | __Variable__ | __Wildcard__:
    """
    Convert a string into a Term according to Prolog conventions:
      - "_" becomes the anonymous variable
      - strings starting with uppercase or "_" become Variables
      - strings starting with lowercase become Atoms
    """

    from .terms import WILDCARD, Atom, Variable

    if (m := __scan__(name)) is None:
        raise AttributeError(f"Invalid identifier: {name}")
    match m.lastgroup:
        case "wildcard":
            return WILDCARD
        case "variable":
            return Variable(name=name)
        case "atom":
            return Atom(name=name)
        case _:
            raise AttributeError(f"Invalid symbol name: {name}")
