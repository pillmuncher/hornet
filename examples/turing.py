# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

from hornet import Database, append, cut, once, reverse  # type: ignore
from hornet.symbols import Q0  # type: ignore
from hornet.symbols import Q1  # type: ignore
from hornet.symbols import Action  # type: ignore
from hornet.symbols import L  # type: ignore
from hornet.symbols import Ls  # type: ignore
from hornet.symbols import Ls0  # type: ignore
from hornet.symbols import Ls1  # type: ignore
from hornet.symbols import NewSym  # type: ignore
from hornet.symbols import Rs  # type: ignore
from hornet.symbols import Rs0  # type: ignore
from hornet.symbols import Rs1  # type: ignore
from hornet.symbols import RsRest  # type: ignore
from hornet.symbols import Sym  # type: ignore
from hornet.symbols import Tape  # type: ignore
from hornet.symbols import Tape0  # type: ignore
from hornet.symbols import Ts  # type: ignore
from hornet.symbols import action  # type: ignore
from hornet.symbols import b  # type: ignore
from hornet.symbols import left  # type: ignore
from hornet.symbols import perform  # type: ignore
from hornet.symbols import q0  # type: ignore
from hornet.symbols import qf  # type: ignore
from hornet.symbols import right  # type: ignore
from hornet.symbols import rule  # type: ignore
from hornet.symbols import stay  # type: ignore
from hornet.symbols import symbol  # type: ignore
from hornet.symbols import turing  # type: ignore


def main():
    db = Database()

    db.tell(
        turing(Tape0, Tape) << perform(q0, [], Ls, Tape0, Rs)
        & reverse(Ls, Ls1)
        & append(Ls1, Rs, Tape),
        perform(qf, Ls, Ls, Rs, Rs) << cut,
        perform(Q0, Ls0, Ls, Rs0, Rs) << symbol(Rs0, Sym, RsRest)
        & once(rule(Q0, Sym, Q1, NewSym, Action))
        & action(Action, Ls0, Ls1, [NewSym | RsRest], Rs1)
        & perform(Q1, Ls1, Ls, Rs1, Rs),
        symbol([], b, []),
        symbol([Sym | Rs], Sym, Rs),
        action(left, Ls0, Ls, Rs0, Rs) << left(Ls0, Ls, Rs0, Rs),
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
