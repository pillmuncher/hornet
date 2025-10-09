# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from hornet import database
from hornet.symbols import (
    A1,
    B1,
    C0,
    C1,
    A,
    B,
    C,
    D,
    E,
    U,
    V,
    W,
    X,
    Y,
    Z,
    _,
    cos,
    cut,
    d,
    diff,
    equal,
    exp,
    ifelse,
    is_atomic,
    is_numeric,
    let,
    log,
    s,
    simp,
    sin,
    throw,
    x,
)


def diff_rules(db):
    db.tell(
        diff(X, Y, Z).when(d(X, Y, Z)),
        d(X, X, 1).when(
            cut,
        ),
        d(C, X, 0).when(
            is_atomic(C),
            cut,
        ),
        s(X + 0, Y).when(
            cut,
            s(X, Y),
        ),
        s(0 + X, Y).when(
            cut,
            s(X, Y),
        ),
        s(X - 0, Y).when(
            cut,
            s(X, Y),
        ),
        s(0 - X, -Y).when(
            cut,
            s(X, Y),
        ),
        d(U + V, X, A + B).when(
            cut,
            d(U, X, A),
            d(V, X, B),
        ),
        d(U - V, X, A - B).when(
            cut,
            d(U, X, A),
            d(V, X, B),
        ),
        d(0 * U, X, 0).when(
            cut,
        ),
        d(U * 0, X, 0).when(
            cut,
        ),
        d(1 * U, X, V).when(
            cut,
            d(U, X, V),
        ),
        d(U * 1, X, V).when(
            cut,
            d(U, X, V),
        ),
        d(C * U, X, C * A).when(is_atomic(C), ~equal(C, X), cut, d(U, X, A)),
        d(U * V, X, B * U + A * V).when(
            cut,
            d(U, X, A),
            d(V, X, B),
        ),
        d(0 / U, X, 0).when(
            cut,
        ),
        d(U / V, X, (A * V - B * U) / (V * V)).when(
            cut,
            d(U, X, A),
            d(V, X, B),
        ),
        d(U**C, X, C * A * U ** (C - 1)).when(
            is_atomic(C),
            ~equal(C, X),
            cut,
            d(U, X, A),
        ),
        d(U**-C, X, -C * A * U ** (-C - 1)).when(
            cut,
            d(U, X, A),
        ),
        d(U**C, X, C * A * U ** (C - 1)).when(
            equal(C, -C1),
            is_atomic(C1),
            ~equal(C1, X),
            cut,
            d(U, X, A),
        ),
        d(sin(W), X, Z * cos(W)).when(
            cut,
            d(W, X, Z),
        ),
        d(exp(W), X, Z * exp(W)).when(
            cut,
            d(W, X, Z),
        ),
        d(log(W), X, Z / W).when(
            cut,
            d(W, X, Z),
        ),
        d(cos(W), X, -(Z * sin(W))).when(
            cut,
            d(W, X, Z),
        ),
    )


