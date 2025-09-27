# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import ChainMap
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable, Sequence, cast

from hornet import terms

from .combinators import (
    Goal,
    Step,
    Subst,
    amb_from_iterable,
    cut,
    fail,
    failure,
    neg,
    predicate_goal,
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
)

type Environment = dict[NonVariable, Variable]

type PythonBody = Callable[[Environment], Goal[Database]]
type PythonGoal = Callable[[Database, Subst, Environment], Step[Database]]


@dataclass(frozen=True, slots=True)
class PythonRule(Rule[PythonBody]):
    pass


def predicate(head: Term) -> Callable[[PythonGoal], PythonRule]:
    assert isinstance(head, NonVariable)

    def decorator(func: PythonGoal) -> PythonRule:
        @wraps(func)
        def python_body(env: Environment) -> Goal[Database]:
            def python_goal(db: Database, subst: Subst) -> Step[Database]:
                return func(db, subst, env)

            return python_goal

        return PythonRule(head=head, body=python_body)

    return decorator


@dataclass(frozen=True, slots=True)
class SubstProxy(Mapping):
    subst: Subst
    env: Environment

    def __len__(self):
        return len(self.env)

    def __iter__(self):
        yield from self.env.keys()

    def __getitem__(self, variable: NonVariable):
        return self.subst.actualize(self.env[variable])


@dataclass(frozen=True, slots=True)
class Clause(ABC):
    env: Environment

    @abstractmethod
    def goal(self, query) -> Goal[Database]: ...


def fresh_goal(clause, query: NonVariable) -> Goal[Database]:
    fresh_env = {var_expr: terms.fresh_variable() for var_expr in clause.env.keys()}
    memo = {
        id(clause_var): fresh_env[var_expr]
        for var_expr, clause_var in clause.env.items()
    }
    fresh_clause = deepcopy(clause, memo=memo)
    assert fresh_clause.env == fresh_env
    return fresh_clause.goal(query)


@dataclass(frozen=True, slots=True)
class AtomicFact(Clause):
    def goal(self, query: NonVariable) -> Goal[Database]:
        return unit


@dataclass(frozen=True, slots=True)
class CompoundFact(Clause):
    head: Compound

    def goal(self, query: NonVariable) -> Goal[Database]:
        return unify(query, self.head)


@dataclass(frozen=True, slots=True)
class AtomicRule(Clause):
    body: Term

    def goal(self, query: NonVariable) -> Goal[Database]:
        return resolve(self.body)


@dataclass(frozen=True, slots=True)
class CompoundRule(Clause):
    head: Functor
    body: Term

    def goal(self, query: NonVariable) -> Goal[Database]:
        return then(unify(query, self.head), resolve(self.body))


@dataclass(frozen=True, slots=True)
class AtomicPythonRule(Clause):
    body: PythonBody

    def goal(self, query: NonVariable) -> Goal[Database]:
        return self.body(self.env)


