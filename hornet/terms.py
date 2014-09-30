#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import ast
import collections
import contextlib
import copy
import functools
import operator
import string

from .util import identity, noop, const, foldr, compose2 as compose, method_of
from .util import first_arg as get_self, rpartial
from .expressions import mcompose, mapply
from .operators import fy, xfx, xfy, yfx, make_token, is_bitor, rearrange
from .dcg import dcg_expand


def get_name(self):
    return self.name


is_wildcard_name = '_'.__eq__
is_variable_name = compose(
    operator.itemgetter(0),
    set(string.ascii_uppercase + '_').__contains__)


first_param = compose(operator.attrgetter('params'), operator.itemgetter(0))
second_param = compose(operator.attrgetter('params'), operator.itemgetter(1))


parenthesized = '({})'.format
comma_separated = compose(functools.partial(map, str), ', '.join)


def action_str(term):
    if term.actions:
        return '[{}]'.format(', '.join(a.__name__ for a in term.actions))
    else:
        return ''


Indicator = collections.namedtuple('Indicator', 'name arity')


@method_of(Indicator)
def __str__(self):
    return '{}/{}:'.format(*self)


class UnificationFailed(Exception):
    pass


class Cut(Exception):
    pass


class Wildcard:

    __slots__ = ()

    __call__ = noop
    __str__ = '_'.__str__
    __repr__ = __str__
    __deepcopy__ = get_self

    deref = property(identity)
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
        return None if self.deref is self else self.deref()

    def __str__(self):
        return self.name if self.deref is self else str(self.deref)

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

    @property
    def deref(self):
        return self.env[self.name]

    @deref.setter
    def ref(self, target):
        self.env[self.name] = target

    def keep_positive(self):
        non_positive = [k for k, v in self.items() if v <= 0]
        for each in non_positive:
            del self[each]

    def unify(self, other, trail):
        other.unify_variable(self, trail)

    def unify_variable(self, other, trail):
        @trail
        def rollback(self=self, other=other, deref=other.deref):
            self[other] -= 1
            other[self] -= 1
            other.ref = deref
        self[other] += 1
        other[self] += 1
        other.ref = self

    def unify_structure(self, other, trail):
        variables = collections.deque()
        seen = set()
        todo = {self}
        while todo:
            variable = todo.pop()
            variable.keep_positive()
            variable.ref = other
            seen.add(variable)
            todo |= variable.keys() - seen
            variables.appendleft(variable)
        @trail
        def rollback(variables=variables):
            for variable in variables:
                variable.ref = variable


class Structure:

    __slots__ = 'env', 'name', 'params', 'actions'

    deref = property(identity)

    @property
    def arity(self):
        return len(self.params)

    @property
    def indicator(self):
        return Indicator(self.name, len(self.params))

    def __init__(self, *, env, name, params=(), actions=()):
        self.env = env
        self.name = name
        self.params = params
        self.actions = list(actions)

    def __repr__(self):
        return str(self)

    def __deepcopy__(self, memo, deepcopy=copy.deepcopy):
        return type(self)(
            env=deepcopy(self.env, memo),
            name=self.name,
            params=[deepcopy(each, memo) for each in self.params],
            actions=self.actions)

    def fresh(self, env):
        return type(self)(
            env=env,
            name=self.name,
            params=[each.fresh(env) for each in self.params],
            actions=self.actions)

    def action(self, *args, **kwargs):
        for each_action in self.actions:
            each_action(self, self.env, *args, **kwargs)

    def unify(self, other, trail):
        other.unify_structure(self, trail)

    def unify_variable(self, variable, trail):
        variable.unify_structure(self, trail)

    def unify_structure(self, other, trail):
        if type(self) != type(other):
            raise UnificationFailed
        elif self.indicator != other.indicator:
            raise UnificationFailed
        elif self.params:
            for this, that in zip(self.params, other.params):
                this.deref.unify(that.deref, trail)

    def resolve(self, db):
        with cut_parent(self):
            for head, body in db.find_all(self.indicator):
                with trailing() as trail:
                    self.unify(head, trail)
                    self.action(db, trail)
                    head.action(db, trail)
                    if body is None:
                        yield
                        continue
                    body = body.deref
                    if not isinstance(body, Conjunction):
                        yield from body.resolve(db)
                        continue
                    stack = [(None, None)]
                    running = body.left.deref.resolve(db)
                    waiting = body.right
                    while running:
                        for _ in running:
                            break
                        else:
                            running, waiting = stack.pop()
                            continue
                        descent = waiting.deref
                        if not isinstance(descent, Conjunction):
                            yield from descent.resolve(db)
                            continue
                        stack.append((running, waiting))
                        running = descent.left.deref.resolve(db)
                        waiting = descent.right


class Relation(Structure):

    __slots__ = ()

    __call__ = get_name

    def __str__(self):
        return '{}({}){}'.format(
            self.name,
            comma_separated(str(each.deref) for each in self.params),
            action_str(self))


class Atom(Structure):

    __slots__ = ()

    __call__ = get_name
    __deepcopy__ = get_self

    def __str__(self):
        return '{}{}'.format(self.name, action_str(self))

    fresh = get_self


class String(Structure):

    __slots__ = ()

    __call__ = get_name
    __str__ = get_name
    __repr__ = compose(get_name, "'{}'".format)
    __deepcopy__ = get_self

    fresh = get_self


class Num(Structure):

    __slots__ = ()

    __call__ = get_name
    __str__ = compose(get_name, str)
    __deepcopy__ = get_self

    fresh = get_self


