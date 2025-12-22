# Copyright (c) 2013-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from hornet import database
from hornet.symbols import L1, L2, L, append


def main(db):
    for subst in db.ask(append([1, 2, 3], [4, 5], L)):
        print(subst[L])
    print()
    for i, subst in enumerate(db.ask(append(L1, L2, [1, 2, 3, 4, 5]))):
        print(f"{i}:", subst[L1], "+", subst[L2])


if __name__ == "__main__":
    main(database())
