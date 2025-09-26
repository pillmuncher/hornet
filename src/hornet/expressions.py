# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from functools import partial, reduce
from itertools import count
from typing import Any, Callable, Iterator, cast

from toolz.functoolz import compose

from .states import StateGenerator, const, get_state, set_state, with_state
from .terms import (
    EMPTY,
    Add,
    Atom,
    BitAnd,
    BitOr,
    BitXor,
    Conjunction,
    Cons,
    Disjunction,
    Div,
    Empty,
    FloorDiv,
    Functor,
    HornetRule,
    Invert,
    LShift,
    MatchTerm,
    Mod,
    Mul,
    Pow,
    QueryTerm,
    RShift,
    Structure,
    Sub,
    Term,
    UAdd,
    USub,
    Variable,
    Wildcard,
)


@dataclass(frozen=True, slots=True)
class RuleExpression:
    term: Term


@dataclass(frozen=True, slots=True)
class DCG:
    expr: Expression[Atom | Functor]

    def when(self, *args) -> RuleExpression:
        head = self.expr.term
        body = Conjunction(*(promote(arg) for arg in args))
        new_head, new_body = dcg_expand(head, body)
        assert isinstance(new_head, MatchTerm)
        assert isinstance(new_body, QueryTerm)
        return RuleExpression(term=HornetRule(head=new_head, body=new_body))


@dataclass(frozen=True, slots=True)
class Expression[T: Term]:
    """
    An Expression object is a monadic wrapper around a Term.
    """

    term: T

    def __init__(self, term: T):
        object.__setattr__(self, "term", promote(term))

    def when(self, *args) -> RuleExpression:
        head = self.term
        body = Conjunction(*(promote(arg) for arg in args))
        assert isinstance(head, MatchTerm)
        assert isinstance(body, QueryTerm)
        return RuleExpression(HornetRule(head=head, body=body))

    def __repr__(self):
        return f"Expression({repr(self.term)})"

    def __str__(self):
        return repr(self.term)

    def __eq__(self, other):
        return isinstance(other, Expression) and self.term == other.term

    def __hash__(self) -> int:
        return hash((Expression, self.term))

    def __neg__(self):
        return expression(USub(promote(self)))

    def __pos__(self):
        return expression(UAdd(promote(self)))

    def __invert__(self):
        return expression(Invert(promote(self)))

    def __add__(self, other):
        return expression(Add(promote(self), promote(other)))

    def __radd__(self, other):
        return expression(Add(promote(other), promote(self)))

    def __sub__(self, other):
        return expression(Sub(promote(self), promote(other)))

    def __rsub__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __mul__(self, other):
        return expression(Mul(promote(self), promote(other)))

    def __rmul__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __truediv__(self, other):
        return expression(Div(promote(self), promote(other)))

    def __rtruediv__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __floordiv__(self, other):
        return expression(FloorDiv(promote(self), promote(other)))

    def __rfloordiv__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __mod__(self, other):
        return expression(Mod(promote(self), promote(other)))

    def __rmod__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __pow__(self, other):
        return expression(Pow(promote(self), promote(other)))

    def __rpow__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __lshift__(self, other):
        return expression(LShift(promote(self), promote(other)))

    def __rlshift__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __rshift__(self, other):
        return expression(RShift(promote(self), promote(other)))

    def __rrshift__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __and__(self, other):
        return expression(BitAnd(promote(self), promote(other)))

    def __rand__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __xor__(self, other):
        return expression(BitXor(promote(self), promote(other)))

    def __rxor__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __or__(self, other):
        return expression(BitOr(promote(self), promote(other)))

    def __ror__(self, other):
        return expression(Sub(promote(other), promote(self)))

    def __call__(self, *args):
        match promote(self):
            case Atom(name):
                return expression((Functor(name, *(promote(arg) for arg in args))))

            case _:
                raise TypeError(f"Atom required, not {self}")


def promote(obj: Any) -> Term | tuple:
    """
    Convert a Python object to a Term.
    """
    match obj:
        case (
            Wildcard()
            | Variable()
            | Atom()
            | Empty()
            | str()
            | bytes()
            | int()
            | bool()
            | float()
            | complex()
        ):
            return obj
        case Functor(name=name, args=args):
            return Functor(name, *(promote(arg) for arg in args))
        case Structure(args):
            return type(obj)(*(promote(arg) for arg in args))
        case Expression(term):
            return promote(term)
        case tuple():
            return tuple(promote(each) for each in obj)
        case Cons(head=BitOr(left=left, right=right)):
            return Cons(promote(left), promote(right))
        case []:
            return EMPTY
        case [Expression(BitOr(left=left, right=right)), *tail]:
            assert not tail
            return Cons(promote(left), promote(right))
        case [head, *tail]:
            return Cons(promote(head), promote(list(tail)))
        case _:
            raise TypeError(f"{type(obj)}")


