# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = "0.2.5a"
__date__ = "2014-09-27"
__author__ = "Mick Krippendorf <m.krippendorf@freenet.de>"
__license__ = "MIT"


def test_builder():
    from hornet import build_term

    from hornet.symbols import _, f, a, b, c, d, e, X, Y, Z

    print(build_term(a))
    print(build_term(f(a, b) << b & c & d))
    print(build_term(f(X, Y) << b(X) & c(Y) & d))
    print(build_term(f(X, Y) << b(X) & c(Y) & d(_, Z, [e, d | a])))
    print(build_term(f(X, Y) << b(X) & c(Y) & d(_, Z, [e, d | [a]])))
    print(build_term(a * (b + c)))


def test_resolver():
    from pprint import pprint

    from hornet import Database
    from hornet.symbols import _, f, g, h, a, b, c, X, Y, Z

    db = Database()
    db.tell(
        a,
        f(a, b, c),
        f(a, a, a),
        f(c, b, a),
        f(X, Y, Z) << g(X, a) & h(Y, b) & c,
        g(X, X, Y),
        h(X) << g(X, a, _) | g(X, b, _),
    )
    pprint(db)

    for subst in db.ask(g(a, Z, Z)):
        pprint(subst)

    for subst in db.ask(g([a, b | c], Z, Z)):
        pprint(subst)

    for subst in db.ask(f(X, Y, Z)):
        pprint(subst)

    for subst in db.ask(h(X)):
        pprint(subst)

    for subst in db.ask(~g(a, b, Y)):
        print(subst)


if __name__ == "__main__":
    test_builder()
    test_resolver()
