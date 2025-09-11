# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from hornet import database
from hornet.symbols import (
    C1,
    A,
    B,
    C,
    D,
    U,
    V,
    W,
    X,
    Y,
    Z,
    cos,
    cut,
    d,
    equal,
    exp,
    is_atomic,
    is_numeric,
    let,
    log,
    simp,
    sin,
    x,
)
from hornet.terms import Add, Atom, Integer, Mult, Pow


def diff_rules(db):
    db.tell(
        d(X, X, 1).when(
            cut,
        ),
        d(C, X, 0).when(
            is_atomic(C),
            cut,
        ),
        d(U + V, X, A + B).when(
            d(U, X, A),
            d(V, X, B),
            cut,
        ),
        d(U - V, X, A - B).when(
            d(U, X, A),
            d(V, X, B),
            cut,
        ),
        d(C * U, X, C * A).when(
            is_atomic(C),
            ~equal(C, X),
            d(U, X, A),
            cut,
        ),
        d(U * V, X, B * U + A * V).when(
            d(U, X, A),
            d(V, X, B),
            cut,
        ),
        d(U / V, X, (A * V - B * U) / (V * V)).when(
            d(U, X, A),
            d(V, X, B),
            cut,
        ),
        d(U**C, X, C * A * U ** (C - 1)).when(
            is_atomic(C),
            ~equal(C, X),
            d(U, X, A),
            cut,
        ),
        d(U**-C, X, -C * A * U ** (-C - 1)).when(
            d(U, X, A),
            cut,
        ),
        d(U**C, X, C * A * U ** (C - 1)).when(
            equal(C, -C1),
            is_atomic(C1),
            ~equal(C1, X),
            d(U, X, A),
            cut,
        ),
        d(sin(W), X, Z * cos(W)).when(
            d(W, X, Z),
            cut,
        ),
        d(exp(W), X, Z * exp(W)).when(
            d(W, X, Z),
            cut,
        ),
        d(log(W), X, Z / W).when(
            d(W, X, Z),
            cut,
        ),
        d(cos(W), X, -(Z * sin(W))).when(
            d(W, X, Z),
            cut,
        ),
    )


