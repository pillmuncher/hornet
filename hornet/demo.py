from .expressions import *

a, b, c, d, e, f, g, h = map(Name, 'abcdefgh')

expr = a + b * c - f(d, e) / g(h(a, b, c), d, e)
print('Ein Ausdruck:')
print(expr)
print()
print('Ein AST:')
print(repr(expr))
