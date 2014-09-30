#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from hornet import *
from hornet.expressions import promote

from hornet.symbols import (
    A, B, C, D, Seen, Tribe, U, V, W, Who, X, Y, Z, ancestor, appenddl,
    aristotle, bob, dan, descendant, directly_related, patriarch, hal, jim,
    joe, lee, man, mortal, plato, related, related_, sam, socrates, son, test,
    tom, tribe, nonequal, lwriteln, a, b, c, d, e, blub,
)


def show_db(db):
    for each in db.ask(listing):
        break


def xor_test(db):
    for each in fail ^ true, true ^ fail, fail ^ fail, true ^ true:
        for subst in db.ask(equal(each, X) & call(X)):
           print(subst[X])
    print()


def eqtest(db):
    for subst in db.ask(equal(tom, X)):
        print(subst[X])
        for a, b in subst.items():
            print(type(a), ':', type(b))
    print()


def barbara(db):
    db.tell(
        man(socrates),
        man(plato),
        man(aristotle),
        mortal(X) <<
            man(X),
    )
    for subst in db.ask(mortal(Who)):
        print(subst[Who])
    print()


def varunify(db):
    for subst in db.ask(equal(X, Z) & equal(Y, Z)):
        for k, v in sorted(subst.items()):
            print(k, '=', v, '=', v())
    print()


def subtraction(db):
    q = equal(A, 5) & equal(B, 2) & equal(C, 1) & let(D, A - B - C)
    for subst in db.ask(q):
        print(subst[A], '-', subst[B], '-', subst[C], '==', subst[D])
    print()


def stdtypes(db):
    for subst in db.ask(equal(10, X) & equal(X, 10)):
        print(sorted(subst.items()))

    for subst in db.ask(equal('hallo', X) & equal(X, 'hallo')):
        print(sorted(subst.items()))

    for subst in db.ask(equal([], X) & equal(X, [])):
        print(sorted(subst.items()))

    for subst in db.ask(equal([1], X) & equal(X, [1])):
        print(sorted(subst.items()))

    for subst in db.ask(equal([1 | promote(2)], X) & equal(X, [promote(1) | 2])):
        print(sorted(subst.items()))

    for subst in db.ask(equal([1, 2], X) & equal(X, [1, 2])):
        print(sorted(subst.items()))

    for subst in db.ask(equal([1, promote(2) | 3], X) & equal(X, [1, 2 | promote(3)])):
        print(sorted(subst.items()))

    for subst in db.ask(equal([1, promote(2), 3], X) & equal(X, [1, 2 | promote(3)])):
        print('Yes.')
        break
    else:
        print('No.')
    print()


def difflist(db):
    db.tell(
        appenddl(A - B, B - C, A - C),
        (A - B + B - C) / (A - C),
    )
    q = appenddl([1, 2 | U] - U, [3, 4 | V] - V, W - [5, 6 | X])
    for subst in db.ask(q):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    for subst in db.ask(q & equal(X, [7, 8, 9])):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    q = ([1, 2 | U] - U + [3, 4 | V] - V) / (W - [5, 6 | X])
    for subst in db.ask(q):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    for subst in db.ask(q & equal(X, [7, 8, 9])):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()


def unify_test(db):

    for subst in db.ask(join(['hallo', 'welt'], 'hallowelt')):
        print('Yes.')
        break
    else:
        print('No.')


