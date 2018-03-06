import pytest
from hulk.base import Language


def test_serialisation():
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
