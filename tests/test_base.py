import pytest
from boggart.core import Language, \
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


def test_location_to_string():
    loc = Location(18, 10)
    assert str(loc) == '18:10'


def test_location_range_from_string():
    expected = LocationRange(Location(1, 5),
                             Location(1, 20))
    actual = LocationRange.from_string("1:5::1:20")

    assert actual == expected


def test_location_range_to_string():
    loc = LocationRange(Location(0, 20), Location(14, 0))
    assert str(loc) == '0:20::14:0'


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
