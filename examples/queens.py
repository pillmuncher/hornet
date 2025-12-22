# Copyright (c) 2013-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from hornet import database
from hornet.symbols import (
    X1,
    Y1,
    Ns,
    Qs,
    Rest,
    S,
    X,
    Xs,
    Y,
    Y0s,
    Ys,
    _,
    arithmetic_equal,
    equal,
    noattack,
    queens,
    select,
    solution,
)

QUEENS = 6


def main(db):
    db.tell(
        queens(S).when(
            equal(Ns, [i + 1 for i in range(QUEENS)]),
            solution(Ns, Ns, [], S),
        ),
        solution([X | Xs], Y0s, Qs, [X / Y | S]).when(
            select(Y, Y0s, Ys),
            noattack(X / Y, Qs),
            solution(Xs, Ys, [X / Y | Qs], S),
        ),
        solution([], _, _, []),
        noattack(X / Y, [X1 / Y1 | Rest]).when(
            ~arithmetic_equal(Y, Y1),
            ~arithmetic_equal(Y1 - Y, X1 - X),
            ~arithmetic_equal(Y1 - Y, X - X1),
            noattack(X / Y, Rest),
        ),
        noattack(_, []),
    )

    for subst in db.ask(queens(S)):
        print(subst[S])


if __name__ == "__main__":
    main(database())
