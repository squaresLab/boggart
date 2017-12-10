import os
from enum import Enum
from typing import List, FrozenSet

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

    def to_dict(self) -> dict:
        """
        Provides a dictionary--based description of this transformation, ready
        to be serialized.
        """
        return { 'match': self.__match,
                 'rewrite': self.__rewrite }


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

    @staticmethod
    def with_name(name: str) -> 'Language':
        """
        Attempts to fetch the language registered with a given name.

        Raises:
            LanguageNotFound: if no language is registered with the given name.
        """
        try:
            return next(lang for lang in Language if lang.name == name)
        except StopIteration:
            raise LanguageNotFound(lang)

    @staticmethod
    def is_supported(language: str) -> bool:
        """
        Determines whether a language with a given name is supported by Hulk.

        Returns:
            True if a language with the given name is supported by Hulk, else
            False.
        """
        return any(l.name == language for l in Language)

    @staticmethod
    def autodetect(filename: str) -> 'Optional[Language]':
        """
        Attempts to automatically detect the language used by a file based
        on the file ending used by that file.

        Returns:
            The language associated with the file ending used by the given file,
            if one exists; if no language is associated with the file ending,
            or if the file has no suffix, `None` is returned instead.
        """
        (_, suffix) = os.path.splitext(filename)
        for lang in Language:
            if suffix in lang.file_endings:
                return lang
        return None # technically this is implicit

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


class Operator(object):
    """
    Used to describe a mutation operator. Each mutation operator has its own
    own unique name that is used by external interfaces (i.e., the server) to
    lookup particular operators.
    """
    def __init__(self,
                 name: str,
                 languages: List[str],
                 transformations: List[Transformation]) -> None:
        assert name != '', \
            "operator must have a non-empty name"
        assert languages != [], \
            "operator must support at least one language"
        assert transformations != [], \
            "operators must implement at least one transformation."

        self.__name = name
        self.__languages = frozenset(languages)
        self.__transformations = frozenset(transformations)

    @property
    def name(self) -> str:
        """
        The name of this mutation operator.
        """
        return self.__name

    @property
    def languages(self) -> FrozenSet[str]:
        """
        The names of the languages supported by this mutation operator.
        """
        return self.__languages.__iter__()

    @property
    def transformations(self) -> Iterable[Transformation]:
        """
        The transformations performed by this mutation operator.
        """
        return self.__transformations.__iter__()

    def supports_language(self, language: Language) -> bool:
        """
        Determines whether this operator supports a given language.

        Returns:
            True if this operator supports the given language, else False.
        """
        return language.name in self.__languages

    def to_dict(self) -> dict:
        """
        Provides a dictionary-based description of this transformation, ready
        to be serialized.
        """
        return {
            'name': self.name,
            'languages': [language for language in self.languages],
            'transformations': [t.to_dict() for t in self.transformations]
        }
