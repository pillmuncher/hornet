from expressions import pyfunc
from resolver import Database, UnificationFailed
from system import *


def grammar(db, s, np, vp, det, noun, verb, masculine, feminine, neuter,
           nominative, genitive, dative, accusative, plural, singular,
           intransitive, transitive, Gender, Number, Case, Trans,
           Rest, A, B, C, D, E, F, S):

    db.assertz(

        s(S) << s(S, []),


        s >>
            np(Number, nominative) &
            vp(Number, nominative, intransitive),

        s >>
            np(Number, Case) &
            vp(Number, Case, transitive),


        np(plural, Case) >>
            noun(_, plural, Case),

        np(Number, Case) >>
            det(Gender, Number, Case) &
            noun(Gender, Number, Case),


        vp(Number, nominative, intransitive) >>
            verb(Number, nominative, intransitive),

        vp(Number, accusative, intransitive) >>
            verb(Number, accusative, intransitive),

        vp(_, dative, transitive) >>
            verb(Number, nominative, transitive) &
            np(Number, nominative),

        vp(Number, nominative, transitive) >>
            verb(Number, nominative, transitive) &
            np(_, dative),

        vp(Number, nominative, transitive) >>
            verb(Number, accusative, transitive) &
            np(_, accusative),


        det(masculine, singular, nominative) >> ['der'],
        det(masculine, singular, genitive) >> ['des'],
        det(masculine, singular, dative) >> ['dem'],
        det(masculine, singular, accusative) >> ['den'],
        det(masculine, plural, nominative) >> ['die'],
        det(masculine, plural, genitive) >> ['der'],
        det(masculine, plural, dative) >> ['den'],
        det(masculine, plural, accusative) >> ['die'],
        det(feminine, singular, nominative) >> ['die'],
        det(feminine, singular, genitive) >> ['der'],
        det(feminine, singular, dative) >> ['der'],
        det(feminine, singular, accusative) >> ['die'],
        det(feminine, plural, nominative) >> ['die'],
        det(feminine, plural, genitive) >> ['der'],
        det(feminine, plural, dative) >> ['den'],
        det(feminine, plural, accusative) >> ['die'],
        det(neuter, singular, nominative) >> ['das'],
        det(neuter, singular, genitive) >> ['des'],
        det(neuter, singular, dative) >> ['dem'],
        det(neuter, singular, accusative) >> ['das'],
        det(neuter, plural, nominative) >> ['die'],
        det(neuter, plural, genitive) >> ['der'],
        det(neuter, plural, dative) >> ['den'],
        det(neuter, plural, accusative) >> ['die'],

        det(masculine, singular, nominative) >> ['ein'],
        det(masculine, singular, genitive) >> ['eines'],
        det(masculine, singular, dative) >> ['einem'],
        det(masculine, singular, accusative) >> ['einen'],
        det(feminine, singular, nominative) >> ['eine'],
        det(feminine, singular, genitive) >> ['einer'],
        det(feminine, singular, dative) >> ['einer'],
        det(feminine, singular, accusative) >> ['eine'],

        det(_, plural, nominative) >> ['einige'],
        det(_, plural, genitive) >> ['einiger'],
        det(_, plural, dative) >> ['einigen'],
        det(_, plural, accusative) >> ['einige'],

        det(_, plural, nominative) >> ['viele'],
        det(_, plural, genitive) >> ['vieler'],
        det(_, plural, dative) >> ['vielen'],
        det(_, plural, accusative) >> ['viele'],

        det(_, plural, nominative) >> ['alle'],
        det(_, plural, genitive) >> ['aller'],
        det(_, plural, dative) >> ['allen'],
        det(_, plural, accusative) >> ['alle'],

        det(masculine, singular, nominative) >> ['kein'],
        det(masculine, singular, genitive) >> ['keines'],
        det(masculine, singular, dative) >> ['keinem'],
        det(masculine, singular, accusative) >> ['keinen'],
        det(masculine, plural, nominative) >> ['keine'],
        det(masculine, plural, genitive) >> ['keiner'],
        det(masculine, plural, dative) >> ['keinen'],
        det(masculine, plural, accusative) >> ['keine'],
        det(feminine, singular, nominative) >> ['keine'],
        det(feminine, singular, genitive) >> ['keiner'],
        det(feminine, singular, dative) >> ['keiner'],
        det(feminine, singular, accusative) >> ['keine'],
        det(feminine, plural, nominative) >> ['keine'],
        det(feminine, plural, genitive) >> ['keiner'],
        det(feminine, plural, dative) >> ['keinen'],
        det(feminine, plural, accusative) >> ['keine'],

        det(masculine, singular, nominative) >> ['mancher'],
        det(masculine, singular, genitive) >> ['manches'],
        det(masculine, singular, dative) >> ['manchem'],
        det(masculine, singular, accusative) >> ['manchen'],
        det(masculine, plural, nominative) >> ['manche'],
        det(masculine, plural, genitive) >> ['mancher'],
        det(masculine, plural, dative) >> ['manchen'],
        det(masculine, plural, accusative) >> ['manchen'],
        det(feminine, singular, nominative) >> ['manche'],
        det(feminine, singular, genitive) >> ['mancher'],
        det(feminine, singular, dative) >> ['mancher'],
        det(feminine, singular, accusative) >> ['manche'],
        det(feminine, plural, nominative) >> ['manche'],
        det(feminine, plural, genitive) >> ['mancher'],
        det(feminine, plural, dative) >> ['manchen'],
        det(feminine, plural, accusative) >> ['manche'],

        det(masculine, singular, nominative) >> ['jeder'],
        det(masculine, singular, genitive) >> ['jedes'],
        det(masculine, singular, dative) >> ['jedem'],
        det(masculine, singular, accusative) >> ['jeden'],
        det(feminine, singular, nominative) >> ['jede'],
        det(feminine, singular, genitive) >> ['jeder'],
        det(feminine, singular, dative) >> ['jeder'],
        det(feminine, singular, accusative) >> ['jede'],


        noun(masculine, singular, nominative) >> ['hund'],
        noun(masculine, singular, genitive) >> ['hundes'],
        noun(masculine, singular, dative) >> ['hund'],
        noun(masculine, singular, accusative) >> ['hund'],
        noun(masculine, plural, nominative) >> ['hunde'],
        noun(masculine, plural, genitive) >> ['hunde'],
        noun(masculine, plural, dative) >> ['hunden'],
        noun(masculine, plural, accusative) >> ['hunde'],

        noun(feminine, singular, nominative) >> ['katze'],
        noun(feminine, singular, genitive) >> ['katze'],
        noun(feminine, singular, dative) >> ['katze'],
        noun(feminine, singular, accusative) >> ['katze'],
        noun(feminine, plural, nominative) >> ['katzen'],
        noun(feminine, plural, genitive) >> ['katzen'],
        noun(feminine, plural, dative) >> ['katzen'],
        noun(feminine, plural, accusative) >> ['katzen'],

        noun(masculine, singular, nominative) >> ['kater'],
        noun(masculine, singular, genitive) >> ['katers'],
        noun(masculine, singular, dative) >> ['kater'],
        noun(masculine, singular, accusative) >> ['kater'],
        noun(masculine, plural, nominative) >> ['kater'],
        noun(masculine, plural, genitive) >> ['kater'],
        noun(masculine, plural, dative) >> ['katern'],
        noun(masculine, plural, accusative) >> ['kater'],

        noun(feminine, singular, nominative) >> ['maus'],
        noun(feminine, singular, genitive) >> ['maus'],
        noun(feminine, singular, dative) >> ['maus'],
        noun(feminine, singular, accusative) >> ['maus'],
        noun(feminine, plural, nominative) >> ['mauese'],
        noun(feminine, plural, genitive) >> ['mauese'],
        noun(feminine, plural, dative) >> ['mauesen'],
        noun(feminine, plural, accusative) >> ['mauese'],


        verb(singular, nominative, Trans) >> ['fehlt'],
        verb(plural, nominative, Trans) >> ['fehlen'],

        verb(singular, dative, transitive) >> ['fehlt'],
        verb(plural, dative, transitive) >> ['fehlen'],

        verb(singular, _, intransitive) >> ['schlaeft'],
        verb(plural, _, intransitive) >> ['schlafen'],

        verb(singular, nominative, intransitive) >> ['frisst'],
        verb(plural, nominative, intransitive) >> ['fressen'],
        verb(singular, accusative, transitive) >> ['frisst'],
        verb(plural, accusative, transitive) >> ['fressen'],

        verb(singular, nominative, intransitive) >> ['jagt'],
        verb(plural, nominative, intransitive) >> ['jagen'],
        verb(singular, accusative, transitive) >> ['jagt'],
        verb(plural, accusative, transitive) >> ['jagen'],

        verb(singular, _, intransitive) >> ['spielt'],
        verb(plural, _, intransitive) >> ['spielen'],

    )

    #for subst in db.query(equal(A, [B, 'hunde', 'jagen', C, 'katzen']) & s(A)):
        #print(subst[A])
    #print()
    #for subst in db.query(s(A) & member('jagen', A)):
        #print(subst[A])
    for subst in db.query(equal(A, ['manche', 'mauese', 'jagen' | B]) & s(A)):
        print(subst[A])
    #for subst in db.query(equal(A, [D, 'kater', 'jagen' | B]) & s(A)):
        #print(subst[A])
    #for subst in db.query(equal(A, 'manche mauese jagen viele katzen'.split()) & s(A)):
        #print(subst[A])
    #for subst in db.query(equal(A, [B, C, 'jagen']) & s(A)):
        #print(subst[A])
    #for subst in db.query(equal(A, ['manche', B, C]) & s(A)):
        #print(subst[A])
    #print()
    #for subst in db.query(equal(A, [B, C, D, 'den', F]) & s(A)):
        #print(subst[A])
    #for subst in db.query(equal(A, [B, C, 'jagt', D, E]) & s(A)):
        #print(subst[A])
    #for i, subst in enumerate(db.query(s(A))):
        #pass
        #print(subst[A])
    #print(i)


