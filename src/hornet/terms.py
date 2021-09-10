#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.5a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import ast
import collections
import copy
import numbers
import operator
import string

from toolz.functoolz import compose, identity

from .tailcalls import tco, trampoline
from .util import noop, foldr, rpartial, tabulate, const
from .util import first_arg as get_self
from .expressions import is_bitor, is_name
from .operators import make_token, fz, xfx, xfy, yfx


__all__ = [
    'Indicator',
    'UnificationFailed',
    'Wildcard',
    'Variable',
    'Structure',
    'Relation',
    'Atomic',
    'Atom',
    'String',
    'Number',
    'List',
    'Nil',
    'NIL',
    'Implication',
    'Conjunction',
    'Disjunction',
    'Adjunction',
    'Conditional',
    'Addition',
    'Subtraction',
    'Multiplication',
    'Division',
    'FloorDivision',
    'Remainder',
    'Exponentiation',
    'Negation',
    'Positive',
    'Negative',
    'Builder',
    'success',
    'failure',
    'is_nil',
    'Environment',
    'build',
]


def get_name(self):
    return self.name


is_wildcard_name = '_'.__eq__


FIRST_VARIABLE_CHARS = frozenset(string.ascii_uppercase + '_')


def is_variable_name(name):
    return name[0] in FIRST_VARIABLE_CHARS


@property
def first_param(structure):
    return structure.params[0]


@property
def second_param(structure):
    return structure.params[1]


parenthesized = '({})'.format


def comma_separated(items):
    return ', '.join(str(each) for each in items)


Indicator = collections.namedtuple('Indicator', 'functor arity')
Indicator.__str__ = lambda self: '{}/{}'.format(*self)
Indicator.__repr__ = Indicator.__str__


class UnificationFailed(Exception):
    pass


class Wildcard:

    __slots__ = ()

    __call__ = noop
    __str__ = const('_')
    __repr__ = __str__
    __deepcopy__ = get_self

    ref = property(identity)
    fresh = get_self

    unify = noop
    unify_variable = noop
    unify_structure = noop


WILDCARD = Wildcard()


class Variable(collections.Counter):

    __slots__ = 'env', 'name'

    def __init__(self, *, env, name):
        self.env = env
        self.name = name

    def __call__(self):
        return None if self.ref is self else self.ref()

    def __str__(self):
        if self.ref is self:
            return min(
                variable.name
                for variable in self.aliases()
                if variable.env is self.env
            )
        else:
            return str(self.ref)

    __repr__ = __str__
    __eq__ = object.__eq__
    __hash__ = object.__hash__

    def __deepcopy__(self, memo, deepcopy=copy.deepcopy):
        var = deepcopy(self.env, memo)(self.name)
        if self and not var:
            memo[id(self)] = var
            var.update((deepcopy(k, memo), v) for k, v in self.items())
        return var

    def fresh(self, env):
        return env(self.name)

    def aliases(self):
        seen = {self}
        todo = self.keys() - seen
        while todo:
            alias = todo.pop()
            seen.add(alias)
            todo |= alias.keys() - seen
        return seen

    @property
    def ref(self):
        return self.env[self.name]

    @ref.setter
    def ref(self, structure):
        self.env[self.name] = structure

    def unify(self, other, trail):
        other.unify_variable(self, trail)

    def unify_variable(self, other, trail):

        self[other] += 1
        other[self] += 1

        @trail.append
        def rollback_unify_variable(self=self, other=other):
            self[other] -= 1
            other[self] -= 1
            if self[other] < 1:
                del self[other]
                del other[self]

    def unify_structure(self, structure, trail):

        variables = self.aliases()
        for variable in variables:
            variable.ref = structure

        @trail.append
        def rollback_unify_structure(variables=variables):
            for variable in variables:
                variable.ref = variable


def is_cut(term):
    return isinstance(term, Atom) and term.name == 'cut'


