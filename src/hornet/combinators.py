# Copyright (c) 2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections import ChainMap
from collections.abc import Mapping
from copy import deepcopy
from functools import reduce
from typing import Callable, Iterable

from .expressions import Expression
from .tailcalls import Frame, tailcall, trampoline
from .terms import (
    AnonVariable,
    Atom,
    BitAnd,
    BitOr,
    Cons,
    Empty,
    Functor,
    Indicator,
    LShift,
    RShift,
    Structure,
    Term,
    Variable,
)

type Result = Frame[Subst]
type Next = Callable[[], Result]
type Emit = Callable[[Database, Subst, Next], Result]
type Step = Callable[[Emit, Next, Next], Result]
type Goal = Callable[[Database, Subst], Step]

type MatchTerm = Atom | Functor
type QueryTerm = Atom | BitAnd | BitOr | Functor | Variable
type ClauseTerm = Atom | Functor | LShift | RShift
type Clause = Callable[[QueryTerm], Goal]


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
        # TODO: make it not blow the stack, i.e. replace recursion with tail-calls.
        match self.deref(obj):
            case Functor(name=name, args=args) as struct:
                return type(struct)(name, *(self.smooth(each) for each in args))
            case Structure(args=args) as struct:
                return type(struct)(*(self.smooth(each) for each in args))
            case term:
                return term

    @property
    class proxy(Mapping):
        "A proxy interface to Subst."

        def __init__(self, subst: Subst):
            self._subst = subst

        def __iter__(self):
            return iter(self._subst)

        def __len__(self):
            return len(self._subst)

        def __getitem__(self, variable: Expression[Variable]):
            if variable.term == (frame := self._subst.smooth(variable.term)):
                raise KeyError
            return frame


def dcg_expand(head: MatchTerm, body: QueryTerm) -> tuple[MatchTerm, QueryTerm]:
    """
    Expand a DCG-style rule (head >> body) into standard Horn clauses
    using difference lists.

    Each non-terminal predicate gets two extra arguments representing
    the input and output lists. Terminals (Cons cells of atoms) are
    expanded into unifications with the input list.
    """
    S0 = Variable.fresh("S")

    def walk(term, inp):
        match term:
            case Atom(name=name):
                # Atoms become Functors with two parameters
                out = Variable.fresh("S")
                return Functor(name, inp, out), out

            case Functor(name=name, args=args) as term:
                # Functors become Functors with two more parameters
                out = Variable.fresh("S")
                return Functor(name, *args, inp, out), out

            case Empty():
                # The empty list consumes nothing
                return Functor("equal", inp, inp), inp

            case Cons(head=head, tail=Empty() as tail):
                # Recursively build the difference list
                return Functor("equal", inp, Cons(head, inp)), inp

            case Cons(head=head, tail=tail):
                # Recursively build the difference list
                tail_term, tail_out = walk(tail, Variable.fresh("S"))
                return Functor("equal", inp, Cons(head, tail_term)), tail_out

            case BitAnd(left=left, right=right):
                # Thread from left to right
                left_term, left_out = walk(left, inp)
                right_term, right_out = walk(right, left_out)
                return BitAnd(left_term, right_term), right_out

            case BitOr(left=left, right=right):
                # Thread left and right alternatives
                left_term, left_out = walk(left, inp)
                right_term, right_out = walk(right, inp)
                final_out = Variable.fresh("S")
                left_conj = BitAnd(left_term, Functor("equal", left_out, final_out))
                right_conj = BitAnd(right_term, Functor("equal", right_out, final_out))
                return BitOr(left_conj, right_conj), final_out

            case Variable():
                # Pass-through variable in DCG body
                return term, inp

            case _:
                raise ValueError(f"Unexpected term in DCG body: {term}")

    # Expand the body
    body_expanded, final_out = walk(body, S0)

    # Expand head with S0 and final_out
    match head:
        case Atom(name=name):
            head_expanded = Functor(name, S0, final_out)
        case Functor(name=name, args=args):
            head_expanded = Functor(name, *args, S0, final_out)

    return head_expanded, body_expanded


def fact(head: MatchTerm) -> Clause:
    """Create a Horn clause that represents a fact.

    Facts are statements that are always true in the knowledge base. This
    function returns a clause that can unify a query term with the fact's head.
    """

    def clause(query_term: QueryTerm) -> Goal:
        fresh_head = deepcopy(head)
        return unify(query_term, fresh_head)

    return clause


def rule(head: MatchTerm, body: QueryTerm) -> Clause:
    """Create a Horn clause that represents a rule.

    Rules relate a head to a body of conditions. This function returns a clause
    that first unifies the head and then resolves the body.
    """

    def clause(query_term: QueryTerm) -> Goal:
        # copy head and body at the same time to preserve common variables:
        fresh_head, fresh_body = deepcopy((head, body))
        return then(unify(query_term, fresh_head), resolve(fresh_body))

    return clause


def resolve(term: Term) -> Goal:
    """Convert a term into a monadic goal suitable for resolution.

    This function interprets different types of terms (atoms, functors,
    conjunctions, disjunctions, and variables) and returns a Goal that can
    be executed in the logic programming monad.
    """
    match term:
        # Atomic or structured goals: find all clauses matching this term
        # in the database. Each clause represents a possible path of execution.
        case Atom() | Functor() as head:
            return lambda db, subst: amb_from_iterable(
                clause(head) for clause in db[term.indicator]
            )(db, subst)

        # Conjunction goals: both left and right must succeed.
        case BitAnd(left=left, right=right):
            return then(resolve(left), resolve(right))

        # Disjunction goals: either left or right can satisfy the query.
        case BitOr(left=left, right=right):
            return choice(resolve(left), resolve(right))

        # Variable goals: substitute the variable for the term it is bound to.
        # If the variable isn't bound, a KeyError is raised.
        case Variable() as variable:
            return lambda db, subst: tailcall(resolve(subst[variable])(db, subst))

        # Everything else is invalid.
        case _:
            raise TypeError(f"expected clause, got {term}")


