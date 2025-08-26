# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from itertools import count

from .combinators import Goal
from .symbols import (
    append,
    arithmetic_equal,
    arithmetic_not_equal,
    atomic,
    call,
    cut,
    equal,
    fail,
    findall,
    greater,
    ignore,
    integer,
    join,
    length,
    let,
    listing,
    lwriteln,
    maplist,
    member,
    nl,
    nonvar,
    numeric,
    once,
    real,
    repeat,
    reverse,
    select,
    smaller,
    tail,
    throw,
    transpose,
    true,
    unequal,
    univ,
    write,
    writeln,
)
from .terms import Term, Variable

__all__ = (
    "append",
    "arithmetic_equal",
    "arithmetic_not_equal",
    "atomic",
    "call",
    "cut",
    "equal",
    "fail",
    "findall",
    "greater",
    "ignore",
    "integer",
    "join",
    "length",
    "let",
    "listing",
    "lwriteln",
    "maplist",
    "member",
    "nl",
    "nonvar",
    "numeric",
    "once",
    "real",
    "repeat",
    "reverse",
    "select",
    "smaller",
    "tail",
    "throw",
    "transpose",
    "true",
    "unequal",
    "univ",
    "write",
    "writeln",
)


def var(name: str, _var_counter=count()) -> Variable:
    return Variable(f"{name}{next(_var_counter)}")


# Not sure yet if these are needed:
@dataclass(frozen=True, slots=True)
class Predicate(Term):
    value: Goal


def predicate(pred: Goal) -> Term:
    return Predicate(pred)
