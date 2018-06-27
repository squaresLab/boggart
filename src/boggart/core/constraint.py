__all__ = ['Constraint', 'IsSingleTerm', 'PrecededBy']

from typing import Any, Dict, FrozenSet
import attr
import logging

from rooibos import Match
from bugzoo import Bug as Snapshot

logger = logging.getLogger(__name__)  # type: logging.Logger


@attr.s(frozen=True)
class Constraint(object):
    @staticmethod
    def from_dict(d: dict) -> 'Constraint':
        if d['type'] == 'is-single-term':
            return IsSingleTerm.from_dict(d)
        if d['type'] == 'preceded-by':
            return PrecededBy.from_dict(d)
        raise SyntaxError("unrecognized constraint")

    def is_satisfied_by(self,
                        match: Match,
                        content_file: str,
                        offset_start: int,
                        offset_stop: int
                        ) -> bool:
        """
        Checks whether a given match satisfies this constraint.
        """
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


@attr.s(frozen=True)
class IsSingleTerm(Constraint):
    @staticmethod
    def from_dict(d: dict) -> 'IsSingleTerm':
        assert 'hole' in d
        hole = str(d['hole'])
        return IsSingleTerm(hole)

    hole = attr.ib(type=str)

    def is_satisfied_by(self,
                        match: Match,
                        content_file: str,
                        offset_start: int,
                        offset_stop: int
                        ) -> bool:
        # NOTE bug in rooibos causes empty terms to be omitted
        if self.hole not in match.environment:
            return False

        content = match.environment[self.hole].fragment.strip()
        return not any(c.isspace() for c in content)

    def to_dict(self) -> Dict[str, Any]:
        return {'type': 'is-single-term',
                'hole': self.hole}


@attr.s(frozen=True)
class PrecededBy(Constraint):
    @staticmethod
    def from_dict(d: dict) -> 'PrecededBy':
        assert 'any-of' in d
        assert isinstance(d['any-of'], list)
        assert d['any-of'] != []
        assert all(isinstance(k, str) for k in d['any-of'])
        return PrecededBy(d['any-of'])

    options = attr.ib(type=FrozenSet[str],
                      converter=frozenset)  # type: ignore

    def is_satisfied_by(self,
                        match: Match,
                        content_file: str,
                        offset_start: int,
                        offset_stop: int
                        ) -> bool:
        preceded_by = content_file[:offset_start].rstrip()
        return any(preceded_by.endswith(opt) for opt in self.options)

    def to_dict(self) -> Dict[str, Any]:
        return {'type': 'preceded-by',
                'any-of': list(self.options)}
