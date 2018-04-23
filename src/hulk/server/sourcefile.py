from typing import Dict, Tuple

from bugzoo.core.bug import Bug
from bugzoo.client import Client as BugZooClient

from ..core import FileLocationRange
from ..exceptions import *

__all__ = ['SourceFileManager']


class SourceFileManager(object):
    def __init__(self, client_bugzoo: BugZooClient) -> None:
        self.__cache_contents_cache = {} # type: Dict[Tuple[str, str], str]

    def line_col_to_offset(self,
                           snapshot: Bug,
                           filepath: str,
                           line_num: int,
                           col_num: int) -> int:
        """
        Transforms a line-column number for a given file belonging to a
        BugZoo snapshot into a zero-indexed character offset.
        """
        raise NotImplementedError

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
        filename = location.filepath
        contents_file = self.read_file(filename)

        start_at = self.line_col_to_offset(snapshot,
                                           filename,
                                           location.start.line_num,
                                           location.start_col_num)
        stop_at = self.line_col_to_offset(snapshot,
                                           filename,
                                           location.stop.line_num,
                                           location.stop.col_num)

        return contents_file[start_at:stop_at + 1]
