class HulkException(Exception):
    """
    Base class for all exceptions produced by Hulk.
    """
    pass


class OperatorNameAlreadyExists(HulkException):
    """
    Used to indicate that a given operator name is already in use by another
    operator.
    """
    def __init__(self, name: str) -> None:
        self.__name = name
        msg = "operator name is already in use: {}".format(name)
        super().__init__(msg)

    @property
    def name(self) -> str:
        """
        The name of the requested operator.
        """
        return self.__name


class LanguageNotFound(HulkException):
    """
    Used to indicate that there exists no language registered under a given
    name.
    """
    def __init__(self, name: str) -> None:
        self.__name = name
        msg = "no language registered with name: {}".format(name)
        super().__init__(msg)

    @property
    def name(self) -> str:
        """
        The name of the requested language.
        """
        return self.__name


class BadConfigFile(HulkException):
    """
    Used to indicate that a given configuration file is ill-formed.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(reason)


class IllegalConfig(HulkException):
    """
    Used to indicate that a given configuration is syntatically correct but
    that it describes an illegal configuration.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
