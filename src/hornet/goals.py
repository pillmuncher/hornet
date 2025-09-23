from __future__ import annotations

from collections import ChainMap
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable, Sequence, cast

from immutables import Map

from hornet import terms

from .combinators import (
    Goal,
    Step,
    Subst,
    amb_from_iterable,
    failure,
    neg,
    seq,
    seq_from_iterable,
    success,
    unify,
    unit,
)
from .expressions import Expression, HasTerm, RuleExpression
from .states import State, StateGenerator, get_env, get_state, set_state, with_state
from .tailcalls import trampoline
from .terms import (
    EMPTY,
    Atom,
    BinaryOperator,
    Conjunction,
    Cons,
    Disjunction,
    Empty,
    Functor,
    HornetRule,
    Indicator,
    Invert,
    MatchTerm,
    Negation,
    QueryTerm,
    Rule,
    Structure,
    Term,
    UnaryOperator,
    Variable,
    Wildcard,
    fresh_name,
)

type Environment = Map[Expression[Variable], Variable]

type PythonBody = Callable[[Environment], Goal[Database]]
type PythonGoal = Callable[[Database, Subst, Environment], Step[Database]]

GoalTerm = Atom | Functor | Conjunction | Disjunction | Negation


type Clause = Callable[[QueryTerm, Environment], Goal[Database]]


@dataclass(frozen=True, slots=True)
class SubstProxy(Mapping):
    subst: Subst
    env: Environment

    def __len__(self):
        return len(self.env)

    def __iter__(self):
        for varexpr in self.env.keys():
            try:
                yield (varexpr, self[varexpr])
            except KeyError:
                continue

    def __getitem__(self, varexpr: Expression[Variable]):
        return self.subst.actualize(self.env[varexpr])


@dataclass(frozen=True, slots=True)
class ClauseRunner:
    clause: Clause
    env: Environment

    def __call__(self, query: Term) -> Goal[Database]:
        # unimportant for the problem at hans:
        assert isinstance(query, QueryTerm)

        # create a mapping from the canonical variable exprs to fresh variables:
        fresh_env = Map(
            {var_expr: terms.fresh_variable() for var_expr in self.env.keys()}
        )

        # create a mapping from the ids of the variables in the clause to the freshened
        # ones:
        memo = {
            id(clause_var): fresh_env[var_expr]
            for var_expr, clause_var in self.env.items()
        }
        # greshen the entire clause, replacing its variables with the freshend ones:
        fresh_clause = deepcopy(self.clause, memo=memo)

        # run the thing:
        return fresh_clause(query, fresh_env)


class Database(ChainMap[Indicator, list[ClauseRunner]]):
    def tell(self, *expressions: HasTerm[Atom | Functor | Rule]) -> None:
        for expr in expressions:
            (clause, indicator), env = term_to_clause(expr.term).run(Map())
            runner = ClauseRunner(clause, env)
            self.setdefault(indicator, []).append(runner)

    def ask(
        self, conjunct: Expression, *conjuncts: Expression, subst: Subst | None = None
    ) -> Iterable[Mapping]:
        if conjuncts:
            query = Conjunction(conjunct.term, *(c.term for c in conjuncts))
        else:
            query = conjunct.term
        fresh_query, env = fresh(term=query).run(Map())
        return (
            SubstProxy(new_subst, env) for new_subst in self.resolve(fresh_query, subst)
        )

    def resolve(self, query: Term, subst: Subst | None = None) -> Iterable[Subst]:
        if subst is None:
            subst = Subst()
        goal = resolve(query)
        step = goal(self, subst)
        for new_subst in trampoline(lambda: step(success, failure, failure)):
            yield new_subst


def resolve(query: Term) -> Goal[Database]:
    match query:
        case Atom() | Functor():
            return lambda db, subst: amb_from_iterable(
                clause_runner(query) for clause_runner in db[query.indicator]
            )(db, subst)

        case Conjunction(body=args):
            return seq_from_iterable(resolve(a) for a in args)

        case Disjunction(body=args):
            return amb_from_iterable(resolve(a) for a in args)

        case Invert(args=(inner,)):
            return neg(resolve(inner))

    raise TypeError(f"Type error: `callable' expected, found {query!r}")


@dataclass(frozen=True, slots=True)
class PythonRule(Rule[PythonBody]):
    pass


def to_python_list(cons_list: Term, subst: Subst) -> list[Term]:
    assert isinstance(cons_list, Cons | Empty)
    result = []
    while True:
        match subst.actualize(cons_list):
            case Cons(head=head, tail=tail):
                result.append(head)
                cons_list = tail
            case Empty():
                return result
            case other:
                raise TypeError(f"Expected Cons list, got {other!r}")


def get_mapped_var(var: Variable) -> State[Map, Variable | None]:
    return get_state(lambda env: env.get(Expression(var)))


def map_var(canonical: Variable, renamed: Variable) -> State[Map, Variable | None]:
    return set_state(lambda env: env.set(Expression(canonical), renamed))


@with_state
def fresh_variable(
    old_var: Variable,
) -> StateGenerator[Map, Term]:
    new_var = yield get_mapped_var(old_var)
    if new_var is None:
        new_var = Variable(fresh_name(old_var.name))
        yield map_var(old_var, new_var)
    return new_var


