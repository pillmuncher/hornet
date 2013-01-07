#!/usr/bin/env python3
"""       turtle-example-suite:

         tdemo_minimal_hanoi.py

A minimal 'Towers of Hanoi' animation:
A tower of 6 discs is transferred from the
left to the right peg.

An imho quite elegant and concise
implementation using a tower class, which
is derived from the built-in type list.

Discs are turtles with shape "square", but
stretched to rectangles by shapesize()
 ---------------------------------------
       To exit press STOP button
 ---------------------------------------
"""
from turtle import *
from resolver import Database

HEIGHT = 6


class Disc(Turtle):

    def __init__(self, n):
        Turtle.__init__(self, shape="square", visible=False)
        self.pu()
        self.shapesize(1.5, n * 1.5, 2)
        self.fillcolor(n / HEIGHT, 0, 1 - n / HEIGHT)
        self.st()


class Tower(list):

    "Hanoi tower, a subclass of built-in type list"

    def __init__(self, x):
        "create an empty tower. x is x-position of peg"
        self.x = x

    def push(self, d):
        d.setx(self.x)
        d.sety(-150 + 34 * len(self))
        self.append(d)

    def pop(self):
        d = list.pop(self)
        d.sety(150)
        return d


def hanoi(db, play_hanoi, move, M, N, From, With, To):

    from system import _, greater, let, cut

    def _move(term, env, db, trail):
        towers[env.To()].push(towers[env.From()].pop())

    db.assertz(

        play_hanoi(N, From, To, With) <<
            greater(N, 0) &
            move(N, From, To, With),

        move(1, From, To, _)[_move] << cut,
        move(N, From, To, With) <<
            let(M, N - 1) &
            move(M, From, With, To) &
            move(1, From, To, _) &
            move(M, With, To, From),
    )
    for subst in db |- play_hanoi(HEIGHT, 0, 1, 2):
        print('Yes.')
        break
    else:
        print('No.')


def play():
    onkey(None, "space")
    clear()
    Database().consult(hanoi)
    write("press STOP button to exit",
          align="center", font=("Courier", 16, "bold"))


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
    for i in range(HEIGHT, 0, -1):
        t1.push(Disc(i))
    # prepare spartanic user interface ;-)
    write("press spacebar to start game",
          align="center", font=("Courier", 16, "bold"))
    onkey(play, "space")
    listen()
    return "EVENTLOOP"


if __name__ == "__main__":
    msg = main()
    print(msg)
    mainloop()
