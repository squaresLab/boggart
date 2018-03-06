import pytest
from hulk.base import Language, \
                      Transformation, \
                      Operator, \
                      Location, \
                      LocationRange


def test_location_equality():
    a = Location(3, 10)
    b = Location(3, 10)
    c = Location(5, 10)

    assert a == b
    assert b == a
    assert a != c
    assert a != None


def test_location_from_string():
    expected = Location(0, 10)
    actual = Location.from_string("0:10")

    assert actual == expected


def test_transformation_serialisation():
    expected = Transformation(':x = :y', ':y = :x')
    actual = Transformation.from_dict(expected.to_dict())
    assert expected == actual


def test_language_serialisation():
    expected = Language("c", [".c"])
    actual = Language.from_dict(expected.to_dict())
    assert actual == expected


def test_language_equality():
    a = Language("java", [".java"])
    b = Language("java", [".java"])
    c = Language("java", [".foo"])
    d = Language("notjava", [".java"])

    assert a == b
    assert b == a
    assert a != c
    assert a != d
