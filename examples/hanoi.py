from turtle import Turtle, clear, goto, ht, listen, mainloop, onkey, penup, write
from typing import SupportsIndex, cast

from hornet import Database, Step, Subst, database, predicate, unit
from hornet.symbols import From, M, N, To, With, _, cut, greater, let, move, play_hanoi, show

"""turtle-example-suite:

         tdemo_minimal_hanoi.py

A minimal 'Towers of Hanoi' animation:
A tower of 6 discs is transferred from the
left to the right peg.

An imho quite elegant and concise
implementation using a tower class, which
is derived from the built-in type list.

Discs are turtles with shape 'square', but
stretched to rectangles by shapesize()
 ---------------------------------------
       To exit press STOP button
 ---------------------------------------

Original work: Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012 Python Software Foundation; All Rights Reserved

Modifications: Copyright (c) 2013-2025 Mick Krippendorf

Original algorithm replaced to demonstrate how to interface Hornet with Python code.
"""


class Disc(Turtle):
    def __init__(self, n):
        Turtle.__init__(self, shape='square', visible=False)
        self.pu()
        self.shapesize(1.5, n * 1.5, 2)
        self.fillcolor(n / 6, 0, 1 - n / 6)
        self.st()


class Tower(list[int]):
    "Hanoi tower, a subclass of built-in type list"

    def __init__(self, x):
        "create an empty tower. x is x-position of peg"
        self.x = x

    def push(self, d):
        d.setx(self.x)
        d.sety(-150 + 34 * len(self))
        self.append(d)

    def pop(self, _: SupportsIndex = -1) -> int:
        d = list.pop(self)
        d.sety(150)
        return d


def hanoi(db):
    db.tell(
        play_hanoi(N, From, To, With).when(
            greater(N, 0),
            move(N, From, To, With),
        ),
        move(1, From, To, _).when(show(From, To), cut),
        move(N, From, To, With).when(
            let(M, N - 1),
            move(M, From, With, To),
            move(1, From, To, _),
            move(M, With, To, From),
        ),
    )

    @db.tell
    @predicate(show(From, To))
    def _show(db: Database, subst: Subst) -> Step:
        to = cast(int, subst[To])
        fro = cast(int, subst[From])
        towers[to].push(towers[fro].pop())
        return unit(db, subst.map)

    for s in db.ask(play_hanoi(6, 0, 1, 2)):
        break


def play():
    onkey(lambda: None, 'space')
    clear()
    hanoi(database())
    write('press STOP button to exit', align='center', font=('Courier', 16, 'bold'))


def main():
    global towers
    ht()
    penup()
    goto(0, -225)
    t1 = Tower(-250)
    t2 = Tower(0)
    t3 = Tower(250)
    towers = t1, t2, t3
    # make tower of 6 discs
    for i in range(6, 0, -1):
        t1.push(Disc(i))
    # prepare spartanic user interface ;-)
    write('press spacebar to start game', align='center', font=('Courier', 16, 'bold'))
    onkey(play, 'space')
    listen()
    return 'EVENTLOOP'


if __name__ == '__main__':
    msg = main()
    print(msg)
    mainloop()
