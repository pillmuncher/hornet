# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from hornet import Database, arithmetic_not_equal, let, select
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
    noattack,
    queens,
    solution,
)

QUEENS = 6


def main():
    db = Database()

    db.tell(
        queens(S) << let(Ns, [i + 1 for i in range(QUEENS)]) & solution(Ns, Ns, [], S),
        solution([X | Xs], Y0s, Qs, [X / Y | S]) << select(Y, Y0s, Ys)
        & noattack(X / Y, Qs)
        & solution(Xs, Ys, [X / Y | Qs], S),
        solution([], _, _, []),
        noattack(X / Y, [X1 / Y1 | Rest]) << arithmetic_not_equal(Y, Y1)
        & arithmetic_not_equal(Y1 - Y, X1 - X)
        & arithmetic_not_equal(Y1 - Y, X - X1)
        & noattack(X / Y, Rest),
        noattack(_, []),
    )

    for subst in db.ask(queens(S)):
        print(subst[S])


if __name__ == "__main__":
    main()