class PrefixOperator(Structure):

    __slots__ = ()

    operand = property(first_param)

    def __call__(self):
        return self.op(self.operand.deref())

    def __str__(self):

        operand = self.operand.deref

        op_fixity = make_token(operator_fixities, self)
        operand_fixity = make_token(operator_fixities, operand)

        if operand_fixity.lbp and op_fixity >= operand_fixity:
            operand_str = parenthesized
        else:
            operand_str = str

        return '{}{}'.format(self.name, operand_str(operand))


class InfixOperator(Structure):

    __slots__ = ()

    left = property(first_param)
    right = property(second_param)

    def __call__(self):
        return self.op(self.left.deref(), self.right.deref())

    def __str__(self):

        left = self.left.deref
        right = self.right.deref

        op_fixity = make_token(operator_fixities, self)
        left_fixity = make_token(operator_fixities, left)
        right_fixity = make_token(operator_fixities, right)

        if left_fixity.rbp and left_fixity < op_fixity:
            left_str = parenthesized
        else:
            left_str = str

        if right_fixity.lbp and op_fixity > right_fixity:
            right_str = parenthesized
        else:
            right_str = str

        return '{} {} {}'.format(left_str(left), self.name, right_str(right))


class Nil(Structure):

    __slots__ = ()

    def __init__(self):
        Structure.__init__(self, env={}, name='[]')

    __call__ = const([])
    __str__ = '[]'.__str__
    __deepcopy__ = get_self

    fresh = get_self


NIL = Nil()


class List(InfixOperator):

    __slots__ = ()

    car = InfixOperator.left
    cdr = InfixOperator.right

    def __init__(self, **kwargs):
        Structure.__init__(self, name='.', **kwargs)

    def __deepcopy__(self, memo, deepcopy=copy.deepcopy):
        return List(
            env=deepcopy(self.env, memo),
            params=[deepcopy(each, memo) for each in self.params],
            actions=self.actions)

    def fresh(self, env):
        return List(
            env=env,
            params=[each.fresh(env) for each in self.params],
            actions=self.actions)

    def __call__(self):
        acc = []
        while isinstance(self, List):
            acc.append(self.car.deref())
            self = self.cdr.deref
        return acc if self == NIL else acc + [self]

    def __str__(self):
        acc = []
        while isinstance(self, List):
            acc.append(self.car.deref)
            self = self.cdr.deref
        if self == NIL:
            return '[{}]'.format(comma_separated(acc))
        return '[{}|{}]'.format(comma_separated(acc), self)


class Implication(InfixOperator):
    __slots__ = ()
    op = lambda left, right: left or not right  # reverse implication: l << r

class Conjunction(InfixOperator):
    __slots__ = ()
    op=operator.and_

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



operator_fixities = {
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
    Negative: fy(70),
    Positive: fy(70),
    Negation: fy(70),
    Exponentiation: xfy(80),
}


@contextlib.contextmanager
def cut_parent(term=NIL):
    try:
        yield
    except Cut as cut:
        pass
    if not isinstance(term, String) and term.name == 'cut':
        raise Cut()


@contextlib.contextmanager
def trailing():
    rollback_funcs = collections.deque()
    try:
        yield rollback_funcs.appendleft
    except UnificationFailed:
        pass
    finally:
        for rollback in rollback_funcs:
            rollback()


class Environment(dict):

    def __call__(self, name, dict_getitem=dict.__getitem__, str=str):
        try:
            return dict_getitem(self, str(name))
        except KeyError:
            var = self[name] = Variable(env=self, name=name)
            return var

    def __getitem__(self, name, dict_getitem=dict.__getitem__, str=str):
        return dict_getitem(self, str(name))

    __getattr__ = __getitem__


def visit_op(op_class, op_name):
    def visit(self, node):
        self.append(op_class(env=self.env, name=op_name, params=self.pop()))
    return visit


class Builder(ast.NodeVisitor):

    def __init__(self, env):
        self.env = env
        self.stack = []

    def build(self, node):
        assert self.stack == []
        self.push()
        self.visit(node)
        assert len(self.stack) == 1 == len(self.stack[0])
        return self.pop().pop()

    def top(self):
        return self.stack[-1]

    def toptop(self):
        return self.stack[-1][-1]

    def append(self, item):
        self.top().append(item)

    def push(self):
        self.stack.append([])

    def pop(self):
        return self.stack.pop()

    def visit_Name(self, node):
        if is_wildcard_name(node.id):
            self.append(WILDCARD)
        elif is_variable_name(node.id):
            self.append(self.env(node.id))
        else:
            self.append(Atom(env=self.env, name=node.id))

    def visit_Str(self, node):
        self.append(String(env=self.env, name=node.s))

    def visit_Bytes(self, node):
        self.append(Bytes(env=self.env, name=node.s))

    def visit_Num(self, node):
        self.append(Num(env=self.env, name=node.n))

    def visit_Tuple(self, node):
        raise ValueError

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
        raise ValueError

    def visit_Dict(self, node):
        raise ValueError

    def visit_AstWrapper(self, node):
        raise ValueError

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.toptop().actions.extend(node.slice)

    def visit_Call(self, node):
        if node.keywords or node.starargs or node.kwargs:
            raise ValueError
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


def make_list(env, items, tail=NIL):

    def cons(*params):
        return List(env=env, params=params)

    return foldr(cons, items, tail)


def unify(left, right, trail):
    left.deref.unify(right.deref, trail)


def build(node):
    return Builder(Environment()).build(node)


is_atomic = rpartial(isinstance, (Atom, String, Num))
is_assertable = rpartial(isinstance,
    (Atom, Relation, Implication, InfixOperator, PrefixOperator, Nil, List))


expand_term = mapply(mcompose(rearrange, dcg_expand, build))
build_term = mapply(mcompose(rearrange, build))
