# Copyright (c) 2014-2025 Mick Krippendorf <m.krippendorf+hornet@posteo.de>
# SPDX-License-Identifier: MIT

from hornet import DCG, database
from hornet.symbols import (
    C,
    Case,
    D,
    F,
    Gender,
    Number,
    S,
    Trans,
    W,
    _,
    accusative,
    dative,
    det,
    equal,
    feminine,
    genitive,
    intransitive,
    masculine,
    neuter,
    nominative,
    noun,
    np,
    plural,
    s,
    singular,
    transitive,
    verb,
    vp,
)


def grammar(db):
    db.tell(
        s(S).when(s(S, [])),
        DCG(
            s.when(
                np(
                    Number,
                    nominative,
                ),
                vp(Number, nominative, intransitive),
            )
        ),
        DCG(
            s.when(
                np(
                    Number,
                    Case,
                ),
                vp(Number, Case, transitive),
            )
        ),
        DCG(
            np(plural, Case).when(
                noun(_, plural, Case),
            )
        ),
        DCG(
            np(Number, Case).when(
                det(
                    Gender,
                    Number,
                    Case,
                ),
                noun(Gender, Number, Case),
            )
        ),
        DCG(
            vp(Number, nominative, intransitive).when(
                verb(Number, nominative, intransitive),
            )
        ),
        DCG(
            vp(Number, accusative, intransitive).when(
                verb(Number, accusative, intransitive),
            )
        ),
        DCG(
            vp(_, dative, transitive).when(
                verb(
                    Number,
                    nominative,
                    transitive,
                ),
                np(Number, nominative),
            )
        ),
        DCG(
            vp(Number, nominative, transitive).when(
                verb(
                    Number,
                    nominative,
                    transitive,
                ),
                np(_, dative),
            )
        ),
        DCG(
            vp(Number, nominative, transitive).when(
                verb(
                    Number,
                    accusative,
                    transitive,
                ),
                np(_, accusative),
            )
        ),
        DCG(det(masculine, singular, nominative).when(["der"])),
        DCG(det(masculine, singular, genitive).when(["des"])),
        DCG(det(masculine, singular, dative).when(["dem"])),
        DCG(det(masculine, singular, accusative).when(["den"])),
        DCG(det(masculine, plural, nominative).when(["die"])),
        DCG(det(masculine, plural, genitive).when(["der"])),
        DCG(det(masculine, plural, dative).when(["den"])),
        DCG(det(masculine, plural, accusative).when(["die"])),
        DCG(det(feminine, singular, nominative).when(["die"])),
        DCG(det(feminine, singular, genitive).when(["der"])),
        DCG(det(feminine, singular, dative).when(["der"])),
        DCG(det(feminine, singular, accusative).when(["die"])),
        DCG(det(feminine, plural, nominative).when(["die"])),
        DCG(det(feminine, plural, genitive).when(["der"])),
        DCG(det(feminine, plural, dative).when(["den"])),
        DCG(det(feminine, plural, accusative).when(["die"])),
        DCG(det(neuter, singular, nominative).when(["das"])),
        DCG(det(neuter, singular, genitive).when(["des"])),
        DCG(det(neuter, singular, dative).when(["dem"])),
        DCG(det(neuter, singular, accusative).when(["das"])),
        DCG(det(neuter, plural, nominative).when(["die"])),
        DCG(det(neuter, plural, genitive).when(["der"])),
        DCG(det(neuter, plural, dative).when(["den"])),
        DCG(det(neuter, plural, accusative).when(["die"])),
        DCG(det(masculine, singular, nominative).when(["ein"])),
        DCG(det(masculine, singular, genitive).when(["eines"])),
        DCG(det(masculine, singular, dative).when(["einem"])),
        DCG(det(masculine, singular, accusative).when(["einen"])),
        DCG(det(feminine, singular, nominative).when(["eine"])),
        DCG(det(feminine, singular, genitive).when(["einer"])),
        DCG(det(feminine, singular, dative).when(["einer"])),
        DCG(det(feminine, singular, accusative).when(["eine"])),
        DCG(det(_, plural, nominative).when(["einige"])),
        DCG(det(_, plural, genitive).when(["einiger"])),
        DCG(det(_, plural, dative).when(["einigen"])),
        DCG(det(_, plural, accusative).when(["einige"])),
        DCG(det(_, plural, nominative).when(["viele"])),
        DCG(det(_, plural, genitive).when(["vieler"])),
        DCG(det(_, plural, dative).when(["vielen"])),
        DCG(det(_, plural, accusative).when(["viele"])),
        DCG(det(_, plural, nominative).when(["alle"])),
        DCG(det(_, plural, genitive).when(["aller"])),
        DCG(det(_, plural, dative).when(["allen"])),
        DCG(det(_, plural, accusative).when(["alle"])),
        DCG(det(masculine, singular, nominative).when(["kein"])),
        DCG(det(masculine, singular, genitive).when(["keines"])),
        DCG(det(masculine, singular, dative).when(["keinem"])),
        DCG(det(masculine, singular, accusative).when(["keinen"])),
        DCG(det(masculine, plural, nominative).when(["keine"])),
        DCG(det(masculine, plural, genitive).when(["keiner"])),
        DCG(det(masculine, plural, dative).when(["keinen"])),
        DCG(det(masculine, plural, accusative).when(["keine"])),
        DCG(det(feminine, singular, nominative).when(["keine"])),
        DCG(det(feminine, singular, genitive).when(["keiner"])),
        DCG(det(feminine, singular, dative).when(["keiner"])),
        DCG(det(feminine, singular, accusative).when(["keine"])),
        DCG(det(feminine, plural, nominative).when(["keine"])),
        DCG(det(feminine, plural, genitive).when(["keiner"])),
        DCG(det(feminine, plural, dative).when(["keinen"])),
        DCG(det(feminine, plural, accusative).when(["keine"])),
        DCG(det(masculine, singular, nominative).when(["mancher"])),
        DCG(det(masculine, singular, genitive).when(["manches"])),
        DCG(det(masculine, singular, dative).when(["manchem"])),
        DCG(det(masculine, singular, accusative).when(["manchen"])),
        DCG(det(masculine, plural, nominative).when(["manche"])),
        DCG(det(masculine, plural, genitive).when(["mancher"])),
        DCG(det(masculine, plural, dative).when(["manchen"])),
        DCG(det(masculine, plural, accusative).when(["manchen"])),
        DCG(det(feminine, singular, nominative).when(["manche"])),
        DCG(det(feminine, singular, genitive).when(["mancher"])),
        DCG(det(feminine, singular, dative).when(["mancher"])),
        DCG(det(feminine, singular, accusative).when(["manche"])),
        DCG(det(feminine, plural, nominative).when(["manche"])),
        DCG(det(feminine, plural, genitive).when(["mancher"])),
        DCG(det(feminine, plural, dative).when(["manchen"])),
        DCG(det(feminine, plural, accusative).when(["manche"])),
        DCG(det(masculine, singular, nominative).when(["jeder"])),
        DCG(det(masculine, singular, genitive).when(["jedes"])),
        DCG(det(masculine, singular, dative).when(["jedem"])),
        DCG(det(masculine, singular, accusative).when(["jeden"])),
        DCG(det(feminine, singular, nominative).when(["jede"])),
        DCG(det(feminine, singular, genitive).when(["jeder"])),
        DCG(det(feminine, singular, dative).when(["jeder"])),
        DCG(det(feminine, singular, accusative).when(["jede"])),
        DCG(noun(masculine, singular, nominative).when(["hund"])),
        DCG(noun(masculine, singular, genitive).when(["hundes"])),
        DCG(noun(masculine, singular, dative).when(["hund"])),
        DCG(noun(masculine, singular, accusative).when(["hund"])),
        DCG(noun(masculine, plural, nominative).when(["hunde"])),
        DCG(noun(masculine, plural, genitive).when(["hunde"])),
        DCG(noun(masculine, plural, dative).when(["hunden"])),
        DCG(noun(masculine, plural, accusative).when(["hunde"])),
        DCG(noun(feminine, singular, nominative).when(["katze"])),
        DCG(noun(feminine, singular, genitive).when(["katze"])),
        DCG(noun(feminine, singular, dative).when(["katze"])),
        DCG(noun(feminine, singular, accusative).when(["katze"])),
        DCG(noun(feminine, plural, nominative).when(["katzen"])),
        DCG(noun(feminine, plural, genitive).when(["katzen"])),
        DCG(noun(feminine, plural, dative).when(["katzen"])),
        DCG(noun(feminine, plural, accusative).when(["katzen"])),
        DCG(noun(masculine, singular, nominative).when(["kater"])),
        DCG(noun(masculine, singular, genitive).when(["katers"])),
        DCG(noun(masculine, singular, dative).when(["kater"])),
        DCG(noun(masculine, singular, accusative).when(["kater"])),
        DCG(noun(masculine, plural, nominative).when(["kater"])),
        DCG(noun(masculine, plural, genitive).when(["kater"])),
        DCG(noun(masculine, plural, dative).when(["katern"])),
        DCG(noun(masculine, plural, accusative).when(["kater"])),
        DCG(noun(feminine, singular, nominative).when(["maus"])),
        DCG(noun(feminine, singular, genitive).when(["maus"])),
        DCG(noun(feminine, singular, dative).when(["maus"])),
        DCG(noun(feminine, singular, accusative).when(["maus"])),
        DCG(noun(feminine, plural, nominative).when(["maeuse"])),
        DCG(noun(feminine, plural, genitive).when(["maeuse"])),
        DCG(noun(feminine, plural, dative).when(["maeusen"])),
        DCG(noun(feminine, plural, accusative).when(["maeuse"])),
        DCG(noun(neuter, plural, nominative).when(["leute"])),
        DCG(noun(neuter, plural, genitive).when(["leute"])),
        DCG(noun(neuter, plural, dative).when(["leuten"])),
        DCG(noun(neuter, plural, accusative).when(["leute"])),
        DCG(verb(singular, nominative, Trans).when(["fehlt"])),
        DCG(verb(plural, nominative, Trans).when(["fehlen"])),
        DCG(verb(singular, dative, transitive).when(["fehlt"])),
        DCG(verb(plural, dative, transitive).when(["fehlen"])),
        DCG(verb(singular, _, intransitive).when(["schlaeft"])),
        DCG(verb(plural, _, intransitive).when(["schlafen"])),
        DCG(verb(singular, nominative, intransitive).when(["frisst"])),
        DCG(verb(plural, nominative, intransitive).when(["fressen"])),
        DCG(verb(singular, accusative, transitive).when(["frisst"])),
        DCG(verb(plural, accusative, transitive).when(["fressen"])),
        DCG(verb(singular, nominative, intransitive).when(["jagt"])),
        DCG(verb(plural, nominative, intransitive).when(["jagen"])),
        DCG(verb(singular, accusative, transitive).when(["jagt"])),
        DCG(verb(plural, accusative, transitive).when(["jagen"])),
        DCG(verb(singular, _, intransitive).when(["spielt"])),
        DCG(verb(plural, _, intransitive).when(["spielen"])),
    )

    # words = "eine maus jagt viele katzen".split()
    # words = "manche maeuse jagen viele katze".split()
    words = ["der", C, D, "die", F]
    # words = ["manche", B, C]
    # words = [B, "hund", D, E, F]
    # words = [B, "hunde", "jagen", C, "katzen"]
    # words = [B, C, "jagen"]
    # words = [B, C, "jagt", D, E]

    print(f"finding senstences that match {list(str(w) for w in words)}:")
    print()
    for subst in db.ask(equal(words, W), s(W)):
        print(str(subst[W]))
    else:
        print("No.")

    # else:
    # print('No.')

    # print(repr(subst[S]))
    # print(i)


db = database()
grammar(db)
