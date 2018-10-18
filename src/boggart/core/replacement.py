__all__ = ['Replacement']

from typing import Dict, List, Sequence
import functools

from .location import FileLocationRange


# FIXME: use attrs
class Replacement(object):
    """
    Describes the replacement of a contiguous body of text in a single source
    code file with a provided text.
    """
    @staticmethod
    def from_dict(d: Dict[str, str]) -> 'Replacement':
        location = FileLocationRange.from_string(d['location'])
        return Replacement(location, d['text'])

    @staticmethod
    def resolve(replacements: Sequence['Replacement']
                ) -> List['Replacement']:
        """
        Resolves all conflicts in a sequence of replacements.
        """
        # group by file
        file_to_reps = {}  # type: Dict[str, List[Replacement]]
        for rep in replacements:
            if rep.filename not in file_to_reps:
                file_to_reps[rep.filename] = []
            file_to_reps[rep.filename].append(rep)

        # resolve redundant replacements
        for fn in file_to_reps:
            reps = file_to_reps[fn]

            def cmp(x, y) -> int:
                return -1 if x < y else 0 if x == y else 0

            def compare(x, y) -> int:
                start_x, stop_x = x.location.start, x.location.stop
                start_y, stop_y = y.location.start, y.location.stop
                if start_x != start_y:
                    return cmp(start_x, start_y)
                # start_x == start_y
                return -cmp(stop_x, stop_y)

            reps.sort(key=functools.cmp_to_key(compare))

            filtered = [reps[0]]  # type: List[Replacement]
            i, j = 0, 1
            while j < len(reps):
                x, y = reps[i], reps[j]
                if x.location.stop > y.location.start:
                    j += 1
                else:
                    i += 1
                    j += 1
                    filtered.append(y)
            filtered.reverse()
            file_to_reps[fn] = filtered

        # collapse into a flat sequence of transformations
        resolved = []  # type: List[Replacement]
        for reps in file_to_reps.values():
            resolved += reps
        return resolved

    def __init__(self,
                 location: FileLocationRange,
                 text: str
                 ) -> None:
        self.__location = location
        self.__text = text

    def __repr__(self) -> str:
        return "Replacement({}, {})".format(repr(self.location),
                                            self.text)

    @property
    def filename(self) -> str:
        """
        The name of the file in which the replacement should be made.
        """
        return self.__location.filename

    @property
    def location(self) -> FileLocationRange:
        """
        The contiguous range of text that should be replaced.
        """
        return self.__location

    @property
    def text(self) -> str:
        """
        The source text that should be used as a replacement.
        """
        return self.__text

    def to_dict(self) -> Dict[str, str]:
        return {'location': str(self.location),
                'text': self.text}
