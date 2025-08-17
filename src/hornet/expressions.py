# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

import ast
import functools
import numbers
from typing import Callable

from astor import code_gen as codegen
from toolz.functoolz import flip, identity

from .util import compose, foldl, qualname, rpartial

__all__ = [
    # monad class:
    "Expression",
    # monadic functions:
    "unit",
    "bind",
    "mlift",
    "mcompose",
    # helper functions:
    "promote",
    "astify",
    # Expression factory functions:
    "Name",
    "Tuple",
    "List",
    "Set",
    "Wrapper",
    # Expression factory operators:
    "Subscript",
    "Call",
    "USub",
    "UAdd",
    "Invert",
    "Add",
    "Sub",
    "Mult",
    "Div",
    "FloorDiv",
    "Mod",
    "Pow",
    "LShift",
    "RShift",
    "BitAnd",
    "BitXor",
    "BitOr",
    # AST node instance test functions:
    "is_binop",
    "is_lshift",
    "is_rshift",
    "is_bitand",
    "is_bitor",
    "is_name",
    "is_str",
    "is_call",
    "is_list",
    "is_set",
    "is_tuple",
    "is_astwrapper",
    "is_operator",
]


class Expression:
    """
    An Expression object wraps around an AST node.
    """

    # See also .test.test_expresion.test_monad_laws()
    __slots__ = "node"

    def __init__(self, node):
        "Initialize an Expression object with an AST node."
        self.node = node

    def __repr__(self):
        return ast.dump(self.node)

    def __str__(self):
        return codegen.to_source(self.node)


# In the Monad, unit is the same as Expression:
unit = Expression


def bind(expr: Expression, mfunc: Callable[[ast.AST], Expression]) -> Expression:
    """
    The function bind(expr, AST --> Expression) --> Expression is the monadic
    bind operator.  It takes an Expression object expr and a monadic function
    mfunc, passes the AST associated with expr to mfunc and returns whatever
    mfunc returns.
    """
    return mfunc(expr.node)


def mlift(func: Callable[..., ast.AST]) -> Callable[..., Expression]:
    """
    The function mlift(... --> AST) --> (... --> unit) "lifts" a normal
    function that returns an AST into a function that returns an Expression.
    It is mostly used as a function decorator.
    """
    return compose(Expression, func)


def mcompose(*mfuncs):
    """
    Make monadic functions AST --> Expression composable.
    """
    return functools.partial(foldl, bind, tuple(reversed(mfuncs)))


# Here come the Expression factory functions.
#
# The arguments they take are converted to AST objects if necessary. They
# return an AST node that gets wrapped in an Expression object by the mlift
# decorator.
# Their names don't conform to PEP-8 because they reflect the AST node types
# they represent.


@mlift
def Name(name, **kwargs):
    return ast.Name(id=name, **kwargs)


@mlift
def Constant(value):
    return ast.Constant(value=value)


@mlift
def Tuple(tuple_):
    return ast.Tuple(elts=[astify(each) for each in tuple_])


@mlift
def List(list_):
    return ast.List(elts=[astify(each) for each in list_])


@mlift
def Set(set_):
    return ast.Set(elts=[astify(each) for each in set_])


# Although the following functions do not represent AST node types, they are
# used in the same way and should follow the same conventions as the ones
# above.


class AstWrapper[T](ast.AST):
    def __init__(self, wrapped: T):
        self.wrapped: T = wrapped


@mlift
def Wrapper(wrapped):
    return AstWrapper(wrapped=wrapped)


# The last set of factory functions are used as operator methods of Expression
# objects.  They are bound to the Expression class below.
#
# When trying to understand what's going on in these functions, some questions
# may arise: Where come the arguments from and, if these are supposed to be
# operator methods in the Expression class, then where the heck is self?
#
# Let's see an example:

# x = Name('x')
# y = x + 3
# z = y + 5

# Here x is an Expression object created by Name('x'). It wraps around an AST
# node ast.Name(id='x', ctx='ast.Load())
#
# x + 3 triggers Expression.__add__ to be called with arguments x and 3.
# Expression.__add__ is bound to the Add factory function which has two
# parameters left and right.  So, x gets passed as left and 3 gets passed as
# right.  Add now calls astify on each argument. For left this just extracts
# the already existing AST node, but for right (which is 3), astify first calls
# the factory function Num, which in turn creates an Expression wrapped around
# an AST node ast.Num(n=3) and then unwraps it again and returns just the AST.
# Then Add attaches both AST nodes as children to an ast.BinOp node which it
# returns.  Since Add was decorated with the mlift function, the result gets
# wrapped in an Expression node, which is returned.  The return value then gets
# bound to y.  In the next line, y + 5 triggers Expression.__add__ again and
# the same thing as before happens, but with arguments y and 5.
#
# But what if we change the last line to:

# z = 5 + y

# 5 (an int) doesn't know how to add an Expression object to itself, so it
# returns NotImplemented which causes Python to call the right argument's
# reversed add method Expression.__radd__.  All reversed operator methods are
# called with swapped operands, like so: Expression.__radd__(right, left). But
# since we used the flip decorator when we bound Add to Expression.__radd__,
# the order in which the arguments are passed are reversed again and we're back
# at Expression.__radd__(left, right).  left is bound to 5 and right to y, as
# we would expect when we saw 5 + y. When we construct our AST node, it comes
# out correctly:

