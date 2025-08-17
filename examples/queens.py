# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

from hornet import arithmetic_not_equal  # type: ignore
from hornet import let  # type: ignore
from hornet import select  # type: ignore
from hornet import Database
from hornet.symbols import X1  # type: ignore
from hornet.symbols import Y1  # type: ignore
from hornet.symbols import Ns  # type: ignore
from hornet.symbols import Qs  # type: ignore
from hornet.symbols import Rest  # type: ignore
from hornet.symbols import S  # type: ignore
from hornet.symbols import X  # type: ignore
from hornet.symbols import Xs  # type: ignore
from hornet.symbols import Y  # type: ignore
from hornet.symbols import Y0s  # type: ignore
from hornet.symbols import Ys  # type: ignore
from hornet.symbols import _  # type: ignore
from hornet.symbols import noattack  # type: ignore
from hornet.symbols import queens  # type: ignore
from hornet.symbols import solution  # type: ignore

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
