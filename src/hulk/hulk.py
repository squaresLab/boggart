import os
from hulk.config import Configuration, Languages, Operators
from typing import Optional


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
    def load(cls, user_config_path: Optional[str] = None) -> 'Hulk':
        """
        Loads a Hulk installation.

        Params:
            - config_filepath: The path to the user configuration file for Hulk.
                If left unspecified, `Hulk.default_user_config_path` will be
                used instead.
        """
        if not user_config_path:
            user_config_path = Hulk.default_user_config_path()

        system_cfg = Configuration.from_file(Hulk.sys_config_path())

        if not os.path.isfile(user_config_path):
            return system_cfg

        user_cfg = Configuration.from_file(user_config_path, system_cfg)
        return user_cfg

    def __init__(self, config: Configuration) -> None:
        self.__config: Configuration = config

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