class Structure:

    __slots__ = 'env', 'name', 'params', 'actions'

    ref = property(identity)
    head = property(get_self)
    body = property(noop)

    @property
    def indicator(self):
        return Indicator(self.name, len(self.params))

    def __init__(self, *, env, name, params=(), actions=()):
        self.env = env
        self.name = name
        self.params = tuple(params)
        self.actions = list(actions)

    def __repr__(self):
        return str(self)

    def __deepcopy__(self, memo, deepcopy=copy.deepcopy):
        return type(self)(
            env=deepcopy(self.env, memo),
            name=self.name,
            params=[deepcopy(each.ref, memo) for each in self.params],
            actions=self.actions,
        )

    def fresh(self, env):
        return type(self)(
            env=env,
            name=self.name,
            params=[each.fresh(env) for each in self.params],
            actions=self.actions,
        )

    def action(self, db, trail):
        for action in self.actions:
            action(self, self.env, db, trail)

    def unify(self, other, trail):
        other.unify_structure(self, trail)

    def unify_variable(self, variable, trail):
        variable.unify_structure(self, trail)

    def unify_structure(self, other, trail):
        if not isinstance(self, type(other)):
            raise UnificationFailed
        elif self.indicator != other.indicator:
            raise UnificationFailed
        elif self.params:
            for this, that in zip(self.params, other.params):
                this.ref.unify(that.ref, trail)

    def choice_point(self, db):
        trail = []
        for term in db.find_all(self.indicator):
            try:
                term.head.unify(self, trail)
                term.head.action(db, trail)
                self.action(db, trail)
            except UnificationFailed:
                pass
            else:
                yield term.body
            finally:
                while trail:
                    trail.pop()()

    def resolve(self, db):

        def success(cont, *args, **kwargs):
            return [self.env.proxy], cont, args, kwargs

        def failure(*args, **kwargs):
            return (), None, args, kwargs

        return trampoline(
            self._resolve_with_tailcall,
            db=db,
            choice_points=[],
            yes=success,
            no=failure,
            prune=failure,
        )

    @tco
    def _resolve_with_tailcall(self, *, db, choice_points, yes, no, prune):

        choice_point = self.choice_point(db)
        choice_points.append(choice_point)
        here = len(choice_points)

        def prune_here():
            while here <= len(choice_points):
                choice_points.pop().close()
            return no()

        def try_next():
            for goals in choice_point:
                break
            else:
                return prune() if is_cut(self) else no()
            if goals is None:
                #  goals is the empty body of a fact
                return yes(try_next)
            else:
                # goals is a rule body, we need to recurse
                return goals.ref._resolve_with_tailcall(
                    db=db,
                    choice_points=choice_points,
                    yes=yes,
                    no=try_next,
                    prune=prune_here,
                )

        return try_next()


class Atomic(Structure):
    __slots__ = ()
    __call__ = get_name
    __str__ = get_name
    __deepcopy__ = get_self
    fresh = get_self


class Atom(Atomic):
    __slots__ = ()


class String(Atomic):
    __slots__ = ()
    __repr__ = compose("'{}'".format, get_name)


class Number(Atomic):
    __slots__ = ()
    __str__ = compose(str, get_name)


class Nil(Atomic):
    __slots__ = ()
    __call__ = list
    __str__ = const('[]')

    def __init__(self):
        Atomic.__init__(self, env={}, name='[]')


NIL = Nil()
is_nil = rpartial(isinstance, Nil)


class Relation(Structure):

    __slots__ = ()

    __call__ = get_name

    def __str__(self):
        return '{}({})'.format(
            self.name,
            comma_separated(str(each.ref) for each in self.params))


class List(Structure):

    __slots__ = ()

    car = first_param
    cdr = second_param

    def __init__(self, **kwargs):
        Structure.__init__(self, name='.', **kwargs)

    def __call__(self):
        acc = []
        while isinstance(self, List):
            acc.append(self.car.ref())
            self = self.cdr.ref
        return acc if is_nil(self) else acc + [self]

    def __str__(self):
        acc = []
        while isinstance(self, List):
            acc.append(self.car.ref)
            self = self.cdr.ref
        if is_nil(self):
            return '[{}]'.format(comma_separated(acc))
        return '[{}|{}]'.format(comma_separated(acc), self)

    def __deepcopy__(self, memo):
        return List(
            env=copy.deepcopy(self.env, memo),
            params=[copy.deepcopy(each.ref, memo) for each in self.params],
            actions=self.actions)

    def fresh(self, env):
        return List(
            env=env,
            params=[each.fresh(env) for each in self.params],
            actions=self.actions)


class PrefixOperator(Structure):

    __slots__ = ()

    operand = first_param

    def __call__(self):
        return self.op(self.operand.ref())

    def __str__(self):

        operand = self.operand.ref

        op_fixity = make_token(OPERATOR_FIXITIES, self)
        operand_fixity = make_token(OPERATOR_FIXITIES, operand)

        if operand_fixity.left_rank and op_fixity > operand_fixity:
            operand_str = parenthesized
        else:
            operand_str = str

        return '{}{}'.format(self.name, operand_str(operand))


