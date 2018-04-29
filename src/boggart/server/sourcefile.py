from typing import Dict, Tuple, List

from bugzoo.core.bug import Bug
from bugzoo.client import Client as BugZooClient

from ..core import FileLocationRange, Replacement
from ..exceptions import *

__all__ = ['SourceFileManager']


class SourceFileManager(object):
    def __init__(self, client_bugzoo: BugZooClient) -> None:
        self.__bugzoo = client_bugzoo
        self.__cache_file_contents = {} # type: Dict[Tuple[str, str], str]
        self.__cache_offsets = {} # type: Dict[Tuple[str, str], List[int]]

    def __line_offsets(self, snapshot: Bug, filepath: str) -> List[int]:
        """
        Returns a list specifying the offset for the first character on each
        line in a given file belonging to a BugZoo snapshot.
        """
        key_cache = (snapshot.name, filepath)
        if key_cache in self.__cache_offsets:
            return self.__cache_offsets[key_cache]

        # get the contents of the file
        contents = self.read_file(snapshot, filepath)

        # find all indices of newline characters
        offsets = [0]
        last_offset = 0
        while True:
            next_line_break = contents.find('\n', last_offset)
            if next_line_break == -1:
                break
            last_offset = next_line_break + 1
            offsets.append(last_offset)

        self.__cache_offsets[key_cache] = offsets
        return offsets

    def line_col_to_offset(self,
                           snapshot: Bug,
                           filepath: str,
                           line_num: int,
                           col_num: int) -> int:
        """
        Transforms a line-column number for a given file belonging to a
        BugZoo snapshot into a zero-indexed character offset.
        """
        line_offsets = self.__line_offsets(snapshot, filepath)
        line_starts_at = line_offsets[line_num - 1]
        offset = line_starts_at + col_num - 1
        return offset

    def read_file(self, snapshot: Bug, filepath: str) -> str:
        """
        Fetches the contents of a specified source code file belonging to a
        given BugZoo snapshot.

        Raises:
            FileNotFound: if the given file is not found inside the snapshot.
        """
        # TODO normalise file path

        bgz = self.__bugzoo
        key_cache = (snapshot.name, filepath)
        if key_cache in self.__cache_file_contents:
            return self.__cache_file_contents[key_cache]

        container = bgz.containers.provision(snapshot)
        try:
            contents = bgz.files.read(container, filepath)
        except KeyError:
            raise FileNotFound(filepath)
        finally:
            del bgz.containers[container.uid]

        self.__cache_file_contents[key_cache] = contents
        return contents

    def read_chars(self, snapshot: Bug, location: FileLocationRange) -> str:
        """
        Fetches a specified sequence of characters from a source code file
        belonging to a BugZoo snapshot.

        Raises:
            FileNotFound: if the given file is not found inside the snapshot.
        """
        filename = location.filename
        contents_file = self.read_file(snapshot, filename)

        start_at = self.line_col_to_offset(snapshot,
                                           filename,
                                           location.start.line,
                                           location.start.column)
        stop_at = self.line_col_to_offset(snapshot,
                                           filename,
                                           location.stop.line,
                                           location.stop.column)

        return contents_file[start_at:stop_at + 1]

    def apply(self,
              snapshot: Bug,
              filename: str,
              replacements: List[Replacement]
              ) -> str:
        # TODO ensure all replacements are in the same file
        # TODO sort replacements by the start of their affected character range
        # TODO ensure no replacements are conflicting
        content = self.read_file(snapshot, filename)
        for replacement in replacements:
            # convert location to character offset range
            location = replacement.location
            start_at = self.line_col_to_offset(snapshot,
                                               filename,
                                               location.start.line,
                                               location.start.column)
            stop_at = self.line_col_to_offset(snapshot,
                                              filename,
                                              location.stop.line,
                                              location.stop.column)
            content = \
                content[:start_at] + replacement.text + content[stop_at + 1:]

        return content
