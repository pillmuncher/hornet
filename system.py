from copy import deepcopy
from functools import reduce
from resolver import unify, UnificationFailed
from expressions import unit, wrap, new_list, Nil, nil, _C_
from util import flip
from pprint import pprint


__all__ = [
    '_', 'cut', 'fail', 'true', 'not_', 'member', 'findall', 'greater', 'write',
    'writeln', 'nl', 'equal', 'reverse', 'call', 'listing', 'let', 'X', 'L'
]

globals().update((each, unit(each)) for each in __all__)


def predicates(db,
               P, Q, X, Y, Z, Tail, Object, Goal, List, Rest, Predicate,
               Arity):

    db.assertz(

        cut,

        fail[_fail],

        true,

        not_(X) <<
            X & cut[_fail],
        not_(_),

        findall(Object, Goal, List)[_findall_3],
        findall(Object, Goal, List, Rest)[_findall_4],

        member(X, [X | _]),
        member(X, [_ | Tail]) <<
            member(X, Tail),

        reverse(X, Y) <<
            reverse(X, [], Y),

        reverse([], Y, Y),
        reverse([X | P], Q, Y) <<
            reverse(P, [X | Q], Y),

        write(X)[_write],

        writeln(X)[_writeln],

        nl[lambda *a: print()],

        equal(P, P),

        call(Goal) <<
            Goal,

        listing[_listing_0],

        listing(Predicate)[_listing_1],

        listing(Predicate, Arity)[_listing_2],

        greater(X, Y)[_greater],

        let(X, Y)[_let],

        _C_([X|L], X, L),

    )


def print_term(term, env, db, trail):
    print(term)


def print_env(term, env, db, trail):
    print(env)


def print_db(term, env, db, trail):
    pprint(db)


def print_trail(term, env, db, trail):
    pprint(trail)


def _fail(term, env, db, trail):
    raise UnificationFailed


def _write(term, env, db, trail):
    print(env.X, end='')


def _writeln(term, env, db, trail):
    print(env.X)


def _findall_3(term, env, db, trail):
    results = [deepcopy(env.Object) for each in db |- env.Goal]
    unify(env.List, make_list(db, results, nil), trail)


def _findall_4(term, env, db, trail):
    results = [deepcopy(env.Object) for each in db |- env.Goal]
    unify(env.List, make_list(db, results, env.Rest), trail)


def make_list(db, items, rest):
    return db.compile(new_list(items, rest))


def _listing_0(term, env, db, trail):
    for each in db.items():
        _listing(*each)


def _listing_1(term, env, db, trail):
    for indicator in db.indicators[env.Predicate()]:
        _listing(indicator, db.get(indicator))


def _listing_2(term, env, db, trail):
    indicator = env.Predicate.name, env.Arity.name
    _listing(indicator, db.get(indicator))


def _listing(indicator, clauses):
    print('{}/{}:'.format(*indicator))
    for clause in clauses:
        print('    {}.'.format(clause))
    print()


def _greater(term, env, db, trail):
    if not env.X() > env.Y():
        raise UnificationFailed


def _let(term, env, db, trail):
    unify(env.X, db.compile(wrap(env.Y())), trail)