class InfixOperator(Structure):

    __slots__ = ()

    left = first_param
    right = second_param

    def __call__(self):
        return self.op(self.left.ref(), self.right.ref())

    def __str__(self):

        left = self.left.ref
        right = self.right.ref

        op_fixity = make_token(OPERATOR_FIXITIES, self)
        left_fixity = make_token(OPERATOR_FIXITIES, left)
        right_fixity = make_token(OPERATOR_FIXITIES, right)

        if left_fixity.right_rank and left_fixity < op_fixity:
            left_str = parenthesized
        else:
            left_str = str

        if right_fixity.left_rank and op_fixity > right_fixity:
            right_str = parenthesized
        else:
            right_str = str

        return '{} {} {}'.format(left_str(left), self.name, right_str(right))


class Implication(InfixOperator):

    __slots__ = ()

    # reverse implication: l << r
    def op(left, right):
        return left or not right

    head = first_param
    body = second_param

    @tco
    def _resolve_with_tailcall(self, *, db, choice_points, yes, no, prune):
        raise TypeError("Implication '{}' is not a valid goal.".format(self))


class Conjunction(InfixOperator):

    __slots__ = ()
    op = operator.and_

    @tco
    def _resolve_with_tailcall(self, *, db, choice_points, yes, no, prune):

        def try_right(retry_left_then_right):
            return self.right.ref._resolve_with_tailcall(
                db=db,
                choice_points=choice_points,
                yes=yes,
                no=retry_left_then_right,
                prune=prune,
            )

        def try_left_then_right():
            return self.left.ref._resolve_with_tailcall(
                db=db,
                choice_points=choice_points,
                yes=try_right,
                no=no,
                prune=prune,
            )

        return try_left_then_right()


class Disjunction(InfixOperator):
    __slots__ = ()
    op = operator.xor


class Adjunction(InfixOperator):
    __slots__ = ()
    op = operator.or_


class Conditional(InfixOperator):
    __slots__ = ()
    op = operator.rshift


class Addition(InfixOperator):
    __slots__ = ()
    op = operator.add


class Subtraction(InfixOperator):
    __slots__ = ()
    op = operator.sub


class Multiplication(InfixOperator):
    __slots__ = ()
    op = operator.mul


class Division(InfixOperator):
    __slots__ = ()
    op = operator.truediv


class FloorDivision(InfixOperator):
    __slots__ = ()
    op = operator.floordiv


class Remainder(InfixOperator):
    __slots__ = ()
    op = operator.mod


class Exponentiation(InfixOperator):
    __slots__ = ()
    op = operator.pow


class Negation(PrefixOperator):
    __slots__ = ()
    op = operator.invert


class Positive(PrefixOperator):
    __slots__ = ()
    op = operator.pos


class Negative(PrefixOperator):
    __slots__ = ()
    op = operator.neg


var_suffix_map = collections.defaultdict(lambda: tabulate('_{:02X}?'.format))


class Environment(dict):

    def __call__(self, name):
        try:
            return self[name]
        except KeyError:
            var = self[name] = Variable(env=self, name=name)
            return var

    def __getattr__(self, name):
        return self[name].ref

    def __deepcopy__(self, memo):
        env = memo[id(self)] = Environment()
        return env

    def rename_vars(self):
        for variable in list(self.values()):
            if isinstance(variable, Variable):
                variable.name += next(var_suffix_map[variable.name])
                self[variable.name] = variable

    @property
    class proxy(collections.ChainMap):

        def __getitem__(self, key):
            return collections.ChainMap.__getitem__(self, str(key))

        def __repr__(self):
            return 'Environment.{}'.format(super().__repr__())

        __str__ = __repr__


OPERATOR_FIXITIES = {
    Adjunction: xfy(10),
    Disjunction: xfy(20),
    Conjunction: xfy(30),
    Implication: xfx(4),
    Conditional: xfx(7),
    Addition: yfx(50),
    Subtraction: yfx(50),
    Multiplication: yfx(60),
    Division: yfx(60),
    FloorDivision: yfx(60),
    Remainder: yfx(60),
    Negative: fz(70),
    Positive: fz(70),
    Negation: fz(70),
    Exponentiation: xfy(80),
}


def visit_op(op_class, op_name):
    def visit(self, node):
        self.append(op_class(env=self.env, name=op_name, params=self.pop()))
    return visit


