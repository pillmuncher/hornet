from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache, reduce
from typing import Callable, Iterable, Self

from immutables import Map

from .tailcalls import Frame, tailcall
from .terms import Atom, Functor, Structure, Term, Variable, Wildcard

type Result = Frame[Subst]
type Next = Callable[[], Result]
type Emit[Ctx] = Callable[[Ctx, Subst, Next], Result]
type Step[Ctx] = Callable[[Emit[Ctx], Next, Next], Result]
type Goal[Ctx] = Callable[[Ctx, Subst], Step[Ctx]]
type Executable = Callable[[Head], Goal]
type Head = Atom | Functor


@dataclass(frozen=True, slots=True)
class Subst(Mapping[Variable, Term]):
    map: Map = field(default_factory=Map)

    def clone_with(self, variable: Variable, value: Term) -> Self:
        return type(self)(self.map.set(variable, value))

    @cache
    def actualize(self, obj) -> Term:
        match self[obj]:
            case Functor(name=name, args=args):
                return Functor(name, *(self.actualize(a) for a in args))
            case Structure(args=args) as struct:
                return type(struct)(*(self.actualize(a) for a in args))
            case obj:
                return obj

    def __getitem__(self, obj) -> Term:
        visited = set()
        while isinstance(obj, Variable) and obj in self.map:
            if obj in visited:
                raise RuntimeError(f"Cyclic variable binding detected: {obj}")
            visited.add(obj)
            obj = self.map[obj]
        return obj

    def __iter__(self):
        return iter(self.map)

    def __len__(self):
        return len(self.map)


@dataclass(frozen=True, slots=True)
class start_query[Ctx]:
    step: Step[Ctx]

    def __call__(self) -> Result:
        return self.step(success, failure, failure)


def success[Ctx](ctx: Ctx, subst: Subst, no: Next) -> Result:
    return subst, no


def failure() -> Result:
    pass


@dataclass(frozen=True, slots=True)
class on_success[Ctx]:
    goal: Goal[Ctx]
    yes: Emit[Ctx]
    prune: Next

    @tailcall
    def __call__(self, ctx: Ctx, subst: Subst, no: Next) -> Result:
        return self.goal(ctx, subst)(self.yes, no, self.prune)


@dataclass(frozen=True, slots=True)
class bind[Ctx]:
    step: Step[Ctx]
    goal: Goal[Ctx]

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return self.step(on_success(self.goal, yes, prune), no, prune)


@dataclass(frozen=True, slots=True)
class unit[Ctx]:
    ctx: Ctx
    subst: Subst

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return yes(self.ctx, self.subst, no)


@dataclass(frozen=True, slots=True)
class cut[Ctx]:
    ctx: Ctx
    subst: Subst

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return yes(self.ctx, self.subst, prune)


@tailcall
def fail_step[Ctx](yes: Emit[Ctx], no: Next, prune: Next) -> Result:
    return no()


def fail[Ctx](ctx: Ctx, subst: Subst) -> Step[Ctx]:
    return fail_step


@dataclass(frozen=True, slots=True)
class then[Ctx]:
    goal1: Goal[Ctx]
    goal2: Goal[Ctx]

    def __call__(self, ctx: Ctx, subst: Subst) -> Step[Ctx]:
        return bind(self.goal1(ctx, subst), self.goal2)


def seq_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    return reduce(then, goals, unit)


def seq[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    return seq_from_iterable(goals)


@dataclass(frozen=True, slots=True)
class on_failure[Ctx]:
    goal: Goal[Ctx]
    ctx: Ctx
    subst: Subst
    yes: Emit[Ctx]
    no: Next
    prune: Next

    @tailcall
    def __call__(self) -> Result:
        return self.goal(self.ctx, self.subst)(self.yes, self.no, self.prune)


@dataclass(frozen=True, slots=True)
class choice_step[Ctx]:
    goal1: Goal[Ctx]
    goal2: Goal[Ctx]
    ctx: Ctx
    subst: Subst

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return self.goal1(self.ctx, self.subst)(
            yes,
            on_failure(self.goal2, self.ctx, self.subst, yes, no, prune),
            prune,
        )


@dataclass(frozen=True, slots=True)
class choice[Ctx]:
    goal1: Goal[Ctx]
    goal2: Goal[Ctx]

    def __call__(self, ctx: Ctx, subst: Subst) -> Step[Ctx]:
        return choice_step(self.goal1, self.goal2, ctx, subst)


@dataclass(frozen=True, slots=True)
class amb_step[Ctx]:
    goal: Goal[Ctx]
    ctx: Ctx
    subst: Subst

    @tailcall
    def __call__(self, yes: Emit[Ctx], no: Next, prune: Next) -> Result:
        return self.goal(self.ctx, self.subst)(yes, no, no)


@dataclass(frozen=True, slots=True)
class amb_goal[Ctx]:
    goal: Goal[Ctx]

    def __call__(self, ctx: Ctx, subst: Subst) -> Step[Ctx]:
        return amb_step(self.goal, ctx, subst)


def amb_from_iterable[Ctx](goals: Iterable[Goal[Ctx]]) -> Goal[Ctx]:
    return amb_goal(reduce(choice, goals, fail))


def amb[Ctx](*goals: Goal[Ctx]) -> Goal[Ctx]:
    return amb_from_iterable(goals)


def neg[Ctx](goal: Goal[Ctx]) -> Goal[Ctx]:
    return amb(seq(goal, cut, fail), unit)


@dataclass(frozen=True, slots=True)
class _unify_variable[Ctx]:
    variable: Variable
    term: Term

    def __call__(self, ctx: Ctx, subst: Subst) -> Step[Ctx]:
        value = subst[self.variable]
        if value is self.variable:
            return unit(ctx, subst.clone_with(self.variable, self.term))
        else:
            return tailcall(_unify(value, self.term)(ctx, subst))


def _unify[Ctx](this: Term, that: Term) -> Goal[Ctx]:
    match this, that:
        case _ if this == that:
            return unit

        case Wildcard(), _:
            return unit

        case _, Wildcard():
            return unit

        case Variable(), _:
            return _unify_variable(this, that)

        case _, Variable():
            return _unify_variable(that, this)

        case Structure(), Structure():
            if this.indicator == that.indicator:
                return unify_pairs(*zip(this.args, that.args))
            else:
                return fail

        case _:
            return fail


@dataclass(frozen=True, slots=True, init=False)
class unify_pairs[Ctx]:
    pairs: tuple[tuple[Term, Term], ...]

    def __init__(self, *pairs: tuple[Term, Term]) -> None:
        object.__setattr__(self, "pairs", pairs)

    def __call__(self, ctx: Ctx, subst: Subst) -> Step[Ctx]:
        return tailcall(
            seq_from_iterable(
                _unify(subst[this], subst[that]) for this, that in self.pairs
            )(ctx, subst)
        )


@dataclass(frozen=True, slots=True)
class unify[Ctx]:
    this: Term
    that: Term

    def __call__(self, ctx: Ctx, subst: Subst) -> Step[Ctx]:
        return _unify(subst[self.this], subst[self.that])(ctx, subst)


def unify_any[Ctx](variable: Variable, *values: Term) -> Goal[Ctx]:
    return amb_from_iterable(unify(variable, value) for value in values)
