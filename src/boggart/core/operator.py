from typing import Dict, Any, List, FrozenSet, Iterator

from .transformation import Transformation
from .language import Language

__all__ = ['Operator']


class Operator(object):
    """
    Used to describe a mutation operator. Each mutation operator has its own
    own unique name that is used by external interfaces (i.e., the server) to
    lookup particular operators.
    """
    @staticmethod
    def from_dict(d: dict) -> 'Operator':
        assert 'name' in d
        assert 'languages' in d
        assert 'transformations' in d
        assert isinstance(d['name'], str)
        assert isinstance(d['languages'], list)
        assert isinstance(d['transformations'], list)
        assert all(isinstance(e, str) for e in d['languages'])
        assert all(isinstance(e, dict) for e in d['transformations'])

        name = d['name']
        languages = d['languages']
        transformations = \
            [Transformation.from_dict(t) for t in d['transformations']]

        return Operator(name, languages, transformations)

    def __init__(self,
                 name: str,
                 languages: List[str],
                 transformations: List[Transformation]
                 ) -> None:
        assert name != '', \
            "operator must have a non-empty name"
        assert languages != [], \
            "operator must support at least one language"
        assert transformations != [], \
            "operators must implement at least one transformation."

        self.__name = name
        self.__languages = frozenset(languages)
        self.__transformations = transformations.copy()

    @property
    def name(self) -> str:
        """
        The name of this mutation operator.
        """
        return self.__name

    @property
    def languages(self) -> Iterator[str]:
        """
        Returns an iterator over the names of the languages that are supported
        by this mutation operator.
        """
        return self.__languages.__iter__()

    @property
    def transformations(self) -> List[Transformation]:
        """
        The transformations performed by this mutation operator.
        """
        return self.__transformations.copy()

    def supports_language(self, language: Language) -> bool:
        """
        Determines whether this operator supports a given language.

        Returns:
            True if this operator supports the given language, else False.
        """
        return language.name in self.__languages

    def to_dict(self) -> Dict[str, Any]:
        """
        Provides a dictionary-based description of this transformation, ready
        to be serialized.
        """
        return {
            'name': self.name,
            'languages': list(self.languages),
            'transformations': [t.to_dict() for t in self.transformations]
        }
