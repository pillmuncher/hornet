#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

__version__ = '0.2.3a'
__date__ = '2014-09-27'
__author__ = 'Mick Krippendorf <m.krippendorf@freenet.de>'
__license__ = 'MIT'


import pprint

from hornet import *

from hornet.symbols import (
    A, Adj, B, C, Case, D, Det, E, F, Gender, L, NP, Noun, Number, Rest, S, T,
    Trans, VP, Verb, W, X, Y, Z, accusative, adj, dative, det, feminine,
    genitive, intransitive, masculine, neuter, nominative, noun, noun_unknown,
    np, np_unknown, plural, s, singular, transitive, verb, vp,
)



def grammar(db):

    db.tell(

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
        noun(feminine, plural, nominative) >> ['maeuse'],
        noun(feminine, plural, genitive) >> ['maeuse'],
        noun(feminine, plural, dative) >> ['maeusen'],
        noun(feminine, plural, accusative) >> ['maeuse'],

        noun(neuter, plural, nominative) >> ['leute'],
        noun(neuter, plural, genitive) >> ['leute'],
        noun(neuter, plural, dative) >> ['leuten'],
        noun(neuter, plural, accusative) >> ['leute'],

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

    #for subst in db.ask(s(A) & member('jagen', A)):

    #words = [B, 'hunde', 'jagen', C, 'katzen']
    #words = ['manche', 'maeuse', 'jagen' | B]
    #words = [D, 'kater', 'jagen' | B]
    #words = 'manche maeuse jagen viele katzen'.split()
    #words = 'eine maus jagt viele katzen'.split()
    #words = [B, C, 'jagen']
    #words = ['manche', B, C]
    words = [B, C, D, 'die', F]
    #words = [B, 'hund', D, E, F]
    #words = [B, C, 'jagt', D, E]
    #words = [A, 'jagen' | E]

    #for i, subst in enumerate(db.ask(s(W) & join(W, S, ' '))):
    for subst in db.ask(equal(words, W) & s(W) & join(W, S, ' ')):
        print(subst[S]())
        #print('Yes.')
    #else:
        #print('No.')

        #print(repr(subst[S]))
    #print(i)


def grammar2(db):

    db.tell(

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


        #noun(noun('raum'), masculine, singular, nominative) >>
            #['raum'] & {cut},


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


def mudlang2(db):

    nouns = {}

    def test(term, env, db, trail):
        nouns[env.X.name] = dict(
            gender=str(env.Gender),
            number=str(env.Number),
            case=str(env.Case),
        )


    grammar2(db)

    db.tell(

        #noun(noun(X), Gender, Number, Case, [X|Y], Y)
        noun(noun(X), Gender, Number, Case, [X|Y], Y)[test],

    )

    L = 'die kabine ist ein betretbarer raum'.split()
    for subst in db.ask(equal(L, S) & s(S, T)):
        print(subst[S])
        print(subst[T])
    pprint.pprint(nouns)

db = Database()
grammar(db)
mudlang2(db)
