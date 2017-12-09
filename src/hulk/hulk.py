from typing import Optional


class Hulk(object):
    """
    Used to manage a local installation of Hulk.
    """

    @property
    @staticmethod
    def default_user_config_path() -> str:
        """
        The default path to the user-level configuration file.
        """
        raise NotImplementedError

    @property
    @staticmethod
    def sys_config_path() -> str:
        """
        The path to the system-level configuration file.
        """
        raise NotImplementedError

    def __init__(self,
                 user_config_path: Optional[str] = None):
        """
        Constructs a Hulk installation.

        Params:
            config_filepath: The path to the user configuration file for Hulk.
                If left unspecified, `Hulk.default_user_config_path` will be
                used instead.
        """
        if user_config_path:
            self.__user_config_file = user_config_path
        else:
            self.__user_config_file = Hulk.default_user_config_path

    @property
    def user_config_path(self) -> str:
        """
        The path to the user-level configuration used by this installation.
        """
        return self.__user_config_file
