from typing import Any

import attr

from bugzoo.core.fileline import FileLine

__all__ = ['Location', 'LocationRange', 'FileLocationRange', 'FileLine']


@attr.s(frozen=True)
class Location(object):
    @staticmethod
    def from_string(s: str) -> 'Location':
        line, _, col = s.partition(':')
        return Location(int(line), int(col))

    line = attr.ib(type=int)
    col = attr.ib(type=int)

    @property
    def column(self) -> int:
        return self.col

    def __str__(self) -> str:
        return "{}:{}".format(self.line, self.column)


@attr.s(frozen=True)
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


@attr.s(frozen=True)
class FileLocationRange(object):
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

    filename = attr.ib(type=str)
    start = attr.ib(type=Location)
    stop = attr.ib(type=Location)

    def __str__(self) -> str:
        return "{}@{}::{}".format(self.filename, self.start, self.stop)
