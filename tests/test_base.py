import pytest
from boggart.core import Language, \
                         Transformation, \
                         Operator, \
                         Location, \
                         LocationRange, \
                         FileLocationRange


def test_location_equality():
    a = Location(3, 10)
    b = Location(3, 10)
    c = Location(5, 10)

    assert a == b
    assert b == a
    assert a != c
    assert c != a


def test_location_range_equality():
    a = LocationRange.from_string("6:10::8:12")
    b = LocationRange.from_string("6:10::8:12")
    c = LocationRange.from_string("6:11::8:12")

    assert a == b
    assert b == a
    assert a != c
    assert c != a


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

    loc_s = "5:6::9:12"
    loc = LocationRange.from_string(loc_s)
    assert str(loc_s)


def test_file_location_range_to_and_from_string():
    loc = FileLocationRange("foo.c", Location(1, 1), Location(3, 10))
    loc_s = "foo.c@1:1::3:10"
    assert str(loc) == loc_s

    loc_from_s = FileLocationRange.from_string(loc_s)
    assert str(loc_from_s) == loc_s
    assert loc == loc_from_s


def test_transformation_serialisation():
    expected = Transformation(':x = :y', ':y = :x', [])
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
