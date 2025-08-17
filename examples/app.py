#!/usr/bin/env python3
# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>


from hornet import Database, append
from hornet.symbols import L1, L2


def main():
    db = Database()

    for subst in db.ask(append(L1, L2, [1, 2, 3, 4, 5])):
        print(subst[L1], "+", subst[L2])

    for subst in db.ask(append([1, 2], L2, [1, 2, 3])):
        print(subst[L2])


if __name__ == "__main__":
    main()
