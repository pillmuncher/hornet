# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>

from hornet import append, database
from hornet.symbols import L1, L2


def main():
    db = database()

    for subst in db.ask(append([1, 2, 3], [4, 5], L1)):
        print(subst[L1])
    print()
    for subst in db.ask(append(L1, L2, [1, 2, 3, 4, 5])):
        print(subst[L1], "+", subst[L2])


if __name__ == "__main__":
    main()
