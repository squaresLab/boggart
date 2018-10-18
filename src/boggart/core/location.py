from typing import Any, List, Dict, Iterable, Iterator

import attr

from bugzoo.core.fileline import FileLine, FileLineSet

__all__ = ['Location', 'LocationRange', 'FileLocationRange', 'FileLine',
           'FileLocationRangeSet', 'FileLineSet']


@attr.s(frozen=True, repr=False)
class Location(object):
    """
    Represents a character location within an arbitrary file.
    """
    @staticmethod
    def from_string(s: str) -> 'Location':
        line, _, col = s.partition(':')
        return Location(int(line), int(col))

    line = attr.ib(type=int)
    col = attr.ib(type=int)

    @property
    def column(self) -> int:
        return self.col

    def __le__(self, other: 'Location') -> bool:
        if self.line == other.line:
            return self.col < other.col
        return self.line < other.line

    def __str__(self) -> str:
        return "{}:{}".format(self.line, self.column)

    def __repr__(self) -> str:
        return "Location({})".format(str(self))


@attr.s(frozen=True, repr=False)
class FileLocation(object):
    """
    Represents a character location within a named file.
    """
    filename = attr.ib(type=str)
    location = attr.ib(type=Location)

    @property
    def col(self) -> int:
        return self.location.col

    @property
    def line(self) -> int:
        return self.location.line

    @staticmethod
    def from_string(s: str) -> 'FileLocation':
        filename, _, loc_s = s.rpartition('@')
        location = Location.from_string(loc_s)
        return FileLocation(filename, location)

    def __str__(self) -> str:
        return "{}@{}".format(self.filename, self.location)

    def __repr__(self) -> str:
        return "FileLocation({})".format(str(self))


@attr.s(frozen=True, repr=False)
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

    start = attr.ib(type=Location)
    stop = attr.ib(type=Location)

    def __str__(self) -> str:
        return "{}::{}".format(self.start, self.stop)

    def __repr__(self) -> str:
        return "LocationRange({})".format(str(self))

    def __contains__(self, loc: Location) -> bool:
        """
        Determines whether a given location is contained within this range.
        """
        left = loc.line > self.start.line \
            or (loc.line == self.start.line and loc.col >= self.start.col)
        right = loc.line < self.stop.line \
            or (loc.line == self.stop.line and loc.col < self.stop.col)
        return left and right


@attr.s(frozen=True, repr=False)
class FileLocationRange(object):
    """
    Represents a contiguous sequence of characters in a particular file.
    """
    @staticmethod
    def from_string(s: str) -> 'FileLocationRange':
        filename, _, s_range = s.rpartition('@')
        location_range = LocationRange.from_string(s_range)
        return FileLocationRange(filename, location_range)

    filename = attr.ib(type=str)
    location_range = attr.ib(type=LocationRange)

    @property
    def start(self) -> Location:
        return self.location_range.start

    @property
    def stop(self) -> Location:
        return self.location_range.stop

    def __str__(self) -> str:
        return "{}@{}".format(self.filename, self.location_range)

    def __repr__(self) -> str:
        return "FileLocationRange({})".format(str(self))

    def __contains__(self, floc: FileLocation) -> bool:
        """
        Determines whether a given location is contained within this range.
        """
        in_file = floc.filename == self.filename
        in_range = floc.location in self.location_range
        return in_file and in_range


class FileLocationRangeSet(object):
    def __init__(self, ranges: Iterable[FileLocationRange]) -> None:
        """
        Represents a set of file location ranges.
        """
        self.__fn_to_ranges = {}  # type: Dict[str, List[FileLocationRange]]
        for r in ranges:
            if r.filename not in self.__fn_to_ranges:
                self.__fn_to_ranges[r.filename] = []
            self.__fn_to_ranges[r.filename].append(r)

    def __iter__(self) -> Iterator[FileLocationRange]:
        for f_ranges in self.__fn_to_ranges.values():
            yield from f_ranges

    def __repr__(self) -> str:
        return "FileLocationRangeSet({})".format(self.__fn_to_ranges)

    def __contains__(self, location: FileLocation) -> bool:
        """
        Determines whether a given file location is contained in one of the
        ranges within this set.
        """
        ranges = self.__fn_to_ranges.get(location.filename, [])
        return any(location in r for r in ranges)
