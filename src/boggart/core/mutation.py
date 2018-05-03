from typing import Dict, Any

from .location import FileLocationRange

__all__ = ['Mutation']


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
        location = FileLocationRange.from_string(d['location'])

        return Mutation(operator, transformation_index, location, arguments)

    def __init__(self,
                 operator: str,
                 transformation_index: int,
                 at: FileLocationRange,
                 args: Dict[str, str]
                 ) -> None:
        self.__operator = operator
        self.__transformation_index = transformation_index
        self.__at = at
        self.__args = dict(args)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Mutation) and \
               self.operator == other.operator and \
               self.transformation_index == other.transformation_index and \
               self.location == other.location and \
               self.arguments == other.arguments

    @property
    def operator(self) -> str:
        """
        The name of the mutation operator that was applied.
        """
        return self.__operator

    @property
    def transformation_index(self) -> int:
        """
        The index of the transformation that was applied.
        """
        return self.__transformation_index

    @property
    def location(self) -> FileLocationRange:
        """
        The character range at which the operator was applied.
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