type VarCount = tuple[int, Iterator[int]]
_v_count: Iterator[int] = count()


def dcg_expand(head: Term, body: Term) -> tuple[Term, Term]:
    (new_head, new_body), _ = _dcg_expand(head, body).run((next(_v_count), _v_count))
    return new_head, new_body


@with_state
def _dcg_expand(head: Term, body: Term) -> StateGenerator[VarCount, tuple[Term, Term]]:
    @with_state
    def current_variable() -> StateGenerator[VarCount, Variable]:
        i, _ = yield get_state()
        return Variable(f"S${i}")

    @with_state
    def advance_variables() -> StateGenerator[VarCount, tuple[Variable, Variable]]:
        i, counter = yield get_state()
        j = next(counter)
        yield set_state(const((j, counter)))
        return Variable(f"S${i}"), Variable(f"S${j}")

    @with_state
    def dcg_expand_cons(term: Term) -> StateGenerator[VarCount, tuple[Term, Variable]]:
        result_terms = []

        while True:
            match term:
                case Cons(head=head, tail=tail):
                    Sout, Sin = yield advance_variables()
                    result_terms.append(Functor("equal", Sout, Cons(head, Sin)))
                    term = tail
                case Empty():
                    break

        Sin = yield current_variable()
        return Conjunction(*result_terms), Sin

    @with_state
    def walk_body(
        term: Term,
    ) -> StateGenerator[VarCount, Term]:
        match term:
            case Atom(name=name):
                Sout, Sin = yield advance_variables()
                return Functor(name, Sout, Sin), Sin

            case Functor(name="inline", args=inlined):
                Sin = yield current_variable()
                return Conjunction(*tuple(inlined)), Sin

            case Functor(name=name, args=args):
                Sout, Sin = yield advance_variables()
                return Functor(name, *args, Sout, Sin), Sin

            case Cons():
                return (yield dcg_expand_cons(term))

            case Conjunction(body=goals):
                new_goals = []
                for goal in goals:
                    new_goal, _ = yield walk_body(goal)
                    new_goals.append(new_goal)
                Sin = yield current_variable()
                return Conjunction(*new_goals), Sin

            case Disjunction(body=goals):
                new_goals = []
                for goal in goals:
                    new_goal, _ = yield walk_body(goal)
                    new_goals.append(new_goal)
                Sin = yield current_variable()
                return Disjunction(*new_goals), Sin

        raise TypeError(f"Expected query term in DCG body, got: {term!r}")

    Sout = yield current_variable()
    body_expanded, Sin = yield walk_body(body)

    match head:
        case Atom(name=name):
            head_expanded = Functor(name, Sout, Sin)
        case Functor(name=name, args=args):
            head_expanded = Functor(name, *args, Sout, Sin)
        case _:
            raise TypeError(f"Expected head term in DCG body, got: {head!r}")

    assert isinstance(head_expanded, MatchTerm)
    assert isinstance(body_expanded, QueryTerm)
    return head_expanded, body_expanded


# In the Monad, unit is the same as Expression:
unit = Expression


type MFunc = Callable[[Term], Expression]


def bind(expr: Expression, mfunc: MFunc) -> Expression:
    """
    The function bind(expr, Term --> Expression) --> Expression is the monadic
    bind operator.  It takes an Expression object expr and a monadic function
    mfunc, passes the Term associated with expr to mfunc and returns whatever
    mfunc returns.
    """
    return mfunc(expr.term)


def lift(func: Callable[..., Term]) -> Callable[..., Expression]:
    """
    The function lift(... --> Term) --> (... --> Expression) "lifts" a normal
    function that returns an Term into a function that returns an Expression.
    It is typically used as a function decorator.
    """
    return compose(Expression, func)


def chain(*mfuncs: MFunc) -> MFunc:
    """
    Chain monadic functions of type Term --> Expression.
    """
    return cast(MFunc, partial(reduce, bind, tuple(reversed(mfuncs))))


def expression[T: Term](term: T) -> Expression[T]:
    return Expression(term)
