# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import ChainMap
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable, Iterator, cast

from immutables import Map

from .combinators import (
    Goal,
    Next,
    Step,
    amb_from_iterable,
    cut,
    fail,
    failure,
    neg,
    prunable,
    seq_from_iterable,
    success,
    then,
    unit,
)
from .states import State, StateOp, get_state, set_state, with_state
from .tailcalls import tailcall, trampoline
from .terms import (
    AllOf,
    AnyOf,
    Atom,
    BinaryOperator,
    Compound,
    Cons,
    Empty,
    Functor,
    HornetRule,
    Indicator,
    Invert,
    NonVariable,
    Operator,
    Term,
    UnaryOperator,
    Variable,
    Wildcard,
    fresh_name,
    fresh_variable,
)

type Environment = Map[Variable, Term]
type Memo = dict[int, Term]
type FreshState = tuple[dict[Variable, Variable], Memo]
type Arguments = tuple[Term, ...]

type PythonBody = Callable[[Environment], Goal[Database, Environment]]
type PythonGoal = Callable[[Database, Subst], Step[Database, Environment]]


@dataclass(frozen=True, slots=True)
class PythonRule(NonVariable):
    head: NonVariable
    body: PythonBody

    @property
    def indicator(self) -> Indicator:
        return self.head.indicator


def predicate(head: Term) -> Callable[[PythonGoal], PythonRule]:
    assert isinstance(head, NonVariable)

    def decorator(python_goal: PythonGoal) -> PythonRule:
        @wraps(python_goal)
        def python_body(renaming: Environment) -> Goal[Database, Environment]:
            def goal(db: Database, env: Environment) -> Step[Database, Environment]:
                return python_goal(db, Subst(env, renaming))

            return goal

        return PythonRule(head, python_body)

    return decorator


def deref_and_compress(env: Environment, term: Term) -> tuple[Environment, Term]:
    """
    Resolve variable bindings and perform path compression.

    Follows the chain of substitutions for a variable and updates the map
    to point directly to the root value to speed up future lookups.
    """

    visited = set()
    while isinstance(term, Variable) and term in env:
        if term in visited:
            raise RuntimeError(f'Cyclic variable binding detected: {term}')
        visited.add(term)
        term = env[term]
    mm = env.mutate()
    for v in visited:
        mm[v] = term
    return mm.finish(), term


def unify(this: Term, that: Term) -> Goal[Database, Environment]:
    """
    Attempt to unify two terms.

    Returns a goal that succeeds if the terms can be matched under the
    current substitution, potentially extending it.
    """

    def goal(
        db: Database, env: Environment, this: Term = this, that: Term = that
    ) -> Step[Database, Environment]:
        env, this = deref_and_compress(env, this)
        env, that = deref_and_compress(env, that)
        return _unify(this, that)(db, env)

    return goal


def unify_variable(variable: Variable, term: Term) -> Goal[Database, Environment]:
    def goal(
        db: Database, env: Environment, variable: Variable = variable, term: Term = term
    ) -> Step[Database, Environment]:
        env, value = deref_and_compress(env, variable)
        assert value is variable
        return unit(db, env.set(variable, term))

    return goal


def unify_pairs(*pairs: tuple[Term, Term]) -> Goal[Database, Environment]:
    return lambda ctx, subst, pairs=pairs: tailcall(
        seq_from_iterable(unify(this, that) for this, that in pairs)(ctx, subst)
    )


def unify_any(variable: Variable, *values: Term) -> Goal[Database, Environment]:
    return amb_from_iterable(unify(variable, value) for value in values)


def _unify(this: Term, that: Term) -> Goal[Database, Environment]:
    match this, that:
        case _ if this == that:
            return unit

        case Wildcard(), _:
            return unit

        case _, Wildcard():
            return unit

        case Variable(), _:
            return unify_variable(this, that)

        case _, Variable():
            return unify_variable(that, this)

        case Compound(), Compound() if this.indicator == that.indicator:
            return unify_pairs(*zip(this.args, that.args))

        case _:
            return fail