def simp_rules(db):
    db.tell(
        simp(X, X).when(
            is_atomic(X),
            cut,
        ),
        simp(--X, Y).when(
            simp(X, Y),
            cut,
        ),
        simp(-A + -B, C).when(
            simp(A + B, C1),
            simp(-C1, C),
            cut,
        ),
        simp(-A + B, C).when(
            simp(B - A, C),
            cut,
        ),
        simp(A + -B, C).when(
            simp(A - B, C),
            cut,
        ),
        simp(-A - -B, C).when(
            simp(B - A, C),
            cut,
        ),
        simp(-A - B, C).when(
            simp(-A + -B, C),
            cut,
        ),
        simp(A - -B, C).when(
            simp(A + B, C),
            cut,
        ),
        simp(-A * -B, C).when(
            simp(A * B, C),
            cut,
        ),
        simp(-A * B, C).when(
            simp(A * B, C1),
            simp(-C1, C),
            cut,
        ),
        simp(A * -B, -C).when(
            simp(A * B, C1),
            simp(-C1, C),
            cut,
        ),
        simp(X + 0, Y).when(
            simp(X, Y),
            cut,
        ),
        simp(0 + X, Y).when(
            simp(X, Y),
            cut,
        ),
        simp(X - 0, Y).when(
            simp(X, Y),
            cut,
        ),
        simp(0 - X, -Y).when(
            simp(X, Y),
            cut,
        ),
        simp(A + B, C).when(
            is_numeric(A),
            is_numeric(B),
            let(C, A + B),
            cut,
        ),
        simp(A - A, 0).when(
            cut,
        ),
        simp(A - B, C).when(
            is_numeric(A),
            is_numeric(B),
            let(C, A - B),
            cut,
        ),
        simp(X * 0, 0).when(
            cut,
        ),
        simp(0 * X, 0).when(
            cut,
        ),
        simp(0 / X, 0).when(
            cut,
        ),
        simp(X * 1, X).when(
            cut,
        ),
        simp(1 * X, X).when(
            cut,
        ),
        simp(X / 1, X).when(
            cut,
        ),
        simp(X / X, 1).when(
            cut,
        ),
        simp(X**1, X).when(
            cut,
        ),
        simp(X**0, 1).when(
            cut,
        ),
        simp(A + A + B, Y).when(
            simp(2 * A + B, Y),
            cut,
        ),
        simp(A + B + A, 2 * A + B).when(
            simp(2 * A + B, Y),
            cut,
        ),
        simp(B + A + A, 2 * A + B).when(
            simp(2 * A + B, Y),
            cut,
        ),
        simp(A + (B + C), D).when(
            simp(A + B + C, D),
            cut,
        ),
        simp(A * (B * C), D).when(
            simp(A * B * C, D),
            cut,
        ),
        simp(X * X, X**2).when(
            cut,
        ),
        simp(X * X**A, Y).when(
            simp(X ** (A + 1), Y),
            cut,
        ),
        simp(X**A * X, Y).when(
            simp(X ** (A + 1), Y),
            cut,
        ),
        simp(A * B + A * C, Y).when(
            simp(A * (B + C), Y),
            cut,
        ),
        simp(A * B + C * A, Y).when(
            simp(A * (B + C), Y),
            cut,
        ),
        simp(A * B + B * C, Y).when(
            simp(B * (A + C), Y),
            cut,
        ),
        simp(A * B + C * B, Y).when(
            simp(B * (A + C), Y),
            cut,
        ),
        simp(A * (A + B), A**2 + A * Y).when(
            simp(B, Y),
            cut,
        ),
        simp(A * (B + A), A**2 + A * Y).when(
            simp(B, Y),
            cut,
        ),
        simp(A * B, X).when(
            is_numeric(A),
            is_numeric(B),
            let(X, A * B),
            cut,
        ),
        simp(A * X + B * X, Z).when(
            ~equal(A, X),
            ~equal(B, X),
            simp((A + B) * X, Z),
            cut,
        ),
        simp((A + B) * (A - B), X**2 - Y**2).when(
            simp(A, X),
            simp(B, Y),
            cut,
        ),
        simp(X**A / X**B, X**C).when(
            is_numeric(A),
            is_numeric(B),
            let(C, A - B),
            cut,
        ),
        simp(A / B, X).when(
            is_numeric(A),
            is_numeric(B),
            let(X, A / B),
            cut,
        ),
        simp(A**B, X).when(
            is_numeric(A),
            is_numeric(B),
            let(X, A**B),
            cut,
        ),
        simp(A + B, C).when(
            simp(A, X),
            simp(B, Y),
            ~equal([A, B], [X, Y]),
            simp(X + Y, C),
            cut,
        ),
        simp(A - B, C).when(
            simp(A, X),
            simp(B, Y),
            ~equal([A, B], [X, Y]),
            simp(X - Y, C),
            cut,
        ),
        simp(A * B, C).when(
            simp(A, X),
            simp(B, Y),
            ~equal([A, B], [X, Y]),
            simp(X * Y, C),
            cut,
        ),
        simp(A / B, C).when(
            simp(A, X),
            simp(B, Y),
            ~equal([A, B], [X, Y]),
            simp(X / Y, C),
            cut,
        ),
        simp(X**A, C).when(
            simp(A, B),
            ~equal(A, B),
            simp(X**B, C),
            cut,
        ),
        simp(X, X).when(
            cut,
        ),
    )