def tribes(db):

    db.tell(

        son(joe, sam),  # joe is the son of sam, etc.
        #son(bob, sam),
        son(jim, joe),
        son(tom, bob),
        son(hal, bob),
        son(dan, jim),
        son(lee, jim),

        # X is a descendant of Y:
        descendant(X, Y) <<
            son(X, Y),          # one's son is one's descendant
        descendant(X, Z) <<
            son(Y, Z) &         # a descendant of one's son
            descendant(X, Y),   # is also one's descendant

        # X is an ancestor of Y:
        ancestor(X, Y) <<
            descendant(Y, X),   # one is an ancestor of one's descendant

        related(X, Y) <<
            related(X, Y, [X]),

        related(X, Y, Seen) <<
            directly_related(X, Z) &
            ~member(Z, Seen) &
            related_(Z, Y, Seen),

        related_(X, X, _),
        related_(X, Y, Seen) <<
            related(X, Y, [X | Seen]),

        directly_related(X, Y) << son(X, Y) | son(Y, X),

        # Z is the patriarch of X:
        patriarch(Z, X) <<
            son(X, Y) &
            patriarch(Z, Y) & cut,
        patriarch(Z, Z),

        tribe(X, [Z | Tribe]) <<
            patriarch(Z, X) &
            findall(Y, descendant(Y, Z), Tribe),
            #findall(test(Y, U), descendant(Y, Z), Tribe, U) & equal(U, [patriarch]),
            #findall(test(Y, U, test(U)), descendant(Y, Z), Tribe) &
            #equal(W, bob) & equal(Tribe, [test(_, V, _) | _]) & equal(W, V),
            #findall(test(Y, U), descendant(Y, Z) & equal(Y, U), Tribe),

    )


def genealogy(db):

    tribes(db)

    print('who is an ancestor of who?')
    for subst in db.ask(ancestor(A, B)):
        print(subst[A], 'of', subst[B])
    print()

    print('who are joe\'s descendants?')
    for subst in db.ask(descendant(A, joe)):
        print(subst[A])
    print()

    print('who are dan\'s ancestors?')
    for subst in db.ask(ancestor(A, dan)):
        print(subst[A])
    print()

    print('who is bob related to?')
    for subst in db.ask(related(bob, A)):
        print(subst[A])
    print()

    print('who is related to bob?')
    for subst in db.ask(related(A, bob)):
        print(subst[A])
    print()

    print('who is lee related to?')
    for subst in db.ask(related(lee, A)):
        print(subst[A])
    print()

    print('who is related to lee?')
    for subst in db.ask(related(A, lee)):
        print(subst[A])
    print()

    print('is lee related to joe?')
    for subst in db.ask(related(lee, joe)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('is lee related to bob?')
    for subst in db.ask(related(lee, bob)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('one is not a relative of oneself. true?')
    for subst in db.ask(~related(A, A)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('who belongs to joe\'s tribe?')
    for subst in db.ask(tribe(joe, A) & lwriteln(A)):
        #print(subst[A])
        pass
    print()

    print('what clauses does the predicate descendant/2 consist of?')
    for subst in db.ask(listing(descendant, 2)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('test')
    for subst in db.ask(related(bob, X) & cut & writeln(X) & fail):
        print('Yes.')
        #break
    else:
        print('No.')
    print()


def backwards(db):

    #for subst in db.ask(member(X, [a, b, c])):
        #print(subst[X])

    for subst in db.ask(equal(W, [X, Y, Z]) & member(a, W) & member(b, W)):
    #for subst in db.ask(equal(W, [X, Y, Z]) & member(a, W)):
        print(subst[W])

    #for subst in db.ask(append([a, b], [c, d, e], X)):
        #print(subst[X])

    #for subst in db.ask(append(X, Y, [a, b, c, d, e])):
        #print(subst[X], subst[Y])

    #for subst in db.ask(ignore(true) & ignore(fail)):
        #print('Yes, ignored.')




def univ_test(db):

    for subst in db.ask(var(X)):
        print(subst)
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.ask(equal(a, X) & var(X)):
        print(subst)
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.ask(equal([a], Y) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.ask(equal(X, a) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.ask(equal([a, B, C], Y) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.ask(equal(X, a(B, C)) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.ask(equal(a(B, C), X) & equal([a, B, C], Y) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    db.tell(
        blub(A << A)
    )
    for subst in db.ask(blub(X) & equal(a << Y, X)):
        print(subst[X])
        print('Yes.')
        break
    else:
        print('No.')

    #for subst in db.ask(equal([a, B, C|D], Y) & univ(X, Y)):
        #print(subst[X], ':', subst[Y])
        #print('Yes.')
        #break
    #else:
        #print('No.')


#def rec(db):
    #for subst in db.ask(equal(X, a(X))):
        #print(subst[X])
    #print()


db = Database()
xor_test(db)
eqtest(db)
barbara(db)
varunify(db)
subtraction(db)
stdtypes(db)
difflist(db)
genealogy(db)
unify_test(db)
backwards(db)
univ_test(db)
#show_db(db)
#rec(db)