@dataclass(frozen=True, slots=True)
class Subst(Mapping[Variable, Term]):
    map: Environment
    env: Environment

    def __len__(self) -> int:
        return len(self.map)

    def __iter__(self) -> Iterator[Variable]:
        yield from self.map.keys()

    def __getitem__(self, variable: Term) -> Term:
        if isinstance(variable, Variable):
            return self.actualize(self.env.get(variable, variable))
        return self.actualize(variable)

    def actualize(self, obj: Term) -> Term:
        match self.deref(obj):
            case Functor(name=name, args=args):
                return Functor(name, *(self.actualize(a) for a in args))
            case Operator(args=args) as struct:
                return type(struct)(*(self.actualize(a) for a in args))
            case obj:
                return obj

    def deref(self, obj: Term) -> Term:
        visited: set[Variable] = set()
        while isinstance(obj, Variable) and obj in self.map:
            if obj in visited:
                raise RuntimeError(f'Cyclic variable binding detected: {obj}')
            visited.add(obj)
            obj = self.map[obj]
        return obj


def fresh(clause: Clause) -> Clause:
    memo: Memo = {id(var): fresh_variable() for var in clause.env.values()}
    memo.update(clause.ground)
    return deepcopy(clause, memo)


def resolve(query: Term) -> Goal[Database, Environment]:
    match query:
        case Atom('true'):
            return unit

        case Atom('cut'):
            return cut

        case Atom('fail'):
            return fail

        case AllOf():
            return seq_from_iterable(resolve(a) for a in query.args)

        case AnyOf():
            return amb_from_iterable(resolve(a) for a in query.args)

        case Invert():
            return neg(resolve(query.operand))

        case Atom() | Functor():
            return lambda db, subst: prunable(
                fresh(clause)(query) for clause in db[query.indicator]
            )(db, subst)

        case _:
            raise TypeError(f'Type error: "callable" expected, found {query!r}')


@dataclass(frozen=True, slots=True)
class Clause(ABC):
    env: Environment
    ground: Memo

    @abstractmethod
    def __call__(self, query: NonVariable) -> Goal[Database, Environment]: ...


@dataclass(frozen=True, slots=True)
class AtomicFact(Clause):
    def __call__(self, query: NonVariable) -> Goal[Database, Environment]:
        return unit


@dataclass(frozen=True, slots=True)
class CompoundFact(Clause):
    head: Functor

    def __call__(self, query: NonVariable) -> Goal[Database, Environment]:
        return unify(query, self.head)


@dataclass(frozen=True, slots=True)
class AtomicRule(Clause):
    body: Term

    def __call__(self, query: NonVariable) -> Goal[Database, Environment]:
        return resolve(self.body)


@dataclass(frozen=True, slots=True)
class CompoundRule(Clause):
    head: Functor
    body: Term

    def __call__(self, query: NonVariable) -> Goal[Database, Environment]:
        return then(unify(query, self.head), resolve(self.body))


@dataclass(frozen=True, slots=True)
class AtomicPythonRule(Clause):
    body: PythonBody

    def __call__(self, query: NonVariable) -> Goal[Database, Environment]:
        return self.body(self.env)


@dataclass(frozen=True, slots=True)
class CompoundPythonRule(Clause):
    head: Functor
    body: PythonBody

    def __call__(self, query: NonVariable) -> Goal[Database, Environment]:
        return then(unify(query, self.head), self.body(self.env))


class Database(ChainMap[Indicator, list[Clause]]):
    def tell(self, *terms: NonVariable) -> None:
        results: list[tuple[Clause, Indicator]] = []
        for term in terms:
            assert isinstance(term, NonVariable)
            results.append(make_clause(term))
        for clause, indicator in results:
            self.setdefault(indicator, []).append(clause)

    def ask(self, *conjuncts: NonVariable, subst: Subst | None = None) -> Iterable[Subst]:
        query, env = make_term(AllOf(*conjuncts))
        goal = resolve(query)
        step = goal(self, Map() if subst is None else subst.map)
        _failure: Next[Environment] = cast(Next[Environment], failure)
        for new_subst in trampoline(lambda: step(success, _failure, _failure)):
            yield Subst(new_subst, env)


def ground_children(term: Term) -> Iterator[Term]:
    if isinstance(term, Compound):
        yield from term.args
    if isinstance(term, (AtomicRule, CompoundRule)):
        yield term.body


def prune_ground_map(memo: Memo) -> Memo:
    roots = set(memo.values())
    for term in tuple(roots):
        roots.difference_update(ground_children(term))
    return {id(term): term for term in roots}


