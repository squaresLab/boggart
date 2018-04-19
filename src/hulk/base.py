from enum import Enum
from typing import List, FrozenSet, Iterable, Any, Optional, Dict
import os


class Location(object):
    @staticmethod
    def from_string(s: str) -> 'Location':
        line, _, col = s.partition(':')
        print(line)
        print(col)
        return Location(int(line), int(col))

    def __init__(self, line: int, col: int):
        self.__line = line
        self.__col = col

    def __eq__(self, other: Any) -> bool:
        return  isinstance(other, Location) and \
                self.line == other.line and \
                self.col == other.col

    @property
    def line(self) -> int:
        return self.__line

    @property
    def column(self) -> int:
        return self.__col

    col = column

    def __str__(self) -> str:
        return "{}:{}".format(self.line, self.column)

    to_string = __str__


class LocationRange(object):
    """
    Captures a continuous range of source code locations.
    """
    @staticmethod
    def from_string(s: str) -> 'LocationRange':
        start_s, _, stop_s = s.partition("::")
        start = Location.from_string(start_s)
        stop = Location.from_string(stop_s)
        return LocationRange(start, stop)

    def __init__(self, start: Location, stop: Location):
        self.__start = start
        self.__stop = stop

    def __eq__(self, other: Any) -> bool:
        return  isinstance(other, LocationRange) and \
                self.start == other.start and \
                self.stop == other.stop

    @property
    def start(self) -> Location:
        """
        The location that marks the start of this range.
        """
        return self.__start

    @property
    def stop(self) -> Location:
        """
        The location that marks the end of this range (inclusive).
        """
        return self.__stop

    def __str__(self) -> str:
        return "{}::{}".format(self.start, self.stop)

    to_string = __str__


class Mutation(object):
    """
    Describes a concrete application of a given mutation operator at a specific
    location (range) in a source code file.
    """
    @staticmethod
    def from_dict(d: dict) -> 'Mutation':
        """
        Constructs a mutation from a dictionary-based description.
        """
        assert 'operator' in d
        assert 'transformation-index' in d
        assert 'location' in d
        assert 'arguments' in d

        operator = d['operator']
        transformation_index = d['transformation-index']
        arguments = d['arguments']
        location = LocationRange.from_string(d['location'])

        return Mutation(operator, transformation_index, location, arguments)

    def __init__(self,
                 operator: str,
                 transformation_index: int,
                 at: LocationRange,
                 args: Dict[str, str]
                 ) -> None:
        self.__operator = operator
        self.__transformation_index = transformation_index
        self.__at = at
        self.__args = dict(args)

    def __eq__(self, other: Any) -> bool:
        return  isinstance(other, Mutation) and \
                self.operator == other.operator and \
                self.transformation_index == other.transformation_index and \
                self.location == other.location and \
                self.arguments == other.arguments

    @property
    def operator(self) -> str:
        """
        The name of the operator.
        """
        return self.__operator

    @property
    def transformation_index(self) -> int:
        """
        The index of the transformation that should be applied.
        """
        return self.__transformation_index

    @property
    def location(self) -> LocationRange:
        """
        The location (range) at which to apply the operator.
        """
        return self.__at

    at = location

    @property
    def arguments(self) -> Dict[str, str]:
        """
        A dictionary of named arguments that are supplied to the operator for
        this mutation.
        """
        return self.__args.copy()

    def to_dict(self) -> dict:
        """
        Provides a dictionary-based description of this mutation, ready to be
        serialized.
        """
        return {
            'operator': self.operator,
            'transformation-index': self.transformation_index,
            'location': self.location.to_string(),
            'arguments': self.arguments
        }


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

    def __init__(self, match: str, rewrite: str):
        self.__match = match
        self.__rewrite = rewrite

    def __hash__(self) -> int:
        return hash((self.match, self.rewrite))

    def __eq__(self, other: Any) -> bool:
        return  isinstance(other, Transformation) and \
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
        return { 'match': self.__match,
                 'rewrite': self.__rewrite }


class Language(object):
    """
    Represents a programming language that is supported by Hulk.
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
        return  isinstance(other, Language) and \
                self.name == other.name and \
                list(self.file_endings) == list(other.file_endings)

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
