from resolver import Database
from system import *


def grammar(db, s, np, vp, det, noun, verb, masculine, feminine, neuter,
           nominative, genitive, dative, accusative, plural, singular,
           intransitive, transitive, Gender, Number, Case, Trans,
           Rest, A, B, C, D, E, F, S):

    db.assertz(

        s(S) << s(S, []),


        s >>
            np(Gender, Number, nominative) &
            vp(Number, nominative, intransitive),

        s >>
            np(Gender, Number, Case) &
            vp(Number, Case, transitive),


        np(Gender, plural, Case) >>
            noun(Gender, plural, Case),

        np(Gender, Number, Case) >>
            det(Gender, Number, Case) &
            noun(Gender, Number, Case),


        vp(Number, nominative, intransitive) >>
            verb(Number, nominative, intransitive),

        vp(Number, accusative, intransitive) >>
            verb(Number, accusative, intransitive),

        vp(_, _, dative, transitive) >>
            verb(Number, nominative, transitive) &
            np(Gender, Number, nominative),

        vp(Number, nominative, transitive) >>
            verb(Number, nominative, transitive) &
            np(_, _, dative),

        vp(Number, nominative, transitive) >>
            verb(Number, accusative, transitive) &
            np(_, _, accusative),


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

    #for subst in db |- equal(A, [B, 'hunde', 'jagen', C, 'katzen']) & s(A):
        #print(subst[A])
    #print()
    for subst in db |- equal(A, ['manche', B, C]) & s(A):
        print(subst[A])
    #print()
    #for subst in db |- equal(A, [B, C, D, 'den', F]) & s(A):
        #print(subst[A])
    #for subst in db |- equal(A, [B, C, 'jagt', D, E]) & s(A):
        #print(subst[A])
    #for i, subst in enumerate(db |- s(A)):
        #pass
        #print(subst[A])
    #print(i)


db = Database()
db.consult(grammar)
