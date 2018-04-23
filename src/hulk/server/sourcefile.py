from typing import Dict, Tuple

from bugzoo.core.bug import Bug
from bugzoo.client import Client as BugZooClient

from ..exceptions import *

__all__ = ['SourceFileManager']


class SourceFileManager(object):
    def __init__(self, client_bugzoo: BugZooClient) -> None:
        self.__cache_contents_cache = {} # type: Dict[Tuple[str, str], str]

    def read_file(self, snapshot: Bug, filepath: str) -> str:
        """
        Fetches the contents of a specified source code file belonging to a
        given BugZoo snapshot.

        Raises:
            FileNotFound: if the given file is not found inside the snapshot.
        """
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