# ast.BinOp(
#         left=ast.Num(n=5),
#         op=ast.Add(),
#         right=ast.Name(id='y')
#     )

# For more complex cases like e.g.:

# x - y * z + 1

# we rely on the priority and associativity rules that Python imposes on us.
# Then this expression is the same as ((x - (y * z)) + 1).


@mlift
@qualname("Expression.__getitem__")
def Subscript(target, subscript):
    return ast.Subscript(
        value=astify(target),
        slice=ast.Slice(lower=astify(subscript)),
    )


@mlift
@qualname("Expression.__call__")
def Call(target, *args):
    return ast.Call(
        func=astify(target),
        args=[astify(each) for each in args],
        keywords=[],
    )


def _unary_op(op, name):
    @mlift
    @qualname(name)
    def op_method(right):
        return ast.UnaryOp(op(), astify(right))

    return op_method


USub = _unary_op(ast.USub, "Expression.__neg__")
UAdd = _unary_op(ast.UAdd, "Expression.__pos__")
Invert = _unary_op(ast.Invert, "Expression.__invert__")


def _binary_op(op, name):
    @mlift
    @qualname(name)
    def op_method(left, right):
        return ast.BinOp(astify(left), op(), astify(right))

    return op_method


Add = _binary_op(ast.Add, "Expression.__add__")
Sub = _binary_op(ast.Sub, "Expression.__sub__")
Mult = _binary_op(ast.Mult, "Expression.__mul__")
Div = _binary_op(ast.Div, "Expression.__truediv__")
FloorDiv = _binary_op(ast.FloorDiv, "Expression.__floordiv__")
Mod = _binary_op(ast.Mod, "Expression.__mod__")
Pow = _binary_op(ast.Pow, "Expression.__pow__")
LShift = _binary_op(ast.LShift, "Expression.__lshift__")
RShift = _binary_op(ast.RShift, "Expression.__rshift__")
BitAnd = _binary_op(ast.BitAnd, "Expression.__and__")
BitXor = _binary_op(ast.BitXor, "Expression.__xor__")
BitOr = _binary_op(ast.BitOr, "Expression.__or__")


# Here the Expression factory operator functions get finally bound to the
# Expression class:

Expression.__getitem__ = Subscript  # type: ignore
Expression.__call__ = Call  # type: ignore
Expression.__neg__ = USub  # type: ignore
Expression.__pos__ = UAdd  # type: ignore
Expression.__invert__ = Invert  # type: ignore
Expression.__add__ = Add  # type: ignore
Expression.__radd__ = flip(Add)  # type: ignore
Expression.__sub__ = Sub  # type: ignore
Expression.__rsub__ = flip(Sub)  # type: ignore
Expression.__mul__ = Mult  # type: ignore
Expression.__rmul__ = flip(Mult)  # type: ignore
Expression.__truediv__ = Div  # type: ignore
Expression.__rtruediv__ = flip(Div)  # type: ignore
Expression.__floordiv__ = FloorDiv  # type: ignore
Expression.__rfloordiv__ = flip(FloorDiv)  # type: ignore
Expression.__mod__ = Mod  # type: ignore
Expression.__rmod__ = flip(Mod)  # type: ignore
Expression.__pow__ = Pow  # type: ignore
Expression.__rpow__ = flip(Pow)  # type: ignore
Expression.__lshift__ = LShift  # type: ignore
Expression.__rlshift__ = flip(LShift)  # type: ignore
Expression.__rshift__ = RShift  # type: ignore
Expression.__rrshift__ = flip(RShift)  # type: ignore
Expression.__and__ = BitAnd  # type: ignore
Expression.__rand__ = flip(BitAnd)  # type: ignore
Expression.__xor__ = BitXor  # type: ignore
Expression.__rxor__ = flip(BitXor)  # type: ignore
Expression.__or__ = BitOr  # type: ignore
Expression.__ror__ = flip(BitOr)  # type: ignore


# Any Python object 'obj' will be turned into an Expression object with its
# AST created if necessary:
@functools.singledispatch
def promote(obj) -> Expression:
    return Wrapper(obj)


promote.register(Expression)(identity)
promote.register(numbers.Number)(Constant)
promote.register(str)(Constant)
promote.register(tuple)(Tuple)
promote.register(list)(List)
promote.register(set)(Set)


# Given any Python object 'obj', return its AST (and create it if necessary):
def astify(obj):
    return promote(obj).node


def is_binop(node, op):
    return isinstance(node, ast.BinOp) and isinstance(node.op, op)


is_lshift = rpartial(is_binop, ast.LShift)
is_rshift = rpartial(is_binop, ast.RShift)
is_bitand = rpartial(is_binop, ast.BitAnd)
is_bitor = rpartial(is_binop, ast.BitOr)

is_name = rpartial(isinstance, ast.Name)
is_str = rpartial(isinstance, ast.Constant)
is_call = rpartial(isinstance, ast.Call)
is_list = rpartial(isinstance, ast.List)
is_set = rpartial(isinstance, ast.Set)
is_tuple = rpartial(isinstance, ast.Tuple)
is_astwrapper = rpartial(isinstance, AstWrapper)
is_operator = rpartial(isinstance, (ast.BinOp, ast.UnaryOp))
is_terminal = rpartial(isinstance, (ast.Name, ast.Constant))
