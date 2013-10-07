from resolver import hornet, Database, UnificationFailed
from system import not_, greater, findall, let, equal, join, writeln, _, cut


@hornet
def fbtest(db, fizzbuzz, fb, fb_out, divisible, V, Vs, N, N1, Max, D, S, X):

    db.assertz(

        fizzbuzz(N, Max) <<
            not_(greater(N, Max)) &
            findall(V, fb(V, N), Vs) &
            fb_out(N, Vs) &
            let(N1, N + 1) &
            fizzbuzz(N1, Max),

        fb('fizz', N) << divisible(N, 3),
        fb('buzz', N) << divisible(N, 5),

        fb_out(N, []) << writeln(N) & cut,
        fb_out(_, Vs) << join(Vs, S) & writeln(S),

        divisible(N, D) << let(X, N % D) & equal(X, 0),

    )

    for subst in db.query(fizzbuzz(1, 100)):
        break


fbtest(Database())
