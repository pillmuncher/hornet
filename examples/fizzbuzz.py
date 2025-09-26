# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from toolz import take

from hornet import DCG, database
from hornet.symbols import (
    M,
    N,
    R,
    S,
    Ws,
    _,
    cut,
    equal,
    fb,
    fizzbuzz,
    ifelse,
    inline,
    join,
    let,
    phrase,
    word,
    words,
)

db = database()


def main():
    db.tell(
        DCG(words(N)).when(word(3, N), word(5, N), word(7, N), inline(cut)),
        DCG(word(3, N)).when(inline(let(M, N % 3), equal(M, 0)), ["fizz"]),
        DCG(word(5, N)).when(inline(let(M, N % 5), equal(M, 0)), ["buzz"]),
        DCG(word(7, N)).when(inline(let(M, N % 7), equal(M, 0)), ["quux"]),
        DCG(word(_, _)).when(),
        fb(N, R).when(
            phrase(words(N), Ws),
            join(Ws, S),
            ifelse(
                equal(S, ""),
                equal(N, R),
                equal(S, R),
            ),
        ),
        fb(N, R).when(
            let(M, N + 1),
            fb(M, R),
        ),
        fizzbuzz(R).when(
            fb(1, R),
        ),
    )

    for s in take(111, db.ask(fizzbuzz(R))):
        print(s[R])


if __name__ == "__main__":
    main()