def get_var(var: Variable) -> State[FreshState, Variable | None]:
    def get_env(state: FreshState) -> Variable | None:
        return state[0].get(var)

    return get_state(get_env)


def add_var(canonical: Variable, renamed: Variable) -> State[FreshState, FreshState]:
    def setter(state: FreshState) -> FreshState:
        env, memo = state
        env[canonical] = renamed
        return env, memo

    return set_state(setter)


def add_ground(term: Term) -> State[FreshState, FreshState]:
    def setter(state: FreshState) -> FreshState:
        env, memo = state
        memo[id(term)] = term
        return env, memo

    return set_state(setter)


@with_state
def new_variable(old_var: Variable) -> StateOp[FreshState, Term]:
    new_var: Variable | None = yield get_var(old_var)
    if new_var is None:
        new_var = Variable(fresh_name(old_var.name))
        yield add_var(old_var, new_var)
    return new_var


@with_state
def new_args(items: Arguments) -> StateOp[FreshState, tuple[Arguments, bool]]:
    new_items: list[Term] = []
    all_ground = True
    for item in items:
        new_item, ground = yield new_term(item)
        if ground:
            yield add_ground(new_item)
        all_ground = all_ground and ground
        new_items.append(new_item)
    return tuple(new_items), all_ground


@with_state
def new_term(term: Term) -> StateOp[FreshState, tuple[Term, bool]]:
    match term:
        case Atom() | Empty() | str() | int() | float() | bytes() | complex() | Exception():
            yield add_ground(term)
            return term, True

        case Wildcard():
            yield add_ground(term)
            return term, True

        case Variable():
            variable = yield new_variable(term)
            return variable, False

        case AllOf(args=args):
            args, ground = yield new_args(args)
            term = AllOf(*args)
            if ground:
                yield add_ground(term)
            return term, ground

        case Functor(name=name, args=args):
            args, ground = yield new_args(args)
            term = Functor(name, *args)
            if ground:
                yield add_ground(term)
            return term, ground

        case Cons(head=head, tail=tail):
            head, head_ground = yield new_term(head)
            tail, tail_ground = yield new_term(tail)
            ground = head_ground and tail_ground
            term = Cons(head, tail)
            if ground:
                yield add_ground(term)
            return term, ground

        case UnaryOperator(operand=operand):
            operand, ground = yield new_term(operand)
            term = type(term)(operand)
            if ground:
                yield add_ground(term)
            return term, ground

        case BinaryOperator(left=left, right=right):
            left, left_ground = yield new_term(left)
            right, right_ground = yield new_term(right)
            ground = left_ground and right_ground
            term = type(term)(left, right)
            if ground:
                yield add_ground(term)
            return term, ground

        case _:
            raise TypeError(f'Unsupported Term node: {term}')


@with_state
def new_clause(term: Term) -> StateOp[FreshState, tuple[Clause, Indicator]]:
    match term:
        case Atom(name=name) as head:
            head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_map(memo)
            return AtomicFact(env, memo), (name, 0)

        case Compound(name=name, args=args) as head:
            head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_map(memo)
            return CompoundFact(env, memo, head), (name, len(args))

        case HornetRule(head=Atom(name=name) as head, body=body):
            body, _ = yield new_term(body)
            env, memo = yield get_state()
            memo = prune_ground_map(memo)
            return AtomicRule(env, memo, body), (name, 0)

        case HornetRule(head=Functor(name=name, args=args) as head, body=body):
            head, _ = yield new_term(head)
            body, _ = yield new_term(body)
            env, memo = yield get_state()
            memo = prune_ground_map(memo)
            return CompoundRule(env, memo, head, body), (name, len(args))

        case PythonRule(head=Atom(name=name) as head, body=body):
            head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_map(memo)
            return AtomicPythonRule(env, memo, body), (name, 0)

        case PythonRule(head=Functor(name=name, args=args) as head, body=body):
            head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_map(memo)
            return CompoundPythonRule(env, memo, head, body), (name, len(args))

        case _:
            raise TypeError(f'Unsupported Term node: {term}')


def make_term(term: Term) -> tuple[Term, Environment]:
    (term, _), (renaming, _) = new_term(term).run(({}, {}))
    return term, Map(renaming)


def make_clause(term: Term) -> tuple[Clause, Indicator]:
    result, _ = new_clause(term).run(({}, {}))
    return result
