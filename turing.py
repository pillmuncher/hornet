from resolver import Database, UnificationFailed
from system import *


def tm(db,
    Action, L, Ls, Ls0, Ls1, NewSym, Q0, Q1, Rs, Rs0, Rs1, RsRest, Sym, Tape,
    Tape0, action, b, left, perform, q0, qf, right, rule, stay, symbol, turing):

    db.assertz(

        turing(Tape0, Tape) <<
            perform(q0, [], Ls, Tape0, Rs) &
            reverse(Ls, Ls1) &
            append(Ls1, Rs, Tape),

        perform(qf, Ls, Ls, Rs, Rs) << cut,
        perform(Q0, Ls0, Ls, Rs0, Rs) <<
            symbol(Rs0, Sym, RsRest) &
            once(rule(Q0, Sym, Q1, NewSym, Action)) &
            action(Action, Ls0, Ls1, [NewSym|RsRest], Rs1) &
            perform(Q1, Ls1, Ls, Rs1, Rs),

        symbol([], b, []),
        symbol([Sym|Rs], Sym, Rs),

        action(left, Ls0, Ls, Rs0, Rs) << left(Ls0, Ls, Rs0, Rs),
        action(stay, Ls, Ls, Rs, Rs),
        action(right, Ls0, [Sym|Ls0], [Sym|Rs], Rs),

        left([], [], Rs0, [b|Rs0]),
        left([L|Ls], Ls, Rs, [L|Rs]),

    )


def tm_test(db, turing, Ts, b, q0, qf, right, rule, stay):

    db.assertz(
        rule(q0, 1, q0, 1, right),
        rule(q0, b, qf, 1, stay),
    )
    for subst in db.query(turing([1,1,1], Ts)):
        print(subst[Ts])


db = Database()
db.consult(tm)
db.consult(tm_test)
