# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

from hornet import arithmetic_equal  # type: ignore
from hornet import equal  # type: ignore
from hornet import findall  # type: ignore
from hornet import greater  # type: ignore
from hornet import join  # type: ignore
from hornet import let  # type: ignore
from hornet import writeln  # type: ignore
from hornet import Database
from hornet.symbols import N1  # type: ignore
from hornet.symbols import D  # type: ignore
from hornet.symbols import Max  # type: ignore
from hornet.symbols import N  # type: ignore
from hornet.symbols import R  # type: ignore
from hornet.symbols import S  # type: ignore
from hornet.symbols import W  # type: ignore
from hornet.symbols import Ws  # type: ignore
from hornet.symbols import divisible  # type: ignore
from hornet.symbols import fizzbuzz  # type: ignore
from hornet.symbols import show  # type: ignore
from hornet.symbols import word  # type: ignore


def main():
    db = Database()

    db.tell(
        fizzbuzz(N, Max) << ~greater(N, Max)
        & findall(W, word(W, N), Ws)
        & show(N, Ws)
        & let(N1, N + 1)
        & fizzbuzz(N1, Max),
        word("fizz", N) << divisible(N, 3),
        word("buzz", N) << divisible(N, 5),
        word("blub", N) << divisible(N, 7),
        divisible(N, D) << arithmetic_equal(0, N % D),
        show(N, Ws) << equal(Ws, []) >> writeln(N) | join(Ws, S) & writeln(S),
    )

    try:
        for subst in db.ask(fizzbuzz(1, 1111)):
            print(subst[R])
    except RuntimeError:
        print("oops!")


if __name__ == "__main__":
    main()
