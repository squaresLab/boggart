from typing import Any

__all__ = ['Location', 'LocationRange']


class Location(object):
    @staticmethod
    def from_string(s: str) -> 'Location':
        line, _, col = s.partition(':')
        print(line)
        print(col)
        return Location(int(line), int(col))

    def __init__(self, line: int, col: int) -> None:
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

    def __init__(self, start: Location, stop: Location) -> None:
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
