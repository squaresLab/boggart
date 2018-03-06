import pytest
from hulk.base import Language, Transformation, Operator


def test_transformation_serialisation():
    expected = Transformation(':x = :y', ':y = :x')
    actual = Transformation.from_dict(expected.to_dict())
    assert expected == actual


def test_language_serialisation():
    expected = Language("c", [".c"])
    actual = Language.from_dict(expected.to_dict())
    assert actual == expected


def test_language_equivalence():
    a = Language("java", [".java"])
    b = Language("java", [".java"])
    c = Language("java", [".foo"])
    d = Language("notjava", [".java"])

    assert a == b
    assert b == a
    assert a != c
    assert a != d
