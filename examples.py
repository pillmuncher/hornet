from expressions import wrap
from resolver import Database
from system import *


def barbara(db, socrates, plato, aristotle, man, mortal, Who, X):
    db.assertz(
        man(socrates),
        man(plato),
        man(aristotle),
        mortal(X) <<
            man(X),
    )
    for subst in db |- mortal(Who):
        print(subst[Who])
    print()


def varunify(db, X, Y, Z):
    print(db.compile(equal(X, Z) & equal(Y, Z)))
    for subst in db |- equal(X, Z) & equal(Y, Z):
        print(sorted(subst.items()))
    print()


def stdtypes(db, X):
    for subst in db |- equal(10, X) & equal(X, 10):
        print(sorted(subst.items()))

    for subst in db |- equal('hallo', X) & equal(X, 'hallo'):
        print(sorted(subst.items()))

    for subst in db |- equal([], X) & equal(X, []):
        print(sorted(subst.items()))

    for subst in db |- equal([1], X) & equal(X, [1]):
        print(sorted(subst.items()))

    for subst in db |- equal([1 | wrap(2)], X) & equal(X, [wrap(1) | 2]):
        print(sorted(subst.items()))

    for subst in db |- equal([1, 2], X) & equal(X, [1, 2]):
        print(sorted(subst.items()))

    for subst in db |- equal([1, wrap(2) | 3], X) & equal(X, [1, 2 | wrap(3)]):
        print(sorted(subst.items()))

    for subst in db |- equal([1, wrap(2), 3], X) & equal(X, [1, 2 | wrap(3)]):
        print('Yes.')
        break
    else:
        print('No.')
    print()


def difflist(db, appenddl, diff, A, B, C, U, V, W, X):
    db.assertz(
        appenddl(diff(A, B),
                 diff(B, C),
                 diff(A, C))
    )
    q = appenddl(diff([1, 2 | U], U),
                 diff([3, 4 | V], V),
                 diff(W, [5, 6 | X]))
    for subst in db |- q:
        for k, v in sorted(subst.items()):
            print(k, ':', v)
    print()
    for subst in db |- q & equal(X, [7]):
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
    for subst in db |- ancestor(A, B):
        print(subst[A], 'of', subst[B])
    print()

    print('who are joe\'s descendants?')
    for subst in db |- descendant(A, joe):
        print(subst[A])
    print()

    print('who are dan\'s ancestors?')
    for subst in db |- ancestor(A, dan):
        print(subst[A])
    print()

    print('who is bob related to?')
    for subst in db |- related(bob, A):
        print(subst[A])
    print()

    print('who is related to bob?')
    for subst in db |- related(A, bob):
        print(subst[A])
    print()

    print('who is lee related to?')
    for subst in db |- related(lee, A):
        print(subst[A])
    print()

    print('who is related to lee?')
    for subst in db |- related(A, lee):
        print(subst[A])
    print()

    print('is lee related to joe?')
    for subst in db |- related(lee, joe):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('is lee related to bob?')
    for subst in db |- related(lee, bob):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('one is not a relative of oneself. true?')
    for subst in db |- not_(related(A, A)):
        print('Yes.')
        break
    else:
        print('No.')
    print()

    print('who belongs to joe\'s tribe?')
    for subst in db |- tribe(joe, A):
        print(subst[A])
    print()

    print('what clauses does the predicate descendant/2 consist of?')
    for subst in db |- listing(descendant, 2):
        print('Yes.')
        break
    else:
        print('No.')
    print()


db = Database()
db.consult(barbara)
db.consult(varunify)
db.consult(stdtypes)
db.consult(difflist)
db.consult(genealogy)