@with_state
def fresh_list(items: Sequence[Term]) -> StateGenerator[Map, tuple[Term, ...]]:
    new_items = []
    for item in items:
        new_item = yield fresh(item)
        new_items.append(new_item)
    return tuple(new_items)


@with_state
def fetch_env() -> StateGenerator[Map, Map]:
    return (yield get_env())


@with_state
def functor(name: str, args: tuple[Term]) -> StateGenerator[Map, Term]:
    return (yield State.unit(Functor(name, *args)))


@with_state
def conjunction(args: tuple[Term]) -> StateGenerator[Map, Term]:
    return (yield State.unit(Conjunction(*args)))


@with_state
def list_to_cons(items: list[Term]) -> StateGenerator[Map, Term]:
    if not items:
        return EMPTY
    head, *tail = items
    new_head = yield fresh(term=head)
    new_tail = yield list_to_cons(tail)
    return Cons(head=new_head, tail=new_tail)


@with_state
def fresh(term: Term | tuple[Term]) -> StateGenerator[Map, Term]:
    match term:
        case str() | int() | float() | bool() | complex():
            return term

        case Wildcard():
            return term

        case Variable():
            return (yield cast(State[Map, Term], fresh_variable(term)))

        case Atom():
            return term

        case Functor(name=name, args=args):
            new_args = yield fresh_list(args)
            return (yield functor(name, new_args))

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

        case Conjunction(body=conjuncts):
            new_conjuncts = yield fresh_list(conjuncts)
            return (yield conjunction(new_conjuncts))

        case tuple() as conjuncts:
            new_conjuncts = yield fresh_list(conjuncts)
            return (yield conjunction(new_conjuncts))

    raise TypeError(f"Unsupported Term node: {term}")


@with_state
def term_to_clause(
    term: Term | PythonRule,
) -> StateGenerator[Map, tuple[Clause, Indicator]]:
    match term:
        case Atom(name=name) as head:
            new_head = yield fresh(head)
            return AtomClause(), (name, None)

        case Structure(name=name, args=args) as head:
            new_args = yield fresh_list(args)
            head_functor = Functor(name, *new_args)
            return StructureClause(head_functor), (head_functor.name, len(new_args))

        case PythonRule(head=Atom(name=name) as head, body=body):
            new_head = yield fresh(head)
            return PythonRuleAtomClause(body), (name, None)

        case PythonRule(head=Structure(name=name, args=args) as head, body=body):
            new_head = yield fresh(head)
            head_functor = Functor(head.name, *new_head.args)
            return PythonRuleStructureClause(head_functor, body), (name, len(args))

        case HornetRule(head=Atom(name=name) as head, body=body):
            new_body_goal = yield fresh(body)
            if body:
                return HornetRuleAtomClause(new_body_goal), (name, None)
            else:
                return HornetRuleAtomClause(None), (name, None)

        case HornetRule(head=Structure(name=name, args=args) as head, body=body):
            new_head = yield fresh(head)
            head_functor = Functor(head.name, *new_head.args)
            if body:
                new_body_goal = yield fresh(body)
                return HornetRuleStructureClause(head_functor, new_body_goal), (
                    name,
                    len(new_head.args),
                )
            else:
                return HornetRuleStructureClause(head_functor, None), (
                    name,
                    len(new_head.args),
                )

    raise TypeError(f"Unsupported Term node: {term}")


@dataclass(frozen=True, slots=True)
class AtomClause:
    def __call__(self, query, env):
        return unit


@dataclass(frozen=True, slots=True)
class StructureClause:
    head: Functor

    def __call__(self, query, env):
        return unify(query, self.head)


@dataclass(frozen=True, slots=True)
class PythonRuleAtomClause:
    body: PythonBody

    def __call__(self, query, env):
        return self.body(env)


@dataclass(frozen=True, slots=True)
class PythonRuleStructureClause:
    head: Functor
    body: PythonBody

    def __call__(self, query, env):
        return seq(unify(query, self.head), self.body(env))


@dataclass(frozen=True, slots=True)
class HornetRuleAtomClause:
    body_goal: Term | None

    def __call__(self, query, env):
        if self.body_goal:
            return resolve(self.body_goal)
        else:
            return unit


@dataclass(frozen=True, slots=True)
class HornetRuleStructureClause:
    head: Functor
    body_goal: Term | None

    def __call__(self, query, env):
        if self.body_goal:
            return seq(unify(query, self.head), resolve(self.body_goal))
        else:
            return unify(query, self.head)


def predicate(
    expr: Expression[Term],
) -> Callable[[PythonGoal], RuleExpression[PythonRule]]:
    head = expr.term
    assert isinstance(head, MatchTerm)

    def decorator(func: PythonGoal) -> RuleExpression[PythonRule]:
        @wraps(func)
        def python_body(env: Environment) -> Goal[Database]:
            def python_goal(db: Database, subst: Subst) -> Step[Database]:
                return func(db, subst, env)

            return python_goal

        return RuleExpression(PythonRule(head=head, body=python_body))

    return decorator