class Database(dict[Indicator, list[Clause]]):
    """A container for storing Horn clauses, indexed by their indicator.

    The database supports facts, rules, and DCG-expanded clauses. Queries
    are resolved against the clauses in this database.
    """

    def add(self, *clause_exprs: Expression[ClauseTerm]) -> None:
        """Add clauses to the database.

        Each expression is normalized and categorized as a fact, rule, or DCG
        construct. The corresponding Clause is then added to the database.
        """
        for clause_expr in clause_exprs:
            match clause_expr.term.normalize(0, 0):
                # Single atoms or functors represent facts:
                # statements that are always true.
                case Atom() | Functor() as term:
                    self.setdefault(term.indicator, []).append(fact(term))

                # Left-shift expressions represent rules:
                # head is true if body is true.
                case LShift(head=head, body=body):
                    if not isinstance(head, Atom | Functor):
                        raise ValueError(f"invalid head clause {head}")
                    if not isinstance(body, Atom | BitAnd | BitOr | Functor | Variable):
                        raise ValueError(f"invalid body clause {body}")
                    self.setdefault(head.indicator, []).append(rule(head, body))

                # Right-shift expressions represent DCG rules.
                case RShift(head=head, body=body) as term:
                    if not isinstance(head, Atom | Functor):
                        raise ValueError(f"invalid head clause {term.head}")
                    if not isinstance(
                        body, (Atom | BitAnd | BitOr | Functor | Variable)
                    ):
                        raise ValueError(f"invalid body clause {term.body}")
                    # Expand to standard clauses before adding to the database.
                    head, body = dcg_expand(head, body)
                    self.setdefault(head.indicator, []).append(rule(head, body))

    def ask(
        self, query: Expression[QueryTerm], subst: Subst | None = None
    ) -> Iterable[Mapping]:
        """Query the database for solutions.

        Returns an iterator of substitution mappings that satisfy the query.
        Each mapping represents a consistent set of variable bindings.
        """
        term = query.term.normalize(0, 0)
        goal = resolve(term)
        step = goal(self, Subst() if subst is None else subst)
        for subst in trampoline(lambda: step(success, failure, failure)):
            yield subst.proxy


def success(db: Database, subst: Subst, no: Next) -> Result:
    "Return the current solution and start searching for more."
    return subst, no


def failure() -> Result:
    "Fail."


def bind(step: Step, goal: Goal) -> Step:
    "Return the frame of applying goal to step."

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
    "Succeed once, then prune the search tree at the previous choice point."

    @tailcall
    def step(yes: Emit, no: Next, prune: Next) -> Result:
        # we commit to the current execution path by injecting
        # the prune continuation as our new backtracking path:
        return yes(db, subst, prune)

    return step


def fail(db: Database, subst: Subst) -> Step:
    """Ignore the argument and start backtracking. Represents failure.
    Together with 'choice', this makes the monad also a monoid. Together
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
    "Invert the frame of a monadic computation, AKA negation as failure."
    return amb(seq(goal, cut, fail), unit)


def _unify_variable(variable: Variable, term: Term) -> Goal:
    def unifier(db: Database, subst: Subst) -> Step:
        if variable in subst:
            # variable is already bound, so try to unify the bound thing:
            return tailcall(_unify(subst[variable], term)(db, subst))
        else:
            # otherwise just create a new binding:
            return unit(db, subst.new_child({variable: term}))

    return unifier


def _unify(this: Term, that: Term) -> Goal:
    match this, that:
        # Anonymous variable "_" matches anything and never binds:
        # This implements "don't-care" semantics.
        case AnonVariable(), _:
            return unit

        # Same as above, but with swapped arguments:
        case _, AnonVariable():
            return unit

        # Equal things are already unified:
        case _ if this == that:
            return unit

        # Unify a Variable to another thing:
        case Variable(), _:
            return _unify_variable(this, that)

        # Same as above, but with swapped arguments:
        case _, Variable():
            return _unify_variable(that, this)

        # Two Structures can be unified only if both have the same name and arity
        # and their elements can be unified:
        case Structure(), Structure() if this.indicator == that.indicator:
            return unify_pairs(*zip(this.args, that.args))

        # Unification failed:
        case _:
            return fail


# Public interface to _unify:
def unify_pairs(*pairs: tuple[Term, Term]) -> Goal:
    """Unify 'this' and 'that'.
    If at least one is an unbound Variable, bind it to the other object.
    If both are either lists or tuples, try to unify them recursively.
    Otherwise, unify them if they are equal."""
    return lambda db, subst: tailcall(
        seq_from_iterable(
            _unify(subst.deref(this), subst.deref(that)) for this, that in pairs
        )(db, subst)
    )


def unify(this: Term, that: Term) -> Goal:
    """Unify 'this' and 'that'.
    If at least one is an unbound Variable, bind it to the other object.
    If both are either lists or tuples, try to unify them recursively.
    Otherwise, unify them if they are equal."""
    return lambda db, subst: tailcall(
        _unify(subst.deref(this), subst.deref(that))(db, subst)
    )


def unify_any(variable: Variable, *values: Term) -> Goal:
    """Tries to unify a variable with any one of objects.
    Fails if no object is unifiable."""
    return amb_from_iterable(unify(variable, value) for value in values)