def mudlang(db, has, use, using, take, sourcerer, dwarf, priest, knight, sword,
            chalice, axe, wand, Who, Weapon, Action, X):
    db.assertz(
        has(sourcerer, wand),
        has(dwarf, axe),
        has(priest, chalice),
        has(knight, sword),
        use(Who, using(Who, Weapon)) >>
            [use] & {has(Who, Weapon)} & take(Weapon),
        take(sword) >> [sword],
        take(axe) >> [axe],
        take(wand) >> [wand],
        take(chalice) >> [chalice],

    )
    # has(Who, Weapon) &
    for subst in db.query(use(Who, using(_, 'wand'), X, [])):
    #for subst in db.query(listing(use)):
        print(subst[Who])
        #pass


def grammar2(db, s, np, vp, det, noun, verb, masculine, feminine, neuter, adj,
             nominative, genitive, dative, accusative, plural, singular,
             intransitive, transitive, Gender, Number, Case, Trans, Rest,
             T, A, B, C, D, E, F, S, X, Y, Z, NP, VP, Det, Adj, Noun, Verb):

    db.assertz(

        s(S, T) << s(T, S, []),


        s(s(NP, VP)) >>
            np(NP, Number, nominative) &
            vp(VP, Number, nominative, intransitive),


        np(np(Det, Noun, [Gender, Number]), Number, Case) >>
            det(Det, Gender, Number, Case) &
            noun(Noun, Gender, Number, Case),

        np(np(Det, Adj, Noun, [Gender, Number]), Number, Case) >>
            det(Det, Gender, Number, Case) &
            adj(Adj, Gender, Number, Case) &
            noun(Noun, Gender, Number, Case),


        vp(vp(Verb, NP), Number, nominative, intransitive) >>
            verb(Verb, Number, nominative, intransitive) &
            np(NP, Number, nominative),


        det(det('der'), masculine, singular, nominative) >> ['der'],
        det(det('die'), feminine, singular, nominative) >> ['die'],
        det(det('das'), neuter, singular, nominative) >> ['das'],

        det(det('ein'), masculine, singular, nominative) >> ['ein'],
        det(det('eine'), feminine, singular, nominative) >> ['eine'],

        det(det('kein'), masculine, singular, nominative) >> ['kein'],
        det(det('keine'), feminine, singular, nominative) >> ['keine'],

        det(det('jeder'), masculine, singular, nominative) >> ['jeder'],
        det(det('jede'), feminine, singular, nominative) >> ['jede'],


        adj(adj('betretbarer'), masculine, singular, nominative) >>
            ['betretbarer'],


        noun(noun('raum'), masculine, singular, nominative) >>
            ['raum'] & {cut},


        verb(verb('ist'), singular, nominative, intransitive) >>
            ['ist'] & {cut},

    )


