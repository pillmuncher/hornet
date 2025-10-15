# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from toolz import take

from hornet import DCGs, database
from hornet.symbols import (
    M,
    N,
    R,
    S,
    V,
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


def main(db):
    db.tell(
        fizzbuzz(R).when(
            fb(1, R),
        ),
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
        *DCGs(
            words(N).when(
                word(3, N),
                word(5, N),
                word(7, N),
                inline(cut),
            ),
            word(3, N).when(inline(let(M, N % 3), equal(M, 0)), ["fizz"]),
            word(5, N).when(inline(let(M, N % 5), equal(M, 0)), ["buzz"]),
            word(7, N).when(inline(let(M, N % 7), equal(M, 0)), ["quux"]),
            word(_, _),
        ),
    )

    for s in take(1111, db.ask(fizzbuzz(V))):
        # print(s[V])
        pass


if __name__ == "__main__":
    from examples import timer

    with timer():
        main(database())
