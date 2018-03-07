import pytest
from hulk.base import Mutation, \
                      Location, \
                      LocationRange


def test_to_and_from_dict():
    location = LocationRange(Location(1, 5),
                             Location(2, 30))
    mutation = Mutation('foo', location, {'x': '120'})

    expected = {
        'operator': 'foo',
        'location': '1:5::2:30',
        'arguments': {'x': '120'}
    }

    assert mutation.to_dict() == expected

    actual = Mutation.from_dict(mutation.to_dict())
    assert actual == mutation
