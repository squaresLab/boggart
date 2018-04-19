from typing import Any, Dict, Tuple

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
    def __init__(self, message: str) -> None:
        self.__message = message
        super().__init__(message)

    @property
    def message(self):
        """
        A short description of the error.
        """
        return self.__message


class ClientServerError(HulkException):
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

    def __init__(self, status_code: int, message: str) -> None:
        self.__status_code = status_code
        super().__init__(message)

    @property
    def status_code(self) -> int:
        """
        The status code that was produced by the server when this error was
        reported to the client.
        """
        return self.__status_code

    def to_response(self, data: Dict[str, Any] = None) -> Tuple[Any, int]:
        """
        Transforms this exception into a HTTP response containing a
        machine-readable description of the exception.
        """
        jsn = {
            'kind': self.__class__.__name__,
            'message': self.message
        }
        if data:
            jsn['data'] = data
        return jsn, self.__status_code


class OperatorNameAlreadyExists(ClientServerError):
    """
    Used to indicate that a given operator name is already in use by another
    operator.
    """
    @staticmethod
    def from_dict(d: dict) -> 'OperatorNameAlreadyExists':
        assert 'data' in d
        assert 'name' in d['data']
        return OperatorNameAlreadyExists(d['data']['name'])

    def __init__(self,
                 name: str,
                 *,
                 status_code: int = 409
                 ) -> None:
        self.__name = name
        msg = "operator name is already in use: {}".format(name)
        super().__init__(msg, status_code)

    @property
    def name(self) -> str:
        """
        The name of the requested operator.
        """
        return self.__name

    def to_response(self) -> Tuple[Any, int]:
        return super().to_response(data={'name': self.name})


class LanguageNotFound(ClientServerError):
    """
    Used to indicate that there exists no language registered under a given
    name.
    """
    @staticmethod
    def from_dict(d: dict) -> 'LanguageNotFound':
        assert 'data' in d
        assert 'name' in d['data']
        return LanguageNotFound(d['data']['name'])

    def __init__(self,
                 name: str,
                 *,
                 status_code: int = 404
                 ) -> None:
        self.__name = name
        msg = "no language registered with name: {}".format(name)
        super().__init__(status_code, msg)

    @property
    def name(self) -> str:
        """
        The name of the requested language.
        """
        return self.__name

    def to_response(self) -> Tuple[Any, int]:
        return super().to_response(data={'name': self.name})


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
