from typing import Any

__all__ = ['Location', 'LocationRange', 'FileLocationRange']


class Location(object):
    @staticmethod
    def from_string(s: str) -> 'Location':
        line, _, col = s.partition(':')
        return Location(int(line), int(col))

    def __init__(self, line: int, col: int) -> None:
        self.__line = line
        self.__col = col

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Location) and \
               self.line == other.line and \
               self.col == other.col

    @property
    def line(self) -> int:
        return self.__line

    @property
    def column(self) -> int:
        return self.__col

    @property
    def col(self) -> int:
        return self.__col

    def __str__(self) -> str:
        return "{}:{}".format(self.line, self.column)

    def __repr__(self) -> str:
        return "Location({})".format(str(self))


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

    def __init__(self, start: Location, stop: Location) -> None:
        self.__start = start
        self.__stop = stop

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, LocationRange) and \
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

    def __repr__(self) -> str:
        return "LocationRange({})".format(str(self))

    to_string = __str__


class FileLocationRange(LocationRange):
    """
    Represents a contiguous sequence of characters in a particular file.
    """
    @staticmethod
    def from_string(s: str) -> 'FileLocationRange':
        filename, _, s_range = s.rpartition('@')
        start_s, _, stop_s = s_range.partition('::')
        start = Location.from_string(start_s)
        stop = Location.from_string(stop_s)
        return FileLocationRange(filename, start, stop)

    def __init__(self, filename: str, start: Location, stop: Location) -> None:
        super().__init__(start, stop)
        self.__filename = filename

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, FileLocationRange) and \
               self.filename == other.filename and \
               super().__eq__(other)

    def __str__(self) -> str:
        str_range = super().__str__()
        return "{}@{}".format(self.filename, str_range)

    def __repr__(self) -> str:
        return "FileLocationRange({})".format(str(self))

    to_string = __str__

    @property
    def filename(self) -> str:
        """
        The name of the file to which the character range belongs.
        """
        return self.__filename
