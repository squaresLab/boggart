import pytest
from hulk.base import Language


def test_serialisation():
    expected = Language("c", [".c"])
    actual = Language.from_dict(expected.to_dict())
    assert actual == expected
