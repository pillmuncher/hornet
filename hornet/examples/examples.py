#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from hornet import *

from hornet.symbols import A, B, C, D, Seen, Tribe, U, V, W, Who, X, Y, Z
from hornet.symbols import ancestor, appenddl, aristotle, bob, dan, descendant
from hornet.symbols import directly_related, patriarch, hal, jim, joe, lee, man
from hornet.symbols import mortal, plato, related, related_, sam, socrates, son
from hornet.symbols import test, tom, tribe, nonequal, lwriteln, a, b, c, d, e
from hornet.symbols import horst


def show_db(db):
    for each in db.query(listing):
        break


def xor_test(db):
    for each in fail ^ true, true ^ fail, fail ^ fail, true ^ true:
        for subst in db.query(equal(each, X) & call(X)):
           print(subst[X])
    print()


def eqtest(db):
    for subst in db.query(equal(tom, X)):
        print(subst[X])
        for a, b in subst.items():
            print(type(a), ':', type(b))
    print()


def barbara(db):
    db.assertz(
        man(socrates),
        man(plato),
        man(aristotle),
        man(horst),
        mortal(X) <<
            man(X),
    )
    for subst in db.query(mortal(Who)):
        print(subst[Who])
    print()


def varunify(db):
    for subst in db.query(equal(X, Z) & equal(Y, Z)):
        for k, v in sorted(subst.items()):
            print(k, '=', v, '=', v())
    print()


def subtraction(db):
    q = equal(A, 5) & equal(B, 2) & equal(C, 1) & let(D, A - B - C)
    for subst in db.query(q):
        print(subst[A], '-', subst[B], '-', subst[C], '==', subst[D])
    print()


def stdtypes(db):
    for subst in db.query(equal(10, X) & equal(X, 10)):
        print(sorted(subst.items()))

    for subst in db.query(equal('hallo', X) & equal(X, 'hallo')):
        print(sorted(subst.items()))

    for subst in db.query(equal([], X) & equal(X, [])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1], X) & equal(X, [1])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1 | promote(2)], X) & equal(X, [promote(1) | 2])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1, 2], X) & equal(X, [1, 2])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1, promote(2) | 3], X) & equal(X, [1, 2 | promote(3)])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1, promote(2), 3], X) & equal(X, [1, 2 | promote(3)])):
        print('Yes.')
        break
    else:
        print('No.')
    print()


def difflist(db):
    db.assertz(
        appenddl(A - B, B - C, A - C),
        (A - B + B - C) / (A - C),
    )
    q = appenddl([1, 2 | U] - U, [3, 4 | V] - V, W - [5, 6 | X])
    for subst in db.query(q):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    for subst in db.query(q & equal(X, [7, 8, 9])):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    q = ([1, 2 | U] - U + [3, 4 | V] - V) / (W - [5, 6 | X])
    for subst in db.query(q):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    for subst in db.query(q & equal(X, [7, 8, 9])):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()


def unify_test(db):

    for subst in db.query(join(['hallo', 'welt'], 'hallowelt')):
        print('Yes.')
        break
    else:
        print('No.')


def tribes(db):

    db.assertz(

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
            findall(test(Y, U), descendant(Y, Z), Tribe, U) & equal(U, [patriarch]),
            #findall(test(Y, U, test(U)), descendant(Y, Z), Tribe) &
            #equal(W, bob) & equal(Tribe, [test(_, V, _) | _]) & equal(W, V),
            #findall(test(Y, U), descendant(Y, Z) & equal(Y, U), Tribe),

    )


def genealogy(db):

    tribes(db)

    print('who is an ancestor of who?')
    for subst in db.query(ancestor(A, B)):
        print(subst[A], 'of', subst[B])
    print()

    print('who are joe\'s descendants?')
    for subst in db.query(descendant(A, joe)):
        print(subst[A])
    print()

    print('who are dan\'s ancestors?')
    for subst in db.query(ancestor(A, dan)):
        print(subst[A])
    print()

    print('who is bob related to?')
    for subst in db.query(related(bob, A)):
        print(subst[A])
    print()

    print('who is related to bob?')
    for subst in db.query(related(A, bob)):
        print(subst[A])
    print()

    print('who is lee related to?')
    for subst in db.query(related(lee, A)):
        print(subst[A])
    print()

    print('who is related to lee?')
    for subst in db.query(related(A, lee)):
        print(subst[A])
    print()

    print('is lee related to joe?')
    for subst in db.query(related(lee, joe)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('is lee related to bob?')
    for subst in db.query(related(lee, bob)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('one is not a relative of oneself. true?')
    for subst in db.query(~related(A, A)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('who belongs to joe\'s tribe?')
    for subst in db.query(tribe(joe, A) & lwriteln(A)):
        #print(subst[A])
        pass
    print()

    print('what clauses does the predicate descendant/2 consist of?')
    for subst in db.query(listing(descendant, 2)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('test')
    for subst in db.query(related(bob, X) & cut & writeln(X) & fail):
        print('Yes.')
        #break
    else:
        print('No.')
    print()


def backwards(db):

    #for subst in db.query(member(X, [a, b, c])):
        #print(subst[X])
        #print('Yes')
        #break
    #else:
        #print('No.')

    #for subst in db.query(equal(W, [X, Y, Z]) & member(a, W) & member(b, W)):
    #for subst in db.query(equal(W, [X, Y, Z]) & member(a, W)):
        #print(subst[W])

    for subst in db.query(append([a, b], [c, d, e], X)):
        print(subst[X])

    #for subst in db.query(append(X, Y, [a, b, c, d, e])):
        #print(subst[X], subst[Y])

    #for subst in db.query(ignore(true) & ignore(fail)):
        #print('Yes, ignored.')




def univ_test(db):

    for subst in db.query(var(X)):
        print(subst)
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.query(equal(a, X) & var(X)):
        print(subst)
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.query(equal([a], Y) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.query(equal(X, a) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.query(equal([a, B, C], Y) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.query(equal(X, a(B, C)) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    for subst in db.query(equal(a(B, C), X) & equal([a, B, C], Y) & univ(X, Y)):
        print(subst[X], ':', subst[Y])
        print('Yes.')
        break
    else:
        print('No.')

    #for subst in db.query(equal([a, B, C|D], Y) & univ(X, Y)):
        #print(subst[X], ':', subst[Y])
        #print('Yes.')
        #break
    #else:
        #print('No.')


#def rec(db):
    #for subst in db.query(equal(X, a(X))):
        #print(subst[X])
    #print()


db = Database()
#xor_test(db)
#eqtest(db)
#barbara(db)
#varunify(db)
#subtraction(db)
#stdtypes(db)
#difflist(db)
#genealogy(db)
#unify_test(db)
backwards(db)
#univ_test(db)
#rec(db)
#show_db(db)
