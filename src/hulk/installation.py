from typing import Optional, Tuple, Dict, Iterator, List
import os

from bugzoo.client import Client as BugZooClient
from bugzoo.core.bug import Bug
from bugzoo.core.fileline import FileLine

from .exceptions import *
from .core import Language, Mutation, Operator
from .config import Configuration, Languages, Operators

__all__ = ['Installation']


class Installation(object):
    """
    Used to manage a local installation of Hulk.
    """
    @classmethod
    def default_user_config_path(cls) -> str:
        """
        The default path to the user-level configuration file.
        """
        if 'HULK_USER_CONFIG_PATH' in os.environ:
            return os.environ['HULK_USER_CONFIG_PATH']

        home = os.environ['HOME']
        default_path = os.path.join(home, '.hulk.yml')
        return default_path

    @classmethod
    def sys_config_path(cls) -> str:
        """
        The path to the system-level configuration file.
        """
        src_dir = os.path.dirname(__file__)
        cfg_fn = os.path.join(src_dir, 'config/sys.hulk.yml')
        return cfg_fn

    @classmethod
    def load(cls,
             client_bugzoo: BugZooClient,
             *,
             user_config_path: Optional[str] = None,
             ) -> 'Installation':
        """
        Loads a Hulk installation.

        Parameters:
            client_bugzoo: A connection to the BugZoo server that should be
                used by this Hulk server.
            config_filepath: The path to the user configuration file for Hulk.
                If left unspecified, `Installation.default_user_config_path`
                will be used instead.
        """
        if not user_config_path:
            user_config_path = Installation.default_user_config_path()

        system_cfg = Configuration.from_file(Installation.sys_config_path())

        if not os.path.isfile(user_config_path):
            return Installation(system_cfg, client_bugzoo)

        user_cfg = Configuration.from_file(user_config_path, system_cfg)
        return Installation(user_cfg, client_bugzoo)

    def __init__(self,
                 config: Configuration,
                 client_bugzoo: BugZooClient
                 ) -> None:
        self.__config = config
        self.__bugzoo = client_bugzoo

        self.__cache_file_contents = {} # type: Dict[Tuple[str, str], str]

    @property
    def bugzoo(self) -> BugZooClient:
        """
        A connection to the BugZoo server to which this Hulk server is
        attached.
        """
        return self.__bugzoo

    @property
    def languages(self) -> Languages:
        """
        The languages registered with this local Hulk installation.
        """
        return self.__config.languages

    @property
    def operators(self) -> Operators:
        """
        The mutation operators registered with this local Hulk installation.
        """
        return self.__config.operators

    def detect_language(self, filename: str) -> Optional[Language]:
        """
        Attempts to automatically detect the language used by a file based
        on its file ending.

        Returns:
            The language associated with the file ending used by the given file.

        Raises:
            LanguageNotDetected: if the language used by the filename could not
                be automatically detected.
        """
        _, suffix = os.path.splitext(filename)
        for language in self.languages:
            if suffix in language.file_endings:
                return language
        raise LanguageNotDetected(filename)

    def read_file_contents(self, snapshot: Bug, filepath: str) -> str:
        """
        Fetches the contents of a specified source code file belonging to a
        given BugZoo snapshot.

        Raises:
            FileNotFound: if the given file is not found inside the snapshot.
        """
        key_cache = (snapshot.name, filepath)
        if key_cache in self.__cache_file_contents:
            return self.__cache_file_contents[key_cache]

        container = self.bugzoo.containers.provision(snapshot)
        try:
            contents = self.bugzoo.files.read(container, filepath)
        except KeyError:
            raise FileNotFound(filepath)
        finally:
            del self.bugzoo.containers[container.uid]

        self.__cache_file_contents[key_cache] = contents
        return contents

    def mutations_to_snapshot(self,
                              snapshot: Bug,
                              filepath: str,
                              *,
                              language: Language = None,
                              operators: List[Operator] = None,
                              restrict_to_lines: Iterator[FileLine] = None
                              ) -> Iterator[Mutation]:
        """
        Computes all of the first-order mutations that can be applied to a
        given file belonging to a specified BugZoo snapshot.

        Returns:
            an iterator over the possible mutations.
        """
        text = self.read_file_contents(snapshot, filepath)
        return self.mutations_to_text(text,
                                      language,
                                      operators=operators,
                                      restrict_to_lines=restrict_to_lines)

    def mutations_to_text(self,
                          text: str,
                          language: Language,
                          *,
                          operators: List[Operator] = None,
                          restrict_to_lines: Iterator[FileLine] = None
                          ) -> Iterator[Mutation]:
        # TODO talk to Rooibos
        raise NotImplementedError
