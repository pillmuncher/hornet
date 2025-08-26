# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections import ChainMap, defaultdict
from dataclasses import dataclass
from functools import reduce
from itertools import count
from typing import Callable, Iterable, Mapping, Protocol

from .expressions import Expression
from .terms import Atom, Functor, Indicator, LShift, RShift, Structure, Term, Variable

type HeadTerm = Atom | Functor
type ClauseTerm = HeadTerm | LShift | RShift

type Result = tuple[Subst | None, Next] | None
type Next = Callable[[], Result]
type Emit = Callable[[Database, Subst, Next], Result]
type Step = Callable[[Emit, Next, Next], Result]
type Goal = Callable[[Database, Subst], Step]


class Subst(ChainMap[Variable, Term]):
    """A substitution environment that maps Variables to values. Such a mapping
    is called a variable binding. Variables are bound during computations and
    unbound again during backtracking. This process is called trailing."""

    def deref(self, obj) -> Term:
        "Chase down Variable bindings."
        while isinstance(obj, Variable) and obj in self:
            obj = self[obj]
        return obj

    def smooth(self, obj) -> Term:
        "Recursively replace all variables with their bindings."
        match self.deref(obj):
            case Structure(args) as struct:
                return type(struct)(*(self.smooth(each) for each in args))
            case term:
                return term

    @property
    class proxy(Mapping):
        "A proxy interface to Subst."

        def __init__(self, subst: Subst):
            self._subst = subst

        def __getitem__(self, variable: Variable):
            return self._subst.smooth(variable)

        def __iter__(self):
            return iter(self._subst)

        def __len__(self):
            return len(self._subst)


def var(name: str, _var_counter=count()) -> Variable:
    return Variable(f"{name}{next(_var_counter)}")


class Clause(Protocol):
    def __call__(self, query_term: Term) -> Goal: ...


@dataclass(frozen=True, slots=True)
class Fact:
    head: HeadTerm

    def __call__(self, query_term: Term) -> Goal:
        return unify((query_term, self.head))


@dataclass(frozen=True, slots=True)
class Rule:
    head: HeadTerm
    body: Goal

    def __call__(self, query_term: Term) -> Goal:
        return seq(unify((query_term, self.head)), self.body)


@dataclass(frozen=True, slots=True)
class Query:
    term: HeadTerm

    def __call__(self, db: Database, subst: Subst) -> Step:
        return amb_from_iterable(
            clause(self.term) for clause in db[self.term.indicator]
        )(db, subst)


def dcg_expand[T: ClauseTerm](term: T) -> T:
    return term


class Database(defaultdict[Indicator, list[Clause]]):
    def __init__(self):
        super().__init__(list)

    def add(self, clause_expr: Expression[ClauseTerm]) -> None:
        match clause_expr.node:
            case Atom() | Functor() as node:
                self[node.indicator].append(Fact(node))
            case LShift(head=head, body=body) as node:
                self[node.indicator].append(Rule(head, Query(body)))
            case RShift() as node:
                node = dcg_expand(node)
                self[node.indicator].append(Rule(node.head, Query(node.body)))

    def ask(
        self, query_expr: Expression[HeadTerm], subst: Subst | None = None
    ) -> Iterable[Subst]:
        result = Query(query_expr.node)(self, subst or Subst())(
            success, failure, failure
        )
        while result is not None:
            subst, backtrack = result
            if subst is not None:
                yield subst.proxy
            result = backtrack()


def tailcall(cont: Callable[..., Result]) -> Callable[..., Result]:
    """Hand-rolled Tail-call elimination.
    A continuation is wrapped in a thunk and returned so it can be called later
    by a driver function."""

    def wrapped(*args, **kwargs) -> Result:
        return None, lambda: cont(*args, **kwargs)

    return wrapped


@tailcall
def success(db: Database, subst: Subst, no: Next) -> Result:
    "Return the current solution and start searching for more."
    return subst, no


@tailcall
def failure() -> Result:
    "Fail."


def bind(step: Step, goal: Goal) -> Step:
    "Return the result of applying goal to step."

    @tailcall
    def mb(yes: Emit, no: Next, prune: Next) -> Result:
        @tailcall
        def on_success(db: Database, subst: Subst, no: Next) -> Result:
            return goal(db, subst)(yes, no, prune)

        return step(on_success, no, prune)

    return mb


def unit(db: Database, subst: Subst) -> Step:
    """Take the single value subst into the monad. Represents success.
    Together with 'then', this makes the monad also a monoid. Together
    with 'fail' and 'choice', this makes the monad also a lattice."""

    @tailcall
    def step(yes: Emit, no: Next, prune: Next) -> Result:
        return yes(db, subst, no)

    return step


