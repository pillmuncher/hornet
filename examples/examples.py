# # Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
#
# from functools import partial, wraps
# from itertools import islice
#
# from hornet import Database
#
# show_funcs = []
#
#
# def show(f=None, *, skip=False):
#     if f is None:
#         return partial(show, skip=skip)
#
#     @wraps(f)
#     def wrapper(*a, **k):
#         if skip:
#             return
#         print("\n\n" + f.__qualname__ + ":\n")
#         return f(*a, **k)
#
#     show_funcs.append(wrapper)
#     return wrapper
#
#
# def show_all(*a, **k):
#     for f in show_funcs:
#         f(*a, **k)
#
#
# @show(skip=True)
# def show_db(db):
#     from hornet import listing
#
#     for _ in db.ask(listing):
#         break
#
#
# @show(skip=False)
# def xor_test(db):
#     from hornet import call, equal, fail, true
#     from hornet.symbols import X
#
#     for each in fail ^ true, true ^ fail, fail ^ fail, true ^ true:
#         for subst in db.ask(equal(each, X) & call(X)):
#             print(subst[X])
#     print()
#
#
# @show(skip=False)
# def eqtest(db):
#     from hornet import equal
#     from hornet.symbols import X, tom
#
#     for subst in db.ask(equal(tom, X)):
#         print(subst[X])
#         for left, right in subst.items():
#             print(type(left), ":", type(right))
#     print()
#
#
# @show(skip=False)
# def barbara(db):
#     from hornet.symbols import (
#         Who,
#         X,
#         aristotle,
#         god,
#         man,
#         mortal,
#         plato,
#         socrates,
#         zeus,
#     )
#
#     db.tell(
#         god(zeus),
#         man(socrates),
#         man(plato),
#         man(aristotle),
#         mortal(X) << man(X),
#     )
#     for subst in db.ask(mortal(Who)):
#         print(subst[Who])
#     print()
#
#
# @show(skip=False)
# def varunify(db):
#     from hornet import equal, true
#     from hornet.symbols import X, Y, Z, man, true
#
#     for subst in db.ask(equal(X, Z) & equal(Y, Z) & (equal(man, Z) | true)):
#         for k, v in sorted(subst.items()):
#             print(k, "=", v, "=", v())
#     print()
#
#
# @show(skip=False)
# def subtraction(db):
#     from hornet import equal, let
#     from hornet.symbols import A, B, C, D
#
#     q = equal(A, 5) & equal(B, 2) & equal(C, 1) & let(D, A - B - C)
#     for subst in db.ask(q):
#         print(subst[A], "-", subst[B], "-", subst[C], "==", subst[D])
#     print()
#
#
# @show(skip=False)
# def stdtypes(db):
#     from hornet import equal
#     from hornet.expressions import promote
#     from hornet.symbols import X
#
#     for subst in db.ask(equal(10, X) & equal(X, 10)):
#         print(sorted(subst.items()))
#
#     for subst in db.ask(equal("hallo", X) & equal(X, "hallo")):
#         print(sorted(subst.items()))
#
#     for subst in db.ask(equal([], X) & equal(X, [])):
#         print(sorted(subst.items()))
#
#     for subst in db.ask(equal([1], X) & equal(X, [1])):
#         print(sorted(subst.items()))
#     for subst in db.ask(equal([1 | promote(2)], X) & equal(X, [promote(1) | 2])):
#         print(sorted(subst.items()))
#
#     for subst in db.ask(equal([1, 2], X) & equal(X, [1, 2])):
#         print(sorted(subst.items()))
#
#     for subst in db.ask(equal([1, promote(2) | 3], X) & equal(X, [1, 2 | promote(3)])):
#         print(sorted(subst.items()))
#
#     for subst in db.ask(equal([1, promote(2), 3], X) & equal(X, [1, 2 | promote(3)])):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#     print()
#
#
# @show(skip=False)
# def difflist(db):
#     from hornet import equal
#     from hornet.symbols import A, B, C, U, V, W, X, appenddl
#
#     db.tell(
#         appenddl(A - B, B - C, A - C),
#         (A - B + B - C) / (A - C),
#     )
#     q = appenddl([1, 2 | U] - U, [3, 4 | V] - V, W - [5, 6 | X])
#     for subst in db.ask(q):
#         for k, v in sorted(subst.items()):
#             print(k, ":", v)
#     print()
#     for subst in db.ask(q & equal(X, [7, 8, 9])):
#         for k, v in sorted(subst.items()):
#             print(k, ":", v)
#     print()
#     q = ([1, 2 | U] - U + [3, 4 | V] - V) / (W - [5, 6 | X])
#     for subst in db.ask(q):
#         for k, v in sorted(subst.items()):
#             print(k, ":", v)
#     print()
#     for subst in db.ask(q & equal(X, [7, 8, 9])):
#         for k, v in sorted(subst.items()):
#             print(k, ":", v)
#     print()
#
#
# @show(skip=False)
# def join_test(db):
#     from hornet import join
#
#     for _ in db.ask(join([], "")):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     try:
#         for _ in db.ask(join([1], "1")):
#             print("Yes.")
#             break
#         else:
#             print("No.")
#     except TypeError:
#         print("Expected Exception raised.")
#
#
# @show(skip=False)
# def unify_test(db):
#     from hornet import join
#
#     for _ in db.ask(join(["hallo", "welt"], "hallowelt")):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#
# def tribes(db):
#     from hornet import cut, findall, member
#     from hornet.symbols import (
#         Seen,
#         Tribe,
#         X,
#         Y,
#         Z,
#         _,
#         ancestor,
#         bob,
#         dan,
#         descendant,
#         directly_related,
#         hal,
#         jim,
#         joe,
#         lee,
#         patriarch,
#         related,
#         related_,
#         sam,
#         son,
#         tom,
#         tribe,
#     )
#
#     db.tell(
#         son(joe, sam),  # joe is the son of sam, etc.
#         # son(bob, sam),
#         son(jim, joe),
#         son(tom, bob),
#         son(hal, bob),
#         son(dan, jim),
#         son(lee, jim),
#         # X is a descendant of Y:
#         descendant(X, Y) << son(X, Y),  # one's son is one's descendant
#         descendant(X, Z) << son(Y, Z)  # a descendant of one's son
#         & descendant(X, Y),  # is also one's descendant
#         # X is an ancestor of Y:
#         ancestor(X, Y) << descendant(Y, X),  # one is an ancestor of one's descendant
#         related(X, Y) << related(X, Y, [X]),
#         related(X, Y, Seen) << directly_related(X, Z)
#         & ~member(Z, Seen)
#         & related_(Z, Y, Seen),
#         related_(X, X, _),
#         related_(X, Y, Seen) << related(X, Y, [X | Seen]),
#         directly_related(X, Y) << son(X, Y) | son(Y, X),
#         # Z is the patriarch of X:
#         patriarch(Z, X) << son(X, Y) & patriarch(Z, Y) & cut,
#         patriarch(Z, Z),
#         tribe(X, [X | Tribe]) << findall(Y, related(Y, X), Tribe),
#         # tribe(X, [Z | Tribe]) <<
#         # patriarch(Z, X) &
#         # findall(Y, descendant(Y, Z), Tribe),
#         # findall(test(Y, U), descendant(Y, Z), Tribe, U) & equal(U, [patriarch]),
#         # findall(test(Y, U, test(U)), descendant(Y, Z), Tribe) &
#         # equal(W, bob) & equal(Tribe, [test(_, V, _) | _]) & equal(W, V),
#         # findall(test(Y, U), descendant(Y, Z) & equal(Y, U), Tribe),
#     )
#
#
# @show(skip=False)
# def genealogy(db):
#     from hornet import cut, fail, listing, writeln
#     from hornet.symbols import (
#         A,
#         B,
#         X,
#         ancestor,
#         bob,
#         dan,
#         descendant,
#         joe,
#         lee,
#         lwriteln,
#         related,
#         tribe,
#     )
#
#     tribes(db)
#
#     print("who is an ancestor of who?")
#     for subst in db.ask(ancestor(A, B)):
#         print(subst[A], "of", subst[B])
#     print()
#
#     print("who are joe's descendants?")
#     for subst in db.ask(descendant(A, joe)):
#         print(subst[A])
#     print()
#
#     print("who are dan's ancestors?")
#     for subst in db.ask(ancestor(A, dan)):
#         print(subst[A])
#     print()
#
#     print("who is bob related to?")
#     for subst in db.ask(related(bob, A)):
#         print(subst[A])
#     print()
#
#     print("who is related to bob?")
#     for subst in db.ask(related(A, bob)):
#         print(subst[A])
#     print()
#
#     print("who is lee related to?")
#     for subst in db.ask(related(lee, A)):
#         print(subst[A])
#     print()
#
#     print("who is related to lee?")
#     for subst in db.ask(related(A, lee)):
#         print(subst[A])
#     print()
#
#     print("is lee related to joe?")
#     for subst in db.ask(related(lee, joe)):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#     print()
#
#     print("is lee related to bob?")
#     for subst in db.ask(related(lee, bob)):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#     print()
#
#     print("one is not a relative of oneself. true?")
#     for subst in db.ask(~related(A, A)):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#     print()
#
#     print("who belongs to joe's tribe?")
#     for subst in db.ask(tribe(joe, A) & lwriteln(A)):
#         # print(subst[A])
#         pass
#     print()
#
#     print("what clauses does the predicate descendant/2 consist of?")
#     for subst in db.ask(listing(descendant, 2)):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#     print()
#
#     print("test")
#     for subst in db.ask(related(bob, X) & cut & writeln(X) & fail):
#         print("Yes.")
#         # break
#     else:
#         print("No.")
#     print()
#
#
# @show(skip=False)
# def member_test(db):
#     from hornet import equal, member
#     from hornet.symbols import W, X, Y, Z, a, b, c
#
#     for subst in db.ask(member(X, [a, b, c])):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(equal(W, [X, Y, Z]) & member(a, W)):
#         print(subst[W])
#     print()
#
#     for subst in db.ask(equal(W, [X, Y, Z]) & member(a, W) & member(b, W)):
#         print(subst[W])
#
#     for subst in islice(db.ask(member(a, W)), 6):
#         print(subst[W])
#
#     for subst in islice(db.ask(member(X, W) & equal(X, b)), 6):
#         print(subst[W])
#
#     for subst in islice(db.ask(member(X, W) & member(X, [a, b, c])), 15):
#         print(subst[W])
#
#
# @show(skip=False)
# def length_test(db):
#     from hornet import equal, length
#     from hornet.symbols import W, X, Y, a, b
#
#     for subst in db.ask(length([1, 2, 3, 4, 5], X)):
#         print(subst[X])
#
#     for subst in db.ask(length(X, -1)):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(length(X, 3)):
#         print(subst[X])
#         break
#
#     for subst in db.ask(length([1, 2, 3, 4, 5], 5)):
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in islice(db.ask(length(X, Y)), 6):
#         print(subst[X], subst[Y])
#
#     for subst in islice(db.ask(equal(X, [a, b | W]) & length(X, Y)), 6):
#         print(subst[X], subst[Y])
#
#
# @show(skip=False)
# def member_length_test(db):
#     from hornet import length, member
#     from hornet.symbols import X, tom
#
#     for subst in db.ask(length(X, 3) & member(tom, X)):
#         # for subst in db.ask(member(tom, X) & length(X, 3)):
#         print(subst[X])
#
#
# @show(skip=False)
# def append_test(db):
#     from hornet import append
#     from hornet.symbols import X, Y, a, b, c, d, e
#
#     for subst in db.ask(append([], [a, b, c, d, e], X)):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(append([a, b, c, d, e], [], X)):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(append([a, b], [c, d, e], X)):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(append([a, b, c, d], e, X)):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(append(X, [d, e], [a, b, c, d, e])):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(append([a, b, c], X, [a, b, c, d, e])):
#         print(subst[X])
#     print()
#
#     for subst in db.ask(append(X, Y, [a, b, c, d, e])):
#         print(subst[X], subst[Y])
#     print()
#
#     for subst in db.ask(append(X, Y, [a, b, c, d | e])):
#         print(subst[X], subst[Y])
#
#
# @show(skip=False)
# def ignore_test(db):
#     from hornet import fail, ignore, true
#
#     for _ in db.ask(ignore(true | true) & ignore(fail)):
#         print("Yes, ignored.")
#
#
# @show(skip=False)
# def univ_test(db):
#     from hornet import equal, univ, var
#     from hornet.symbols import A, B, C, X, Y, Z, a, blub
#
#     for subst in db.ask(var(X)):
#         print(subst)
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal(a, X) & var(X)):
#         print(subst)
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal([a], Y) & univ(X, Y)):
#         print(subst[X], ":", subst[Y])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal(X, a) & univ(X, Y)):
#         print(subst[X], ":", subst[Y])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal([a, B, C], Y) & univ(X, Y)):
#         print(subst[X], ":", subst[Y])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal(X, a(B, C)) & univ(X, Y)):
#         print(subst[X], ":", subst[Y])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal(X, a(B, C)) & univ(X, [Y | Z])):
#         print(subst[X], ":", subst[Y], ":", subst[Z])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     for subst in db.ask(equal(a(B, C), X) & equal([a, B, C], Y) & univ(X, Y)):
#         print(subst[X], ":", subst[Y])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     db.tell(blub(A << A))
#     for subst in db.ask(blub(X) & equal(a << Y, X)):
#         print(subst[X])
#         print("Yes.")
#         break
#     else:
#         print("No.")
#
#     # db.tell(
#     # blub << true & (A << (A & true))
#     # )
#     # for subst in db.ask(blub):
#     # print(subst[X])
#     # print('Yes.')
#     # break
#     # else:
#     # print('No.')
#     # for subst in db.ask(equal([a, B, C|D], Y) & univ(X, Y)):
#     # print(subst[X], ':', subst[Y])
#     # print('Yes.')
#     # break
#     # else:
#     # print('No.')
#
#
# @show(skip=False)
# def rec(db):
#     from hornet import equal
#     from hornet.symbols import X, a
#
#     for _ in db.ask(equal(X, a(X))):
#         print("oh!")
#         break
#
#
# @show(skip=False)
# def cut_test(db):
#     from hornet import cut, equal, writeln
#     from hornet.symbols import A, B, X, Y, bar, branch, foo, root
#
#     # db.tell(
#     # root(X, Y) <<
#     # branch(X, Y),
#     # branch(X, Y) << foo(X) & bar(Y),
#     # branch(X, Y) << foo(Y) & bar(X),
#     # foo(1) << cut,
#     # foo(2),
#     # bar(3),
#     # bar(4),
#     # )
#     # for subst in db.ask(root(A, B)):
#     # print(subst)
#
#     db.tell(
#         root(X, Y) << branch(X, Y),
#         root(Y, X) << writeln([X, Y]) & branch(X, Y),
#         branch(X, Y) << equal(foo(1), X) & equal(bar(2), Y) & cut,
#         # branch(foo(1), bar(2)) << cut,
#     )
#
#     # for subst in db.ask(root(foo(A), bar(B))):
#     for subst in db.ask(root(A, B)):
#         print(subst)
#
#
# @show(skip=False)
# def transpose_test(db):
#     from hornet import equal, transpose
#     from hornet.symbols import L, X, a, b, c, d, e, f, g, h, i, j, k, l
#
#     L0 = [[a, b, c, d], [e, f, g, h], [i, j, k, l]]
#     for subst in db.ask(equal(L0, L) & transpose(L, X)):
#         print(subst[L])
#         print(subst[X])
#
#
# @show(skip=False)
# def maplist_test(db):
#     from hornet import maplist, writeln
#
#     for _ in db.ask(maplist(writeln, [1, 2, 3, 4, 5])):
#         pass
#
#
# show_all(Database())
