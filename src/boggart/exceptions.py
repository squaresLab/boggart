#
# TODO use metaprogramming to reduce the amount of boilerplate
#
from typing import Any, Dict, Tuple

import flask

__all__ = [
    'BoggartException',
    'UnexpectedResponse',
    'ClientServerError',
    'OperatorNameAlreadyExists',
    'OperatorNotFound',
    'LanguageNotFound',
    'LanguageNotDetected',
    'BadConfigFile',
    'IllegalConfig',
    'FileNotFound',
    'MutantNotFound',
    'SnapshotNotFound',
    'ConnectionFailure',
    'BadFormat',
    'UnexpectedServerError',
    'BuildFailure'
]


class BoggartException(Exception):
    """
    Base class for all exceptions produced by Boggart.
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


class ConnectionFailure(BoggartException):
    """
    Failed to establish a connection to the server within the timeout.
    """
    def __init__(self) -> None:
        super().__init__(
            "failed to establish connection to server within timeout."
        )


class UnexpectedResponse(BoggartException):
    """
    The server produced an unexpected response that the client does not know
    how to interpret or decode.
    """
    def __init__(self, response: flask.Response) -> None:
        msg = "Server produced an unexpected response [{}]:\n{}"
        msg = msg.format(response.status_code, response.text)
        super().__init__(msg)


class ClientServerError(BoggartException):
    """
    Base class for all exceptions that may be thrown from the server to the
    client. Provides the necessary machinery to write/read errors to/from
    JSON descriptions.
    """
    @staticmethod
    def from_dict(d: dict) -> 'BoggartException':
        assert 'error' in d
        d = d['error']

        assert isinstance(d, dict)
        assert 'kind' in d

        # TODO use metaprogramming to avoid having to maintain this list
        cls = ({
            'OperatorNameAlreadyExists': OperatorNameAlreadyExists,
            'LanguageNotFound': LanguageNotFound,
            'BadConfigFile': BadConfigFile,
            'IllegalConfig': IllegalConfig,
            'UnexpectedServerError': UnexpectedServerError
        })[d['kind']]

        return cls.from_data(d.get('data', {}))  # type: ignore

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

    @property
    def data(self) -> Dict[str, Any]:
        return {}

    def to_response(self) -> Tuple[Any, int]:
        """
        Transforms this exception into a HTTP response containing a
        machine-readable description of the exception.
        """
        jsn = {
            'kind': self.__class__.__name__,
            'message': self.message
        }
        data = self.data
        if data:
            jsn['data'] = data
        jsn = {'error': jsn}
        return jsn, self.__status_code


class BuildFailure(ClientServerError):
    """
    The mutant failed to build.
    """
    @staticmethod
    def from_data(data: dict) -> 'BuildFailure':
        return BuildFailure()

    def __init__(self) -> None:
        super().__init__(400, "failed to build mutant.")


class BadFormat(ClientServerError):
    """
    A given data structure did not match the expected format.
    """
    @staticmethod
    def from_data(data: dict) -> 'BadFormat':
        assert 'reason' in data
        return BadFormat(data['reason'])

    def __init__(self, reason: str) -> None:
        self.__reason = reason
        super().__init__(400, "unexpected format: {}".format(reason))

    @property
    def reason(self) -> str:
        return self.__reason

    @property
    def data(self) -> Dict[str, Any]:
        return {'reason': self.reason}


class UnexpectedServerError(ClientServerError):
    """
    The server encountered an unexpected error.
    """
    @staticmethod
    def from_exception(ex: Exception) -> 'UnexpectedServerError':
        return UnexpectedServerError(str(ex))

    @staticmethod
    def from_data(data: dict) -> 'UnexpectedServerError':
        assert 'message' in data
        return UnexpectedServerError(data['message'])

    def __init__(self, message: str) -> None:
        self.__message = message
        super().__init__(500, "unexpected error: {}".format(message))

    @property
    def message(self) -> str:
        return self.__message

    @property
    def data(self) -> Dict[str, Any]:
        return {'message': self.message}


class OperatorNameAlreadyExists(ClientServerError):
    """
    Used to indicate that a given operator name is already in use by another
    operator.
    """
    @staticmethod
    def from_data(data: dict) -> 'OperatorNameAlreadyExists':
        assert 'name' in data
        return OperatorNameAlreadyExists(data['name'])

    def __init__(self,
                 name: str,
                 *,
                 status_code: int = 409
                 ) -> None:
        self.__name = name
        msg = "operator name is already in use: {}".format(name)
        super().__init__(status_code, msg)

    @property
    def name(self) -> str:
        """
        The name of the requested operator.
        """
        return self.__name

    @property
    def data(self) -> Dict[str, Any]:
        return {'name': self.name}


class LanguageNotFound(ClientServerError):
    """
    Used to indicate that there exists no language registered under a given
    name.
    """
    @staticmethod
    def from_data(data: dict) -> 'LanguageNotFound':
        assert 'name' in data
        return LanguageNotFound(data['name'])

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

    @property
    def data(self) -> Dict[str, Any]:
        return {'name': self.name}


class LanguageNotDetected(ClientServerError):
    """
    Failed to automatically detect the language used by a file.
    """
    @staticmethod
    def from_data(data: dict) -> 'LanguageNotDetected':
        assert 'filename' in data
        return LanguageNotDetected(data['filename'])

    def __init__(self,
                 filename: str,
                 *,
                 status_code: int = 400
                 ) -> None:
        self.__filename = filename
        msg = "unable to automatically detect language used by file: {}"
        msg = msg.format(filename)
        super().__init__(status_code, msg)

    @property
    def filename(self) -> str:
        """
        The name of the file.
        """
        return self.__filename

    @property
    def data(self) -> Dict[str, Any]:
        return {'filename': self.filename}


class OperatorNotFound(ClientServerError):
    """
    Used to indicate that no operator has been registered under a given name.
    """
    @staticmethod
    def from_data(data: dict) -> 'OperatorNotFound':
        assert 'name' in data
        return OperatorNotFound(data['name'])

    def __init__(self,
                 name: str,
                 *,
                 status_code: int = 404
                 ) -> None:
        self.__name = name
        msg = "no operator registered with name: {}".format(name)
        super().__init__(status_code, msg)

    @property
    def name(self) -> str:
        """
        The name of the requested language.
        """
        return self.__name

    @property
    def data(self) -> Dict[str, Any]:
        return {'name': self.name}


class SnapshotNotFound(ClientServerError):
    """
    Used to indicate that no snapshot was found with the given name on the
    attached BugZoo server.
    """
    @staticmethod
    def from_data(data: dict) -> 'SnapshotNotFound':
        assert 'name' in data
        return SnapshotNotFound(data['name'])

    def __init__(self,
                 name: str,
                 *,
                 status_code: int = 404
                 ) -> None:
        self.__name = name
        msg = "no BugZoo snapshot registered with name: {}".format(name)
        super().__init__(status_code, msg)

    @property
    def name(self) -> str:
        """
        The name of the requested snapshot.
        """
        return self.__name

    @property
    def data(self) -> Dict[str, Any]:
        return {'name': self.name}


class MutantNotFound(ClientServerError):
    """
    Used to indicate that the requested file was not found.
    """
    @staticmethod
    def from_data(data: dict) -> 'MutantNotFound':
        assert 'uuid' in data
        return MutantNotFound(data['uuid'])

    def __init__(self,
                 uuid: str,
                 *,
                 status_code: int = 404
                 ) -> None:
        self.__uuid = uuid
        msg = "mutant not found: {}".format(uuid)
        super().__init__(status_code, msg)

    @property
    def uuid(self) -> str:
        """
        The UUID of the missing mutant.
        """
        return self.__uuid

    @property
    def data(self) -> Dict[str, Any]:
        return {'uuid': self.uuid}


class FileNotFound(ClientServerError):
    """
    Used to indicate that the requested file was not found.
    """
    @staticmethod
    def from_data(data: dict) -> 'FileNotFound':
        assert 'name' in data
        return FileNotFound(data['name'])

    def __init__(self,
                 name: str,
                 *,
                 status_code: int = 404
                 ) -> None:
        self.__name = name
        msg = "file not found: {}".format(name)
        super().__init__(status_code, msg)

    @property
    def name(self) -> str:
        """
        The name of the missing file.
        """
        return self.__name

    @property
    def data(self) -> Dict[str, Any]:
        return {'name': self.name}


class BadConfigFile(BoggartException):
    """
    Used to indicate that a given configuration file is ill-formed.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(reason)


class IllegalConfig(BoggartException):
    """
    Used to indicate that a given configuration is syntatically correct but
    that it describes an illegal configuration.
    """
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
