# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import ChainMap
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable, Iterator, Sequence

from .combinators import (
    Goal,
    Map,
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
    unify,
    unit,
)
from .states import State, StateGenerator, get_state, set_state, with_state
from .tailcalls import trampoline
from .terms import (
    Atom,
    BinaryOperator,
    Compound,
    Conjunction,
    Cons,
    Disjunction,
    Empty,
    Functor,
    HornetRule,
    Indicator,
    Invert,
    NonVariable,
    Rule,
    Term,
    UnaryOperator,
    Variable,
    fresh_name,
    fresh_variable,
)

type Environment = dict[NonVariable, Variable]
type Memo = dict[int, Term]
type FreshState = tuple[Environment, Memo]

type PythonBody = Callable[[Environment], Goal[Database]]
type PythonGoal = Callable[[Database, Subst], Step[Database]]


@dataclass(frozen=True, slots=True)
class PythonRule(Rule[PythonBody]):
    pass


def predicate(head: Term) -> Callable[[PythonGoal], PythonRule]:
    assert isinstance(head, NonVariable)

    def decorator(func: PythonGoal) -> PythonRule:
        @wraps(func)
        def python_body(env: Environment) -> Goal[Database]:
            def python_goal(db: Database, subst: Map) -> Step[Database]:
                return func(db, Subst(subst, env))

            return python_goal

        return PythonRule(head=head, body=python_body)

    return decorator


@dataclass(frozen=True, slots=True)
class Subst(Mapping):
    map: Map
    env: Environment

    def __len__(self):
        return len(self.map)

    def __iter__(self):
        yield from self.map.keys()

    def __getitem__(self, variable):
        return self.actualize(self.env.get(variable, variable))

    def actualize(self, obj) -> Term:
        match self.deref(obj):
            case Functor(name=name, args=args):
                return Functor(name, *(self.actualize(a) for a in args))
            case Compound(args=args) as struct:
                return type(struct)(*(self.actualize(a) for a in args))
            case obj:
                return obj

    def deref(self, obj) -> Term:
        visited = set()
        while isinstance(obj, Variable) and obj in self.map:
            if obj in visited:
                raise RuntimeError(f"Cyclic variable binding detected: {obj}")
            visited.add(obj)
            obj = self.map.get(obj, obj)
        return obj


@dataclass(frozen=True, slots=True)
class Clause(ABC):
    env: Environment
    ground: Memo

    @abstractmethod
    def __call__(self, query) -> Goal[Database]: ...


def fresh(clause: Clause, query: NonVariable) -> Goal[Database]:
    memo: Memo = {id(var): fresh_variable() for var in clause.env.values()}
    memo.update(clause.ground)
    fresh_clause = deepcopy(clause, memo=memo)
    return fresh_clause(query)


@dataclass(frozen=True, slots=True)
class AtomicFact(Clause):
    def __call__(self, query: NonVariable) -> Goal[Database]:
        return unit


@dataclass(frozen=True, slots=True)
class CompoundFact(Clause):
    head: Compound

    def __call__(self, query: NonVariable) -> Goal[Database]:
        return unify(query, self.head)


@dataclass(frozen=True, slots=True)
class AtomicRule(Clause):
    body: Term

    def __call__(self, query: NonVariable) -> Goal[Database]:
        return resolve(self.body)


@dataclass(frozen=True, slots=True)
class CompoundRule(Clause):
    head: Functor
    body: Term

    def __call__(self, query: NonVariable) -> Goal[Database]:
        return then(unify(query, self.head), resolve(self.body))


@dataclass(frozen=True, slots=True)
class AtomicPythonRule(Clause):
    body: PythonBody

    def __call__(self, query: NonVariable) -> Goal[Database]:
        return self.body(self.env)


@dataclass(frozen=True, slots=True)
class CompoundPythonRule(Clause):
    head: Compound
    body: PythonBody

    def __call__(self, query: NonVariable) -> Goal[Database]:
        return then(unify(query, self.head), self.body(self.env))


def resolve(query: Term) -> Goal[Database]:
    match query:
        case Atom("true"):
            return unit

        case Atom("cut"):
            return cut

        case Atom("fail"):
            return fail

        case Atom() | Functor():
            return lambda db, subst: prunable(
                fresh(clause, query) for clause in db[query.indicator]
            )(db, subst)

        case Conjunction(args=args):
            return seq_from_iterable(resolve(a) for a in args)

        case Disjunction(body=args):
            return amb_from_iterable(resolve(a) for a in args)

        case Invert(args=(inner,)):
            return neg(resolve(inner))

    raise TypeError(f"Type error: `callable' expected, found {query!r}")


class Database(ChainMap[Indicator, list[Clause]]):
    def tell(self, *terms: NonVariable) -> None:
        results = []
        for term in terms:
            assert isinstance(term, NonVariable)
            result, _ = term_to_clause(term).run(({}, {}))
            results.append(result)
        for clause, indicator in results:
            self.setdefault(indicator, []).append(clause)

    def ask(self, *conjuncts: Term, subst: Map | None = None) -> Iterable[Subst]:
        assert all(isinstance(c, NonVariable) for c in conjuncts)
        (query, _), (env, _) = new_term(term=conjuncts).run(({}, {}))
        if subst is None:
            subst = Map()
        goal = resolve(query)
        step = goal(self, subst)
        for new_subst in trampoline(lambda: step(success, failure, failure)):
            yield Subst(new_subst, env)


