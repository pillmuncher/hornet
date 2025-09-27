# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from hornet import database
from hornet.symbols import (
    Q0,
    Q1,
    Action,
    L,
    Ls,
    Ls0,
    Ls1,
    NewSym,
    Rs,
    Rs0,
    Rs1,
    RsRest,
    Sym,
    Tape,
    Tape0,
    Ts,
    action,
    append,
    b,
    cut,
    left,
    once,
    perform,
    q0,
    qf,
    reverse,
    right,
    rule,
    stay,
    symbol,
    turing,
)


def main():
    db = database()

    db.tell(
        turing(Tape0, Tape).when(
            perform(q0, [], Ls, Tape0, Rs),
            reverse(Ls, Ls1),
            append(Ls1, Rs, Tape),
        ),
        perform(qf, Ls, Ls, Rs, Rs).when(cut),
        perform(Q0, Ls0, Ls, Rs0, Rs).when(
            symbol(Rs0, Sym, RsRest),
            once(rule(Q0, Sym, Q1, NewSym, Action)),
            action(Action, Ls0, Ls1, [NewSym | RsRest], Rs1),
            perform(Q1, Ls1, Ls, Rs1, Rs),
        ),
        symbol([], b, []),
        symbol([Sym | Rs], Sym, Rs),
        action(left, Ls0, Ls, Rs0, Rs).when(left(Ls0, Ls, Rs0, Rs)),
        action(stay, Ls, Ls, Rs, Rs),
        action(right, Ls0, [Sym | Ls0], [Sym | Rs], Rs),
        left([], [], Rs0, [b | Rs0]),
        left([L | Ls], Ls, Rs, [L | Rs]),
    )

    db.tell(
        rule(q0, 1, q0, 1, right),
        rule(q0, b, qf, 1, stay),
    )

    for subst in db.ask(turing([1, 1, 1], Ts)):
        print(subst[Ts])


if __name__ == "__main__":
    main()
