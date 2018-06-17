__all__ = ['Transformation']

from typing import Any, Dict, FrozenSet
import attr
import logging

from .constraint import Constraint

from rooibos import Match

logger = logging.getLogger(__name__)  # type: logging.Logger


@attr.s(frozen=True)
class Transformation(object):
    """
    Describes a source code transformation as a corresponding pair of Rooibos
    match and rewrite templates.
    """
    match = attr.ib(type=str)
    rewrite = attr.ib(type=str)
    constraints = attr.ib(type=FrozenSet[Constraint],
                          converter=frozenset)  # type: ignore

    @staticmethod
    def from_dict(d: dict) -> 'Transformation':
        assert 'match' in d
        assert 'rewrite' in d
        assert isinstance(d['match'], str)
        assert isinstance(d['rewrite'], str)

        match = d['match']
        rewrite = d['rewrite']
        constraints = \
            [Constraint.from_dict(c) for c in d.get('constraints', [])]

        return Transformation(match, rewrite, constraints)  # type: ignore

    def satisfies_constraints(self,
                              match: Match,
                              content_file: str,
                              offset_start: int,
                              offset_stop: int
                              ) -> bool:
        """
        Checks whether a given match satisfies the constraints of this
        transformation.
        """
        return all(c.is_satisfied_by(match,
                                     content_file,
                                     offset_start,
                                     offset_stop)
                   for c in self.constraints)

    def to_dict(self) -> dict:
        """
        Provides a dictionary--based description of this transformation, ready
        to be serialized.
        """
        return {'match': self.match,
                'rewrite': self.rewrite,
                'constraints': [c.to_dict() for c in self.constraints]}
