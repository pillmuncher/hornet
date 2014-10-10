#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


from functools import wraps, partial


from hornet import *
from hornet.expressions import promote
from hornet.util import noop

from hornet.symbols import (
    A, B, C, D, Seen, Tribe, U, V, W, Who, X, Y, Z, ancestor, appenddl,
    aristotle, bob, dan, descendant, directly_related, patriarch, hal, jim,
    joe, lee, man, mortal, plato, related, related_, sam, socrates, son, test,
    tom, tribe, nonequal, lwriteln, a, b, c, d, e, blub,
)


show_funcs = []

def show(f=None, *, skip=False):
    if f is None:
        return partial(show, skip=skip)
    if skip:
        @wraps(f)
        def wrapper(*a, **k):
            print('\n\n' + f.__qualname__ + ': skipped\n')
    else:
        @wraps(f)
        def wrapper(*a, **k):
            print('\n\n' + f.__qualname__ + ':\n')
            return f(*a, **k)
    show_funcs.append(wrapper)
    return wrapper


def show_all(*a, **k):
    for f in show_funcs:
        f(*a, **k)


@show(skip=True)
def show_db(db):
    for each in db.ask(listing):
        break


@show
def xor_test(db):
    for each in fail ^ true, true ^ fail, fail ^ fail, true ^ true:
        for subst in db.ask(equal(each, X) & call(X)):
           print(subst[X])
    print()


@show
def eqtest(db):
    for subst in db.ask(equal(tom, X)):
        print(subst[X])
        for a, b in subst.items():
            print(type(a), ':', type(b))
    print()


@show
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


@show
def varunify(db):
    for subst in db.ask(equal(X, Z) & equal(Y, Z) & (equal(man, Z) | true)):
        for k, v in sorted(subst.items()):
            print(k, '=', v, '=', v())
    print()


@show
def subtraction(db):
    q = equal(A, 5) & equal(B, 2) & equal(C, 1) & let(D, A - B - C)
    for subst in db.ask(q):
        print(subst[A], '-', subst[B], '-', subst[C], '==', subst[D])
    print()


@show
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


@show
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


@show
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

        tribe(X, [X|Tribe]) <<
            findall(Y, related(X, Y), Tribe),
        #tribe(X, [Z | Tribe]) <<
            #patriarch(Z, X) &
            #findall(Y, descendant(Y, Z), Tribe),
            #findall(test(Y, U), descendant(Y, Z), Tribe, U) & equal(U, [patriarch]),
            #findall(test(Y, U, test(U)), descendant(Y, Z), Tribe) &
            #equal(W, bob) & equal(Tribe, [test(_, V, _) | _]) & equal(W, V),
            #findall(test(Y, U), descendant(Y, Z) & equal(Y, U), Tribe),

    )


@show
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


@show
def member_test(db):

    for subst in db.ask(member(X, [a, b, c])):
        print(subst[X])
    print()

    for subst in db.ask(equal(W, [X, Y, Z]) & member(a, W)):
        print(subst[W])
    print()

    for subst in db.ask(equal(W, [X, Y, Z]) & member(a, W) & member(b, W)):
        print(subst[W])


@show
def append_test(db):

    for subst in db.ask(append([], [a, b, c, d, e], X)):
        print(subst[X])
    print()

    for subst in db.ask(append([a, b, c, d, e], [], X)):
        print(subst[X])
    print()

    for subst in db.ask(append([a, b], [c, d, e], X)):
        print(subst[X])
    print()

    for subst in db.ask(append([a, b, c, d], e, X)):
        print(subst[X])
    print()

    for subst in db.ask(append(X, [d, e], [a, b, c, d, e])):
        print(subst[X])
    print()

    for subst in db.ask(append([a, b, c], X, [a, b, c, d, e])):
        print(subst[X])
    print()

    for subst in db.ask(append(X, Y, [a, b, c, d, e])):
        print(subst[X], subst[Y])
    print()

    for subst in db.ask(append(X, Y, [a, b, c, d|e])):
        print(subst[X], subst[Y])


@show
def ignore_test(db):

    for subst in db.ask(ignore(true | true) & ignore(fail)):
        print('Yes, ignored.')


@show
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

    for subst in db.ask(equal(X, a(B, C)) & univ(X, [Y|Z])):
        print(subst[X], ':', subst[Y], ':', subst[Z])
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

    #db.tell(
        #blub << true & (A << (A & true))
    #)
    #for subst in db.ask(blub):
        #print(subst[X])
        #print('Yes.')
        #break
    #else:
        #print('No.')
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


@show
def cut_test(db):

    from ..symbols import branch, root, foo, bar, A, B, X, Y

    db.tell(

        root(X, Y) <<
            branch(X, Y),

        branch(X, Y) << foo(X) & bar(Y),
        branch(X, Y) << foo(Y) & bar(X),

        foo(1) << cut,
        foo(2),
        bar(3),
        bar(4),

    )

    for subst in db.ask(root(A, B)):
        print(subst)



@show
def transpose_test(db):

    from ..symbols import a, b, c, d, e, f, g, h, i, j, k, l, X, L

    L0 = [[a, b, c, d], [e, f, g, h], [i, j, k, l]]
    for subst in db.ask(equal(L0, L) & transpose(L, X)):
        print(subst[L])
        print(subst[X])


@show
def maplist_test(db):

    for subst in db.ask(maplist(writeln, [1, 2, 3, 4, 5])):
        pass


#@show
#def length_test(db):

    #for subst in db.ask(length([1, 2, 3, 4, 5], X)):
        #print(subst[X])

    #for subst in db.ask(length(X, 3)):
        #print(subst[X])
        #break

    #for subst in db.ask(length([1, 2, 3, 4, 5], 5)):
        #print('Yes.')
        #break
    #else:
        #print('No.')

    #for i, subst in enumerate(db.ask(length(X, Y))):
        #print(subst[X], subst[Y])
        #if i == 5:
            #break



show_all(Database())
