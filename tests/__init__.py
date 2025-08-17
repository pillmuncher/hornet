# Copyright (c) 2014 Mick Krippendorf <m.krippendorf@freenet.de>

import pytest

from hornet.expressions import bind


def ast_eq(a, b):
    assert repr(a) == repr(b)


def ast_neq(a, b):
    assert repr(a) != repr(b)


def expression_all(test, mf_result, mf_expected, *term_pairs):
    for term, expected in term_pairs:
        result = bind(term, mf_result)
        expected = bind(expected, mf_expected)
        try:
            test(result, expected)
        except BaseException:
            print(term)
            print(result)
            print(expected)
            print()
            raise


def expression_all_raise(error, test, *invalid):
    for each in invalid:
        try:
            with pytest.raises(error):
                bind(each, test)
        except BaseException:
            print(each)
            raise