class Builder(ast.NodeVisitor):

    def __init__(self, env):
        self.env = env
        self.stack = []

    def push(self):
        self.stack.append([])

    def pop(self):
        return self.stack.pop()

    def top(self):
        return self.stack[-1]

    def toptop(self):
        return self.stack[-1][-1]

    def append(self, item):
        self.top().append(item)

    def build(self, node):
        assert self.stack == []
        self.push()
        self.visit(node)
        assert 1 == len(self.stack) == len(self.stack[0])
        return self.pop().pop()

    def visit_Name(self, node):
        if is_wildcard_name(node.id):
            self.append(WILDCARD)
        elif is_variable_name(node.id):
            self.append(self.env(node.id))
        else:
            self.append(Atom(env=self.env, name=node.id))

    def visit_Constant(self, node):
        if isinstance(node.value, numbers.Number):
            self.append(Number(env=self.env, name=node.value))
        elif isinstance(node.value, str):
            self.append(String(env=self.env, name=node.value))
        else:
            raise ValueError("node must be of type str or Number!")

    def visit_Tuple(self, node):
        raise TypeError('Tuples are not allowed: {}'.format(node))

    def cons(self, car, cdr):
        return List(env=self.env, params=[car, cdr])

    def visit_List(self, node):

        if node.elts:

            self.push()

            *elts, last = node.elts

            for each in elts:
                self.visit(each)

            if is_bitor(last):
                self.visit(last.left)
                self.visit(last.right)
                *items, left, right = self.pop()
                cdr = self.cons(left, right)

            else:
                self.visit(last)
                *items, last = self.pop()
                cdr = self.cons(last, NIL)

            self.append(foldr(self.cons, items, cdr))

        else:
            self.append(NIL)

    def visit_Set(self, node):
        raise TypeError('Sets are not allowed: {}'.format(node))

    def visit_Dict(self, node):
        raise TypeError('Dicts are not allowed: {}'.format(node))

    def visit_AstWrapper(self, node):
        raise TypeError('Invalid node {} of type {} found'
                        .format(node, type(node)))

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.toptop().actions.extend(node.slice)

    def visit_Call(self, node):
        if not is_name(node.func):
            raise TypeError('{} is not a valid functor name.'
                            .format(node.func))
        if node.keywords:
            raise TypeError('Keyword arguments are not allowed: {}'
                            .format(node))
        if node.starargs:
            raise TypeError('Starred arguments are not allowed: {}'
                            .format(node))
        if node.kwargs:
            raise TypeError('Starred keyword arguments are not allowed: {}'
                            .format(node))
        self.push()
        for each in node.args:
            self.visit(each)
        args = self.pop()
        assert len(args) == len(node.args)
        self.append(Relation(env=self.env, name=node.func.id, params=args))

    def visit_UnaryOp(self, node):
        self.push()
        self.visit(node.operand)
        self.visit(node.op)

    def visit_BinOp(self, node):
        self.push()
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.op)

    visit_Invert = visit_op(Negation, '~')
    visit_UAdd = visit_op(Positive, '+')
    visit_USub = visit_op(Negative, '-')
    visit_Add = visit_op(Addition, '+')
    visit_Sub = visit_op(Subtraction, '-')
    visit_Mult = visit_op(Multiplication, '*')
    visit_Div = visit_op(Division, '/')
    visit_FloorDiv = visit_op(FloorDivision, '//')
    visit_Mod = visit_op(Remainder, '%')
    visit_Pow = visit_op(Exponentiation, '**')
    visit_RShift = visit_op(Conditional, '>>')
    visit_LShift = visit_op(Implication, '<<')
    visit_BitAnd = visit_op(Conjunction, '&')
    visit_BitXor = visit_op(Disjunction, '^')
    visit_BitOr = visit_op(Adjunction, '|')


def build(node):
    return Builder(Environment()).build(node)


# class PythonBuilder:

    # def build_Wildcard(self, node):
    # pass

    # def build_Variable(self, node):
    # pass

    # def build_Relation(self, node):
    # pass

    # def build_Atom(self, node):
    # pass

    # def build_String(self, node):
    # pass

    # def build_Num(self, node):
    # pass

    # def build_List(self, node):
    # pass

    # def build_Nil(self, node):
    # pass

    # def build_Implication(self, node):
    # pass

    # def build_Conjunction(self, node):
    # pass

    # def build_Disjunction(self, node):
    # pass

    # def build_Adjunction(self, node):
    # pass

    # def build_Conditional(self, node):
    # pass

    # def build_Addition(self, node):
    # pass

    # def build_Subtraction(self, node):
    # pass

    # def build_Multiplication(self, node):
    # pass

    # def build_Division(self, node):
    # pass

    # def build_FloorDivision(self, node):
    # pass

    # def build_Remainder(self, node):
    # pass

    # def build_Exponentiation(self, node):
    # pass

    # def build_Negation(self, node):
    # pass

    # def build_Positive(self, node):
    # pass

    # def build_Negative(self, node):
    # pass
