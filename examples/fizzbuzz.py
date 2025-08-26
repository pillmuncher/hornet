# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from hornet import (
    Database,
    arithmetic_equal,
    equal,
    findall,
    greater,
    join,
    let,
    writeln,
)
from hornet.symbols import N1, D, Max, N, R, S, W, Ws, divisible, fizzbuzz, show, word


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
