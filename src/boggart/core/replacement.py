__all__ = ['Replacement']

from typing import Dict

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
