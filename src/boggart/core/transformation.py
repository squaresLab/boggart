from typing import Any, Dict

__all__ = ['Transformation']


class Transformation(object):
    """
    Describes a source code transformation as a corresponding pair of Rooibos
    match and rewrite templates.
    """
    @staticmethod
    def from_dict(d: dict) -> 'Transformation':
        assert 'match' in d
        assert 'rewrite' in d
        assert isinstance(d['match'], str)
        assert isinstance(d['rewrite'], str)

        match = d['match']
        rewrite = d['rewrite']

        return Transformation(match, rewrite)

    def __init__(self, match: str, rewrite: str) -> None:
        self.__match = match
        self.__rewrite = rewrite

    def __repr__(self) -> str:
        return "Transformation({}, {})".format(self.match, self.rewrite)

    def __hash__(self) -> int:
        return hash((self.match, self.rewrite))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Transformation) and \
               self.match == other.match and \
               self.rewrite == other.rewrite

    @property
    def match(self) -> str:
        return self.__match

    @property
    def rewrite(self) -> str:
        return self.__rewrite

    def to_dict(self) -> dict:
        """
        Provides a dictionary--based description of this transformation, ready
        to be serialized.
        """
        return {'match': self.__match,
                'rewrite': self.__rewrite}