def cut(db: Database, subst: Subst) -> Step:
    "yes, then prune the search tree at the previous choice point."

    @tailcall
    def step(yes: Emit, no: Next, prune: Next) -> Result:
        # we commit to the current execution path by injecting
        # the prune continuation as our new backtracking path:
        return yes(db, subst, prune)

    return step


def fail(db: Database, subst: Subst) -> Step:
    """Ignore the argument and start backtracking. Represents failure.
    Together with 'coice', this makes the monad also a monoid. Together
    with 'unit' and 'then', this makes the monad also a lattice.
    It is also mzero."""

    @tailcall
    def step(yes: Emit, no: Next, prune: Next) -> Result:
        return no()

    return step


def then(goal1: Goal, goal2: Goal) -> Goal:
    """Apply two monadic functions goal1 and goal2 in sequence.
    Together with 'unit', this makes the monad also a monoid. Together
    with 'fail' and 'choice', this makes the monad also a lattice."""

    def goal(db: Database, subst: Subst) -> Step:
        return bind(goal1(db, subst), goal2)

    return goal


def seq_from_iterable(goals: Iterable[Goal]) -> Goal:
    "Find solutions for all goals in sequence."
    return reduce(then, goals, unit)


def seq(*goals: Goal) -> Goal:
    "Find solutions for all goals in sequence."
    return seq_from_iterable(goals)


def choice(goal1: Goal, goal2: Goal) -> Goal:
    """Succeeds if either of the goal functions succeeds.
    Together with 'fail', this makes the monad also a monoid. Together
    with 'unit' and 'then', this makes the monad also a lattice."""

    def goal(db: Database, subst: Subst) -> Step:
        @tailcall
        def step(yes: Emit, no: Next, prune: Next) -> Result:
            # we pass goal1 and goal2 the same success continuation, so we
            # can invoke goal1 and goal2 at the same point in the computation:
            @tailcall
            def on_failure() -> Result:
                return goal2(db, subst)(yes, no, prune)

            return goal1(db, subst)(yes, on_failure, prune)

        return step

    return goal


def amb_from_iterable(goals: Iterable[Goal]) -> Goal:
    joined = reduce(choice, goals, fail)

    def goal(db: Database, subst: Subst) -> Step:
        @tailcall
        def step(yes: Emit, no: Next, prune: Next) -> Result:
            # we serialize the goals and inject the
            # fail continuation as the prune path:
            return joined(db, subst)(yes, no, no)

        return step

    return goal


def amb(*goals: Goal) -> Goal:
    "Find solutions for some goals. This creates a choice point."
    return amb_from_iterable(goals)


def neg(goal: Goal) -> Goal:
    "Invert the result of a monadic computation, AKA negation as failure."
    return amb(seq(goal, cut, fail), unit)


def compatible(this, that):
    "Only sequences of same type and length are compatible in unification."
    return type(this) is type(that) and len(this) == len(that)


def _unify(this: Term, that: Term):
    match this, that:
        case _ if this == that:
            # Equal things are already unified:
            return unit
        case Structure(args=this_args), Structure(args=that_args) if (
            this.indicator == that.indicator
        ):
            # Two Structures are unified only if their elements are also and both have
            # the same type:
            return unify(*zip(this_args, that_args))

        case Variable(), _:
            # Bind a Variable to another thing:
            return lambda db, subst: unit(subst.new_child({this: that}), db)
        case _, Variable():
            # Same as above, but with swapped arguments:
            return lambda db, subst: unit(subst.new_child({that: this}), db)
        case _:
            # Unification failed:
            return fail


# Public interface to _unify:
def unify(*pairs: tuple[Term, Term]) -> Goal:
    """Unify 'this' and 'that'.
    If at least one is an unbound Variable, bind it to the other object.
    If both are either lists or tuples, try to unify them recursively.
    Otherwise, unify them if they are equal."""
    return lambda db, subst: seq_from_iterable(
        _unify(subst.deref(this), subst.deref(that)) for this, that in pairs
    )(db, subst)


def unify_any(variable: Variable, *values: Term) -> Goal:
    """Tries to unify a variable with any one of objects.
    Fails if no object is unifiable."""
    return amb_from_iterable(unify((variable, value)) for value in values)


@dataclass(frozen=True, slots=True)
class Predicate(Term):
    value: Goal


def predicate(pred: Goal) -> Term:
    return Predicate(pred)
