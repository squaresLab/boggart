from typing import Optional, Tuple, Dict
import os

import bugzoo
import bugzoo.client

from hulk.base import Language
from hulk.config import Configuration, Languages, Operators


class Hulk(object):
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
             client_bugzoo: bugzoo.client.Client,
             *,
             user_config_path: Optional[str] = None,
             ) -> 'Hulk':
        """
        Loads a Hulk installation.

        Parameters:
            client_bugzoo: A connection to the BugZoo server that should be
                used by this Hulk server.
            config_filepath: The path to the user configuration file for Hulk.
                If left unspecified, `Hulk.default_user_config_path` will be
                used instead.
        """
        if not user_config_path:
            user_config_path = Hulk.default_user_config_path()

        system_cfg = Configuration.from_file(Hulk.sys_config_path())

        if not os.path.isfile(user_config_path):
            return Hulk(system_cfg, client_bugzoo)

        user_cfg = Configuration.from_file(user_config_path, system_cfg)
        return Hulk(user_cfg, client_bugzoo)

    def __init__(self,
                 config: Configuration,
                 client_bugzoo: bugzoo.client.Client
                 ) -> None:
        self.__config = config
        self.__bugzoo = client_bugzoo

        self._cache_file_contents = {} # type: Dict[Tuple[str, str], str]

    @property
    def bugzoo(self) -> bugzoo.client.Client:
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
            The language associated with the file ending used by the given file,
            if one exists; if no language is associated with the file ending,
            or if the file has no suffix, `None` is returned instead.
        """
        (_, suffix) = os.path.splitext(filename)
        for language in self.languages:
            if suffix in language.file_endings:
                return language
        return None # technically this is implicit
