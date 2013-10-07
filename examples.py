from expressions import wrap
from resolver import Database, UnificationFailed
from system import *


def eqtest(db, X, a):
    for subst in db.query(equal(a, X)):
        print(subst[X])
        for a, b in subst.items():
            print(type(a), ':', type(b))
    print()


def barbara(db, socrates, plato, aristotle, man, mortal, Who, X):
    db.assertz(
        man(socrates),
        man(plato),
        man(aristotle),
        mortal(X) <<
            man(X),
    )
    for subst in db.query(mortal(Who)):
        print(subst[Who])
    print()


def varunify(db, X, Y, Z):
    print(db.compile(equal(X, Z) & equal(Y, Z)))
    for subst in db.query(equal(X, Z) & equal(Y, Z)):
        print(sorted(subst.items()))
    print()


def pyfunc_test(db, X, Y):
    def unequal(X, Y):
        if X == Y:
            raise UnificationFailed
    db.assertz(unequal)


def pyfunc(db, unequal, X, Y):
    db.consult(pyfunc_test)
    for subst in db.query(unequal('holla', 'hallo')):
        print('Yes.')
        break
    else:
        print('No.')
    for subst in db.query(unequal(1, 1)):
        print('Yes.')
        break
    else:
        print('No.')
    print()


def subtraction(db, A, B, C, D):
    q = equal(A, 5) & equal(B, 2) & equal(C, 1) & let(D, A - B - C)
    for subst in db.query(q):
        print(subst[A], '-', subst[B], '-', subst[C], '==', subst[D])
    print()


def stdtypes(db, X):
    for subst in db.query(equal(10, X) & equal(X, 10)):
        print(sorted(subst.items()))

    for subst in db.query(equal('hallo', X) & equal(X, 'hallo')):
        print(sorted(subst.items()))

    for subst in db.query(equal([], X) & equal(X, [])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1], X) & equal(X, [1])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1 | wrap(2)], X) & equal(X, [wrap(1) | 2])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1, 2], X) & equal(X, [1, 2])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1, wrap(2) | 3], X) & equal(X, [1, 2 | wrap(3)])):
        print(sorted(subst.items()))

    for subst in db.query(equal([1, wrap(2), 3], X) & equal(X, [1, 2 | wrap(3)])):
        print('Yes.')
        break
    else:
        print('No.')
    print()


def difflist(db, appenddl, A, B, C, U, V, W, X):
    db.assertz(
        appenddl(A - B, B - C, A - C),
    )
    q = appenddl([1, 2 | U] - U, [3, 4 | V] - V, W - [5, 6 | X])
    for subst in db.query(q):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    for subst in db.query(q & equal(X, [7])):
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()


def tribes(db, sam, joe, jim, bob, dan, hal, tom, lee, son, descendant,
           ancestor, related, related_, directly_related, forefather, tribe,
           Tribe, X, Y, Z, Seen, test, U, V, W):

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
            not_(member(Z, Seen)) &
            related_(Z, Y, Seen),

        related_(X, X, _),
        related_(X, Y, Seen) <<
            related(X, Y, [X | Seen]),

        directly_related(X, Y) <<
            son(X, Y),
        directly_related(X, Y) <<
            son(Y, X),

        # Z is the forefather of X:
        forefather(Z, X) <<
            son(X, Y) &
            forefather(Z, Y) & cut,
        forefather(Z, Z),

        tribe(X, [Z | Tribe]) <<
            forefather(Z, X) &
            findall(Y, descendant(Y, Z), Tribe),
            #findall(Y, descendant(Y, Z), Tribe, U),
            #findall(test(Y, U, test(U)), descendant(Y, Z), Tribe) &
            #equal(W, bob) & equal(Tribe, [test(_, V, _) | _]) & equal(W, V),

    )


def genealogy(db, joe, bob, dan, lee, descendant, ancestor, related, tribe, A,
              B):

    db.consult(tribes)

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
    for subst in db.query(not_(related(A, A))):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('who belongs to joe\'s tribe?')
    for subst in db.query(tribe(joe, A)):
        print(subst[A])
    print()

    print('what clauses does the predicate descendant/2 consist of?')
    for subst in db.query(listing(descendant, 2)):
        print('Yes.')
        break
    else:
        print('No.')
    print()


db = Database()
#db.consult(eqtest)
db.consult(barbara)
db.consult(varunify)
db.consult(pyfunc)
db.consult(subtraction)
db.consult(stdtypes)
db.consult(difflist)
db.consult(genealogy)
