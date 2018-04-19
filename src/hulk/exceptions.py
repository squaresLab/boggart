import flask

__ALL__ = [
    'HulkException',
    'ServerError',
    'OperatorNameAlreadyExists',
    'LanguageNotFound',
    'BadConfigFile',
    'IllegalConfig'
]


class HulkException(Exception):
    """
    Base class for all exceptions produced by Hulk.
    """

class ServerError(HulkException):
    """
    Base class for all exceptions that may be thrown from the server to the
    client. Provides the necessary machinery to write/read errors to/from
    JSON descriptions.
    """
    @staticmethod
    def from_dict(d: dict) -> 'HulkException':
        assert 'kind' in d

        # TODO use metaprogramming to avoid having to maintain this list
        cls = ({
            'OperatorNameAlreadyExists': OperatorNameAlreadyExists,
            'LanguageNotFound': LanguageNotFound,
            'BadConfigFile': BadConfigFile,
            'IllegalConfig': IllegalConfig
        })[d]

        return cls.from_dict(d)

    def to_response(self) -> flask.Response:
        """
        Transforms this exception into a HTTP response containing a
        machine-readable description of the exception.
        """
        raise NotImplementedError


class OperatorNameAlreadyExists(ServerError):
    """
    Used to indicate that a given operator name is already in use by another
    operator.
    """
    @staticmethod
    def from_dict(d: dict) -> 'OperatorNameAlreadyExists':
        assert 'name' in d
        return OperatorNameAlreadyExists(d['name'])

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


class LanguageNotFound(ServerError):
    """
    Used to indicate that there exists no language registered under a given
    name.
    """
    @staticmethod
    def from_dict(d: dict) -> 'LanguageNotFound':
        assert 'name' in d
        return LanguageNotFound(d['name'])

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


class BadConfigFile(ServerError):
    """
    Used to indicate that a given configuration file is ill-formed.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(reason)


class IllegalConfig(ServerError):
    """
    Used to indicate that a given configuration is syntatically correct but
    that it describes an illegal configuration.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