"""
    Die Kabine ist ein Raum. "Kabinen an Bord eines Raumschiffs..."
    Das Bad ist östlich von der Kabine. Die Beschreibung ist "Wie eine Kabine, ist auch das Bad..."
    Die Broschüre ist in der Kabine. "Sie beschreibt die Herrlichkeit..."
    Das Bett ist in der Kabine.
    Das Bett ist ein betretbarer Raum.
    Setze "Möbel" mit Bett gleich.
    Der Spiegel ist Kulisse im Bad.
    Die Dusche ist hier. Sie ist unbeweglich.
"""


def mudlang2(db, s, np, vp, noun, verb, feminine, singular, nominative, det,
             transitive, intransitive, Number, np_unknown, noun_unknown,
             Gender, Case, A, B, C, D, E, S, T, X, Y):

    from copy import deepcopy

    nouns = {}

    def test(term, env, db, trail):
        print('>>>', term)
        nouns[env.X.name] = deepcopy((
                                env.X,
                                env.Gender,
                                env.Number,
                                env.Case
                            ))

    db.consult(grammar2)

    db.assertz(

        noun(noun(X), Gender, Number, Case, [X|Y], Y)[test],

    )

    L = ['die', 'kabine', 'ist', 'ein', 'betretbarer', 'raum']
    #S = ['die', 'kabine', 'ist', 'ein', 'raum']
    for subst in db.query(equal(L, S) & s(S, T)):
        print(subst[S])
        print(subst[T])
    print(nouns)
    #for subst in db.query(equal(A, cut) & call(A)):
        #print(subst[A])
    #for subst in db.query(listing('test')):
        #pass


db = Database()
db.consult(grammar)
#db.consult(mudlang2)
