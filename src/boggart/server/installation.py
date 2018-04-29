from typing import Optional, Tuple, Dict, Iterator, List
import os

from bugzoo.client import Client as BugZooClient
from bugzoo.core.bug import Bug
from bugzoo.core.fileline import FileLine

from .mutant import MutantManager
from .sourcefile import SourceFileManager
from ..exceptions import *
from ..core import Language, Mutation, Operator, Mutant
from ..config import Configuration, Languages, Operators

__all__ = ['Installation']


class Installation(object):
    """
    Used to manage a local installation of boggart.
    """
    @classmethod
    def default_user_config_path(cls) -> str:
        """
        The default path to the user-level configuration file.
        """
        if 'HULK_USER_CONFIG_PATH' in os.environ:
            return os.environ['HULK_USER_CONFIG_PATH']

        home = os.environ['HOME']
        default_path = os.path.join(home, '.boggart.yml')
        return default_path

    @classmethod
    def sys_config_path(cls) -> str:
        """
        The path to the system-level configuration file.
        """
        src_dir = os.path.dirname(__file__)
        cfg_fn = os.path.join(src_dir, '../config/sys.boggart.yml')
        return cfg_fn

    @classmethod
    def load(cls,
             client_bugzoo: BugZooClient,
             *,
             user_config_path: Optional[str] = None
             ) -> 'Installation':
        """
        Loads a boggart installation.

        Parameters:
            client_bugzoo: A connection to the BugZoo server that should be
                used by this boggart server.
            config_filepath: The path to the user configuration file for boggart.
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
        self.__sources = SourceFileManager(client_bugzoo)
        self.__mutants = MutantManager(client_bugzoo,
                                       config.operators,
                                       self.__sources)

    @property
    def bugzoo(self) -> BugZooClient:
        """
        A connection to the BugZoo server to which this boggart server is
        attached.
        """
        return self.__bugzoo

    @property
    def sources(self) -> SourceFileManager:
        """
        Provides access to the contents and caches the contents of source code
        belonging to BugZoo snapshots.
        """
        return self.__sources

    @property
    def languages(self) -> Languages:
        """
        The languages registered with this installation.
        """
        return self.__config.languages

    @property
    def operators(self) -> Operators:
        """
        The mutation operators registered with this installation.
        """
        return self.__config.operators

    @property
    def mutants(self) -> MutantManager:
        """
        The active mutants that are registered with this installation.
        """
        return self.__mutants

    def mutations(self,
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

        Raises:
            LanguageNotDetected: if no language is specified and the language
                used by the file cannot be automatically determined.
            FileNotFound: if the given file is not found inside the snapshot.
        """
        if operators is None:
            operators = list(self.operators)

        text = self.sources.read_file(snapshot, filepath)

        if language is None:
            language = self.languages.detect(filepath)

        # TODO talk to Rooibos
        mutations = [] # type: List[Mutation]

        yield from mutations
