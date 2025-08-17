# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

import pprint

from hornet import Database, findall  # type: ignore
from hornet.symbols import Id  # type: ignore
from hornet.symbols import S  # type: ignore
from hornet.symbols import Side  # type: ignore
from hornet.symbols import Ss  # type: ignore
from hornet.symbols import W  # type: ignore
from hornet.symbols import left  # type: ignore
from hornet.symbols import point  # type: ignore
from hornet.symbols import right  # type: ignore
from hornet.symbols import section  # type: ignore
from hornet.symbols import sections  # type: ignore
from hornet.symbols import segment  # type: ignore
from hornet.symbols import segments  # type: ignore
from hornet.symbols import side  # type: ignore
from hornet.symbols import wing  # type: ignore


def make_wing(db):
    db.tell(
        wing(Side, wing(side(Side), Ss)) << segments(Side, Ss),
        segments(Side, segments(Ss))
        << findall(segment(Id, S), segment(Side, Id) & sections(Id, S), Ss),
        sections(Id, sections(Ss)) << findall(section(S), section(Id, S), Ss),
        segment(left, 1),
        segment(left, 2),
        segment(right, 3),
        segment(right, 4),
        section(1, [point(1, 2), point(3, 4)]),
        section(1, [point(5, 6), point(7, 8)]),
        section(2, [point(2, 3), point(4, 5)]),
        section(2, [point(6, 7), point(8, 9)]),
        section(3, [point(11, 12), point(13, 14)]),
        section(3, [point(15, 16), point(17, 18)]),
        section(4, [point(12, 13), point(14, 15)]),
        section(4, [point(16, 17), point(18, 19)]),
    )


def ask_wing(db, side):
    for subst in db.ask(wing(side, W)):
        pprint.pprint(subst[W])


db = Database()
make_wing(db)
ask_wing(db, left)
ask_wing(db, right)
