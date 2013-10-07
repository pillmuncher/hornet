from copy import deepcopy
from numbers import Number
from resolver import unify, UnificationFailed, Atom
from expressions import unit, wrap, new_list, Nil, nil, _C_
from pprint import pprint


__all__ = [
    '_', 'cut', 'fail', 'true', 'not_', 'or_', 'member', 'findall', 'greater',
    'write', 'writeln', 'nl', 'equal', 'unequal', 'reverse', 'call', 'listing',
    'let', 'atomic', 'real', 'integer', 'numeric', 'once', 'append', 'lwriteln',
    'join'
]

globals().update((each, unit(each)) for each in __all__)


X = unit('X')
L = unit('L')

def predicates(db,
               P, Q, X, Y, Z, Tail, Object, Goal, List, Rest, Predicate,
               A, B, C, D, H, T, S, Arity):

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

        append([], A, A),
        append([A|B], C, [A|D]) <<
                append(B, C, D),

        once(Goal) <<
            Goal & cut,
        once(Goal) <<
            Goal & cut,

        reverse(X, Y) <<
            reverse(X, [], Y),

        reverse([], Y, Y),
        reverse([X | P], Q, Y) <<
            reverse(P, [X | Q], Y),

        write(X)[_write],

        writeln(X)[_writeln],

        lwriteln([H|T]) << write(H) & lwriteln(T),
        lwriteln([]) << nl,

        nl[lambda *a: print()],

        equal(P, P),

        unequal(P, P) << cut[_fail],
        unequal(_, _),

        call(Goal) <<
            Goal,

        once(Goal) <<
            Goal & cut,

        listing[_listing_0],

        listing(Predicate)[_listing_1],

        listing(Predicate, Arity)[_listing_2],

        greater(X, Y)[_greater],

        let(X, Y)[_let],

        _C_([X|L], X, L),

        atomic(X)[_atomic],

        integer(X)[_integer],

        real(X)[_real],

        numeric(X)[_numeric],

        or_(P, Q)[_or],

        join(L, S)[_join] << cut,

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
    results = [deepcopy(env.Object) for each in db.query(env.Goal)]
    unify(env.List, make_list(db, results, nil), trail)


def _findall_4(term, env, db, trail):
    results = [deepcopy(env.Object) for each in db.query(env.Goal)]
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
    result = env.Y()
    if result >= 0:
        unify(env.X, db.compile(wrap(result)), trail)
    else:
        unify(env.X, db.compile(-wrap(-result)), trail)


def _atomic(term, env, db, trail):
    if not isinstance(env.X, Atom):
        raise UnificationFailed
    if not isinstance(env.X(), (str, Number)):
        raise UnificationFailed


def _integer(term, env, db, trail):
    if not isinstance(env.X, Atom):
        raise UnificationFailed
    if not isinstance(env.X(), int):
        raise UnificationFailed


def _real(term, env, db, trail):
    if not isinstance(env.X, Atom):
        raise UnificationFailed
    if not isinstance(env.X(), float):
        raise UnificationFailed


def _numeric(term, env, db, trail):
    if not isinstance(env.X, Atom):
        raise UnificationFailed
    if not isinstance(env.X(), Number):
        raise UnificationFailed


def _or(term, env, db, trail):  # TODO: implement this!
    raise UnificationFailed


def _join(term, env, db, trail):
    unify(env.S, db.compile(wrap(''.join(env.L()))), trail)
