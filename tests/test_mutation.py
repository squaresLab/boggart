import pytest
from boggart.core import Mutation, \
                         Location, \
                         LocationRange


def test_eq():
    lx = LocationRange(Location(14, 0), Location(28, 10))
    ly = LocationRange(Location(30, 5), Location(31, 6))
    op = 'foo'
    args = {'x': 'bar'}

    m = Mutation(op, 0, lx, args)
    m_identical = Mutation(op, 0, lx, args)
    m_different_operator = Mutation('bar', 0, lx, args)
    m_different_location = Mutation(op, 0, ly, args)
    m_different_args = Mutation(op, 0, lx, {'y': 'hello'})

    assert m != None
    assert m == m_identical
    assert m != m_different_operator
    assert m != m_different_location
    assert m != m_different_args


def test_to_and_from_dict():
    location = LocationRange(Location(1, 5),
                             Location(2, 30))
    mutation = Mutation('foo', 0, location, {'x': '120'})

    expected = {
        'operator': 'foo',
        'transformation-index': 0,
        'location': '1:5::2:30',
        'arguments': {'x': '120'}
    }

    assert mutation.to_dict() == expected

    actual = Mutation.from_dict(mutation.to_dict())
    assert actual == mutation
