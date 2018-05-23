from typing import Iterable, List, Any

__all__ = ['Language']


class Language(object):
    """
    Represents a programming language that is supported by boggart.
    """
    @staticmethod
    def from_dict(d: dict) -> 'Language':
        assert 'name' in d
        assert 'file-endings' in d
        assert isinstance(d['name'], str)
        assert isinstance(d['file-endings'], list)
        assert all(isinstance(e, str) for e in d['file-endings'])

        name = d['name']
        file_endings = d['file-endings']
        return Language(name, file_endings)

    def __init__(self,
                 name: str,
                 file_endings: List[str]
                 ) -> None:
        self.__name = name
        self.__file_endings = frozenset(file_endings)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Language) and \
               self.name == other.name and \
               list(self.file_endings) == list(other.file_endings)

    def __repr__(self) -> str:
        return "Language({self.name})".format(self=self)

    @property
    def name(self) -> str:
        """
        The name of the language.
        """
        return self.__name

    @property
    def file_endings(self) -> Iterable[str]:
        """
        A list of known file endings used by this language. These are used to
        automatically detect the language used by a given file when language
        information is not explicitly provided.
        """
        return self.__file_endings.__iter__()

    def to_dict(self) -> dict:
        """
        Provides a dictionary-based description of this language, ready to be
        serialized.
        """
        return {
            'name': self.name,
            'file-endings': list(self.file_endings)
        }
