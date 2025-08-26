# Copyright (c) 2014 Mick Krippendorf <m.krippendorf+hornet@posteo.de>


def test_builder():
    from hornet import build_term
    from hornet.symbols import X, Y, Z, _, a, b, c, d, e, f

    print(build_term(a))
    print(build_term(f(a, b) << b & c & d))
    print(build_term(f(X, Y) << b(X) & c(Y) & d))
    print(build_term(f(X, Y) << b(X) & c(Y) & d(_, Z, [e, d | a])))
    print(build_term(f(X, Y) << b(X) & c(Y) & d(_, Z, [e, d | [a]])))
    print(build_term(a * (b + c)))


def test_resolver():
    from pprint import pprint

    from hornet import Database
    from hornet.symbols import X, Y, Z, _, a, b, c, f, g, h

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
