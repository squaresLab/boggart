from enum import Enum
from typing import List, Iter

class Transformation(object):
    """
    Describes a source code transformation as a corresponding pair of Rooibos
    match and rewrite templates.
    """
    def __init__(self, match: str, rewrite: str) -> None:
        self.__match = match
        self.__rewrite = rewrite

    @property
    def match(self) -> str:
        return self.__match

    @property
    def rewrite(self) -> str:
        return self.__rewrite


class Language(Enum):
    """
    Represents programming languages that are supported by Hulk.
    """
    C       = ("C",         ['.c'])
    CXX     = ("C++",       ['.cc', '.cxx', '.cpp'])
    PYTHON  = ("Python",    ['.py'])
    JAVA    = ("Java",      ['.java'])

    def __init__(self, name: str, file_endings: List[str]) -> None:
        self.__name = name
        self.__file_endings = frozenset(file_endings)

    @property
    def name(self) -> str:
        """
        The name of the language.
        """
        return self.__name

    @property
    def file_endings(self) -> Iter[str]:
        """
        A list of known file endings used by this language. These are used to
        automatically detect the language used by a given file when language
        information is not explicitly provided.
        """
        return self.__file_endings.__iter__()


class Operator(object):
    """
    Used to describe a mutation operator. Each mutation operator has its own
    own unique name that is used by external interfaces (i.e., the server) to
    lookup particular operators.
    """
    def __init__(self,
                 name: str,
                 languages: List[Language]) -> None:
        assert name != '', "operator must have a non-empty name"
        assert languages != [], "operator must support at least one language"

        self.__name = name
        self.__languages = frozenset(languages)

    @property
    def name(self) -> str:
        """
        The name of this mutation operator.
        """
        return self.__name

    @property
    def languages(self) -> Iter[Language]:
        """
        The languages supported by this mutation operator.
        """
        return self.__languages.__iter__()