def diff_test(db):
    # formula = x**-3 + 2 * x**2 + 7 * (x + 9)
    # formula = --x
    # formula = 5 * x**2 * 5
    # formula = x**4 * 5
    # formula = (2 + x) ** 3
    # formula = (2 + x) ** 3
    # formula = x * y * (x + 3)
    # print(formula)
    # formula = x + x + x

    # for subst in db.ask(equal(formula, A)):
    #     print(repr(subst.A))
    # for subst in db.ask(simp(formula, A), d(A, x, B), simp(B, C)):
    # for subst in db.ask(d(formula, x, B)):
    # for subst in db.ask(simp(x + 0, A)):
    from hornet.symbols import u, x, y, z

    formulae = [
        x,  # atomic
        --x,  # double negation
        -x + -y,  # -A + -B
        -x + y,  # -A + B
        x + -y,  # A + -B
        -x - -y,  # -A - -B
        -x - y,  # -A - B
        x - -y,  # A - -B
        -x * -y,  # -A * -B
        -x * y,  # -A * B
        x * -y,  # A * -B
        x + 0,  # X + 0
        0 + x,  # 0 + X
        x - 0,  # X - 0
        0 - x,  # 0 - X
        2 + 3,  # numeric addition
        5 - 5,  # A - A
        7 - 2,  # numeric subtraction
        x * 0,  # X * 0
        0 * x,  # 0 * X
        0 / x,  # 0 / X
        x * 1,  # X * 1
        1 * x,  # 1 * X
        x / 1,  # X / 1
        x / x,  # X / X
        x**1,  # X**1
        x**0,  # X**0
        x + x + y,  # A + A + B
        x + y + x,  # A + B + A
        y + x + x,  # B + A + A
        # x + (y + z),  # A + (B + C)
        # x * (y * z),  # A * (B * C)
        x * x,  # X * X
        x * x**2,  # X * X**A
        x**2 * x,  # X**A * X
        x * y + x * z,  # A * B + A * C
        x * y + z * x,  # A * B + C * A
        x * y + y * z,  # A * B + B * C
        x * y + z * y,  # A * B + C * B
        x * (x + y),  # A * (A + B)
        x * (y + x),  # A * (B + A)
        2 * 3,  # numeric multiplication
        x * u + y * u,  # A * X + B * X
        (x + y) * (x - y),  # (A + B) * (A - B)
        5**3 / 2**1,  # X**A / X**B numeric
        7 / 2,  # A / B numeric
        2**3,  # A**B numeric
        x + y,  # recursive sum simplification
        x - y,  # recursive difference simplification
        x * y,  # recursive product simplification
        x / y,  # recursive division simplification
        x**2,  # recursive power simplification
        x,  # identity simplification
    ]

    # for i, formula in enumerate(formulae):
    #     print(formula)
    #     print(repr(formula))
    #     for subst in db.ask(simp(formula, A)):
    #         print(i, ":", subst[A])
    #         break
    #     else:
    #         print("fail")
    #     # print(subst[B])
    #     # print(subst[C])
    # # break

    formula = x**-3 + 2 * x**2 + 7 * (x + 9)
    print(formula)
    for subst in db.ask(simp(formula, A), d(A, x, B), simp(B, C)):
        # for subst in db.ask(simp(formula, A)):
        print(subst[A])
        print(subst[B])
        print(subst[C])
        break
    else:
        print("fail")


def expr_eval(expr, globals):
    import ast

    expr_ast = ast.Expression(expr.node)
    ast.fix_missing_locations(expr_ast)
    return eval(compile(expr_ast, "<ast>", "eval"), globals)


def main():
    db = database()
    diff_rules(db)
    simp_rules(db)
    diff_test(db)


if __name__ == "__main__":
    main()

f = x**-3 + 2 * x**2 + 7 * (x + 9)
Add(
    Pow(
        Atom(name="x"),
        Integer(value=-3),
    ),
    Add(
        Mult(
            Integer(value=2),
            Pow(
                Atom(name="x"),
                Integer(value=2),
            ),
        ),
        Mult(
            Integer(value=7),
            Add(
                Atom(name="x"),
                Integer(value=9),
            ),
        ),
    ),
)
