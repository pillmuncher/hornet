# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from hornet import database
from hornet.symbols import L1, L2, append


def main():
    db = database()

    for subst in db.ask(append([1, 2, 3], [4, 5], L1)):
        print(subst[L1])
    print()
    for subst in db.ask(append(L1, L2, [1, 2, 3, 4, 5])):
        print(subst[L1], "+", subst[L2])


if __name__ == "__main__":
    main()