@dataclass(frozen=True, slots=True)
class CompoundPythonRule(Clause):
    head: Compound
    body: PythonBody

    def goal(self, query: NonVariable) -> Goal[Database]:
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
            return lambda db, subst: predicate_goal(
                [fresh_goal(clause, query) for clause in db[query.indicator]]
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
            result, _ = term_to_clause(term).run({})
            results.append(result)
        for clause, indicator in results:
            self.setdefault(indicator, []).append(clause)

    def ask(
        self, *conjuncts: NonVariable, subst: Subst | None = None
    ) -> Iterable[Mapping]:
        assert all(isinstance(c, NonVariable) for c in conjuncts)
        query = Conjunction(*conjuncts)
        fresh_query, env = fresh(term=query).run({})
        return (
            SubstProxy(new_subst, env)
            for new_subst in self.run_query(fresh_query, subst)
        )

    def run_query(self, query: Term, subst: Subst | None = None) -> Iterable[Subst]:
        if subst is None:
            subst = Subst()
        goal = resolve(query)
        step = goal(self, subst)
        for new_subst in trampoline(lambda: step(success, failure, failure)):
            yield new_subst


def get_mapped_var(var: Variable) -> State[Environment, Variable | None]:
    return get_state(lambda env: env.get(var))


def map_var(canonical: Variable, renamed: Variable) -> State[Environment, Environment]:
    def setter(env) -> Environment:
        env[canonical] = renamed
        return env

    return set_state(setter)


@with_state
def fresh_variable(
    old_var: Variable,
) -> StateGenerator[Environment, Term]:
    new_var = yield get_mapped_var(old_var)
    if new_var is None:
        new_var = Variable(fresh_name(old_var.name))
        yield map_var(old_var, new_var)
    return new_var


@with_state
def fresh_list(items: Sequence[Term]) -> StateGenerator[Environment, tuple[Term, ...]]:
    new_items = []
    for item in items:
        new_item = yield fresh(item)
        new_items.append(new_item)
    return tuple(new_items)


@with_state
def fresh(term: Term | tuple[Term]) -> StateGenerator[Environment, Term]:
    match term:
        case str() | int() | float() | bool() | complex():
            return term

        case Variable(name="_"):
            return term

        case Variable():
            return (yield cast(State[Environment, Term], fresh_variable(term)))

        case Atom():
            return term

        case Functor(name=name, args=args):
            new_args = yield fresh_list(args)
            return Functor(name, *new_args)

        case Empty():
            return term

        case Cons(head=head, tail=tail):
            new_head = yield fresh(head)
            new_tail = yield fresh(tail)
            return Cons(new_head, new_tail)

        case UnaryOperator(operand=operand):
            new_operand = yield fresh(operand)
            return type(term)(operand=new_operand)

        case BinaryOperator(left=left, right=right):
            new_left = yield fresh(left)
            new_right = yield fresh(right)
            return type(term)(new_left, new_right)

        case Conjunction(args=conjuncts):
            new_conjuncts = yield fresh_list(conjuncts)
            return Conjunction(*new_conjuncts)

        case tuple() as conjuncts:
            new_conjuncts = yield fresh_list(conjuncts)
            return Conjunction(*new_conjuncts)

    raise TypeError(f"Unsupported Term node: {term}")


@with_state
def term_to_clause(
    term: Term | PythonRule,
) -> StateGenerator[Environment, tuple[Clause, Indicator]]:
    match term:
        case Atom(name=name) as head:
            fresh_head = yield fresh(head)
            env = yield get_state()
            return AtomicFact(env), (name, None)

        case Compound(name=name, args=args) as head:
            fresh_args = yield fresh_list(args)
            fresh_head = Functor(name, *fresh_args)
            env = yield get_state()
            return CompoundFact(env, fresh_head), (fresh_head.name, len(fresh_args))

        case HornetRule(head=Atom(name=name) as head, body=body):
            fresh_body_goal = yield fresh(body)
            env = yield get_state()
            return AtomicRule(env, fresh_body_goal), (name, None)

        case HornetRule(head=Functor(name=name, args=args) as head, body=body):
            fresh_head = yield fresh(head)
            env = yield get_state()
            if body:
                fresh_body_goal = yield fresh(body)
                return CompoundRule(env, fresh_head, fresh_body_goal), (
                    name,
                    len(fresh_head.args),
                )
            else:
                return CompoundFact(env, fresh_head), (
                    name,
                    len(fresh_head.args),
                )

        case PythonRule(head=Atom(name=name) as head, body=body):
            fresh_head = yield fresh(head)
            env = yield get_state()
            return AtomicPythonRule(env, body), (name, None)

        case PythonRule(head=Functor(name=name, args=args) as head, body=body):
            fresh_head = yield fresh(head)
            env = yield get_state()
            return CompoundPythonRule(env, fresh_head, body), (name, len(args))

    raise TypeError(f"Unsupported Term node: {term}")
