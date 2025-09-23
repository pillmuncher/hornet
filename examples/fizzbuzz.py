# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from toolz import take

from hornet import database
from hornet.symbols import (
    Current,
    M,
    N,
    Next,
    R,
    Result,
    S,
    W,
    Ws,
    equal,
    fb,
    findall,
    fizzbuzz,
    ifelse,
    join,
    let,
    word,
)

db = database()


def main():
    db.tell(
        word("fizz", N).when(
            let(M, N % 3),
            equal(M, 0),
        ),
        word("buzz", N).when(
            let(M, N % 5),
            equal(M, 0),
        ),
        word("blub", N).when(
            let(M, N % 7),
            equal(M, 0),
        ),
        fb(N, Result).when(
            findall(W, word(W, N), Ws),
            join(Ws, S),
            ifelse(
                equal(S, ""),
                equal(N, Result),
                equal(S, Result),
            ),
        ),
        fb(Current, Result).when(
            let(Next, Current + 1),
            fb(Next, Result),
        ),
        fizzbuzz(Result).when(
            fb(1, Result),
        ),
    )

    try:
        for s in take(1111, db.ask(fizzbuzz(R))):
            print(s[R])
            pass
    except RuntimeError:
        print("oops!")


if __name__ == "__main__":
    # from examples.utils import timer
    #
    # with timer():
    main()