def ground_children(term: Term) -> Iterator[Term]:
    if isinstance(term, Compound):
        yield from term.args
    if isinstance(term, AtomicRule | CompoundRule) and term.body is not None:
        yield term.body


def prune_ground_memo(memo: Memo) -> Memo:
    roots = set(memo.values())
    for term in tuple(roots):
        roots.difference_update(ground_children(term))
    return {id(term): term for term in roots}


def get_var(var: Variable) -> State[FreshState, Variable | None]:
    return get_state(lambda state: state[0].get(var))


def add_var(canonical: Variable, renamed: Variable) -> State[FreshState, FreshState]:
    def setter(state) -> FreshState:
        env, memo = state
        env[canonical] = renamed
        return env, memo

    return set_state(setter)


def add_ground(term: Term) -> State[FreshState, FreshState]:
    def setter(state) -> FreshState:
        env, memo = state
        memo[id(term)] = term
        return env, memo

    return set_state(setter)


@with_state
def new_variable(old_var: Variable) -> StateGenerator[FreshState, Term]:
    new_var = yield get_var(old_var)
    if new_var is None:
        new_var = Variable(fresh_name(old_var.name))
        yield add_var(old_var, new_var)
    return new_var


@with_state
def new_args_list(
    items: Sequence[Term],
) -> StateGenerator[FreshState, tuple[tuple[Term, ...], bool]]:
    new_items = []
    all_ground = True
    for item in items:
        new_item, ground = yield new_term(item)
        if ground:
            yield add_ground(new_item)
        all_ground = all_ground and ground
        new_items.append(new_item)
    return tuple(new_items), all_ground


@with_state
def new_term(
    term: Term | tuple[Term],
) -> StateGenerator[FreshState, tuple[Term, bool]]:
    match term:
        case str() | int() | float() | bool() | complex() | Exception():
            yield add_ground(term)
            return term, True

        case Variable(name="_"):
            yield add_ground(term)
            return term, True

        case Variable():
            variable = yield new_variable(term)
            return variable, False

        case Atom():
            yield add_ground(term)
            return term, True

        case Functor(name=name, args=args):
            new_args, ground = yield new_args_list(args)
            result = Functor(name, *new_args)
            if ground:
                yield add_ground(result)
            return result, ground

        case Empty():
            yield add_ground(term)
            return term, True

        case Cons(head=head, tail=tail):
            new_head, head_ground = yield new_term(head)
            new_tail, tail_ground = yield new_term(tail)
            ground = head_ground and tail_ground
            result = Cons(new_head, new_tail)
            if ground:
                yield add_ground(result)
            return result, ground

        case UnaryOperator(operand=operand):
            new_operand, ground = yield new_term(operand)
            result = type(term)(new_operand)
            if ground:
                yield add_ground(result)
            return result, ground

        case BinaryOperator(left=left, right=right):
            new_left, left_ground = yield new_term(left)
            new_right, right_ground = yield new_term(right)
            ground = left_ground and right_ground
            result = type(term)(new_left, new_right)
            if ground:
                yield add_ground(result)
            return result, ground

        case Conjunction(args=conjuncts):
            new_conjuncts, ground = yield new_args_list(conjuncts)
            result = Conjunction(*new_conjuncts)
            if ground:
                yield add_ground(result)
            return result, ground

        case tuple() as conjuncts:
            new_conjuncts, ground = yield new_args_list(conjuncts)
            result = Conjunction(*new_conjuncts)
            if ground:
                yield add_ground(result)
            return result, ground

    raise TypeError(f"Unsupported Term node: {term}")


@with_state
def term_to_clause(
    term: Term | PythonRule,
) -> StateGenerator[FreshState, tuple[Clause, Indicator]]:
    match term:
        case Atom(name=name) as head:
            new_head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_memo(memo)
            return AtomicFact(env, memo), (name, 0)

        case Compound(name=name, args=args) as head:
            new_head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_memo(memo)
            return CompoundFact(env, memo, new_head), (new_head.name, len(head.args))

        case HornetRule(head=Atom(name=name) as head, body=body):
            new_body, _ = yield new_term(body)
            env, memo = yield get_state()
            memo = prune_ground_memo(memo)
            return AtomicRule(env, memo, new_body), (name, 0)

        case HornetRule(head=Functor(name=name, args=args) as head, body=body):
            new_head, _ = yield new_term(head)
            if body:
                new_body, _ = yield new_term(body)
                env, memo = yield get_state()
                memo = prune_ground_memo(memo)
                return CompoundRule(env, memo, new_head, new_body), (
                    name,
                    len(new_head.args),
                )
            else:
                env, memo = yield get_state()
                memo = prune_ground_memo(memo)
                return CompoundFact(env, memo, new_head), (name, len(new_head.args))

        case PythonRule(head=Atom(name=name) as head, body=body):
            new_head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_memo(memo)
            return AtomicPythonRule(env, memo, body), (name, 0)

        case PythonRule(head=Functor(name=name, args=args) as head, body=body):
            new_head, _ = yield new_term(head)
            env, memo = yield get_state()
            memo = prune_ground_memo(memo)
            return CompoundPythonRule(env, memo, new_head, body), (name, len(args))

    raise TypeError(f"Unsupported Term node: {term}")