def simp_rules(db):
    db.tell(
        simp(X, Y).when(s(X, Y)),
        s(A, A).when(
            is_atomic(A),
            cut,
        ),
        # Addition
        s(0 + A, B).when(
            cut,
            s(A, B),
        ),
        s(A + 0, B).when(
            cut,
            s(A, B),
        ),
        s(A + B, C).when(
            is_numeric(A),
            is_numeric(B),
            cut,
            let(C, A + B),
        ),
        s(A + (B + C), D).when(
            cut,
            s(A + B + C, D),
        ),
        s(-A + -B, C).when(
            cut,
            s(A + B, C0),
            ifelse(
                equal(A + B, C0),
                equal(C0, C),
                s(-C0, C),
            ),
        ),
        s(-A + B, C).when(
            cut,
            s(B - A, C),
        ),
        s(A + -B, C).when(
            cut,
            s(A - B, C),
        ),
        s(A + B, C).when(
            s(A, A1),
            s(B, B1),
            ~equal([A, B], [A1, B1]),
            cut,
            s(A1 + B1, C),
        ),
        # Subtraction
        s(--A, B).when(
            cut,
            s(A, B),
        ),
        s(A - 0, B).when(
            cut,
            s(A, B),
        ),
        s(0 - A, B).when(
            cut,
            s(-A, B),
        ),
        s(A - A, 0).when(
            cut,
        ),
        s(A - B, C).when(
            is_numeric(A),
            is_numeric(B),
            cut,
            let(C, A - B),
        ),
        s(-A, -B).when(
            cut,
            s(A, B),
        ),
        s(-A - -B, C).when(
            cut,
            s(B - A, C),
        ),
        s(-A - B, D).when(
            cut,
            s(A + B, C),
            ifelse(
                equal(A + B, C0),
                equal(C0, D),
                s(-C0, D),
            ),
        ),
        s(A - -B, C).when(
            cut,
            s(A + B, C),
        ),
        s(A - B, C).when(
            s(A, A1),
            ~equal(A, A1),
            s(B, B1),
            ~equal(B, B1),
            cut,
            s(A1 - B1, C),
        ),
        # Multiplication
        s(0 * _, 0).when(
            cut,
        ),
        s(_ * 0, 0).when(
            cut,
        ),
        s(1 * A, B).when(
            cut,
            s(A, B),
        ),
        s(A * 1, B).when(
            cut,
            s(A, B),
        ),
        s(A * (B * C), D).when(
            cut,
            s(A * B * C, D),
        ),
        s(A * (A + B), A**2 + A * C).when(
            cut,
            s(B, C),
        ),
        s(A * (B + A), A**2 + A * C).when(
            cut,
            s(B, C),
        ),
        s(A * D + B * D, C).when(
            ~equal(A, D),
            ~equal(B, D),
            cut,
            s((A + B) * D, C),
        ),
        s(A * A, C).when(
            cut,
            s(A, B),
            s(B**2, C),
        ),
        s(A * A**B, C).when(
            cut,
            s(A ** (B + 1), C),
        ),
        s(-A * -B, C).when(
            cut,
            s(A * B, C),
        ),
        s(-A * B, C).when(
            cut,
            s(A * B, C0),
            ~equal(C0, A * B),
            s(-C0, C),
        ),
        s(A * -B, C).when(
            cut,
            s(A * B, C0),
            ~equal(C0, A * B),
            s(-C0, C),
        ),
        s(A * B, C).when(
            is_numeric(A),
            is_numeric(B),
            cut,
            let(C, A * B),
        ),
        s(A * B, C).when(
            s(A, D),
            s(B, E),
            ~equal([A, B], [D, E]),
            cut,
            s(D * E, C),
        ),
        s((A + B) * (A - B), C**2 - D**2).when(
            cut,
            s(A, C),
            s(B, D),
        ),
        # Division
        s(A / 0, 0).when(
            throw(ZeroDivisionError(f"Division by zero: {A / 0}")),
        ),
        s(0 / _, 0).when(
            cut,
        ),
        s(A / A, 1).when(
            cut,
        ),
        s(A / 1, B).when(
            cut,
            s(A, B),
        ),
        s(A / B, C).when(
            is_numeric(A),
            is_numeric(B),
            cut,
            let(C, A / B),
        ),
        s(A / B, C).when(
            s(A, A1),
            s(B, B1),
            ~equal([A, B], [A1, B1]),
            cut,
            s(A1 / B1, C),
        ),
        # Exponentiation
        s(_**0, 1).when(
            cut,
        ),
        s(A**1, B).when(
            cut,
            s(A, B),
        ),
        s(A**B * A, C).when(
            cut,
            s(A, A1),
            s(B + 1, B1),
            s(A1**B1, C),
        ),
        s(A**B * A**C, A**D).when(
            is_numeric(B),
            is_numeric(C),
            cut,
            let(D, B + C),
        ),
        s(A**B / A**C, A**D).when(
            is_numeric(B),
            is_numeric(C),
            cut,
            let(D, B - C),
        ),
        s(A**B, C).when(
            is_numeric(A),
            is_numeric(B),
            cut,
            let(C, A**B),
        ),
        s(A**B, C).when(
            s(B, D),
            ~equal(B, D),
            cut,
            s(A**D, C),
        ),
        # Fixpoint
        s(A, A).when(
            cut,
        ),
    )


def diff_test(db):
    formula = x**-3 + 2 * x**2 + 7 * (x + 9)
    for subst in db.ask(simp(formula, A), diff(A, x, B), simp(B, C)):
        print(f"{subst[A] = !s}")
        print(f"{subst[B] = !s}")
        print(f"{subst[C] = !s}")


def main(db):
    diff_rules(db)
    simp_rules(db)
    diff_test(db)


if __name__ == "__main__":
    main(database())
