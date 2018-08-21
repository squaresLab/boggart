from typing import Dict, Union, List, Any
try:
    from typing import NoReturn
except ImportError:
    from mypy_extensions import NoReturn
from urllib.parse import urljoin, urlparse
from timeit import default_timer as timer
import time
import logging

import requests

from ..exceptions import ConnectionFailure, \
                         ClientServerError, \
                         UnexpectedResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__all__ = ['API']


class API(object):
    def __init__(self,
                 base_url: str,
                 *,
                 timeout: int = 30,
                 timeout_connection: int = 60
                 ) -> None:
        """
        Constructs a new low-level API client for communicating with a boggart
        server at a given address.

        Parameters:
            base_url: the base URL of the boggart server.
            timeout: the default timeout for API calls (in seconds).
            timeout_connection: the maximum numbers of seconds to wait when
                attempting to connect to the server before raising a
                ConnectionFailure exception.

        Raises:
            ValueError: if the provided URL lacks a scheme (e.g., 'http').
            ConnectionFailure: if a connection to the server could not be
                established within the connection timeout window.
        """
        if not urlparse(base_url).scheme:
            logger.error("invalid base URL provided: missing scheme.")
            raise ValueError("invalid base URL provided: missing scheme (e.g., 'http').")  # noqa: pycodestyle

        self.__base_url = base_url
        self.__timeout = timeout

        logger.info("attempting to establish connection to server '%s' with timeout of %d seconds",  # noqa: pycodestyle
                    base_url,
                    timeout)
        url = self.url("status")
        time_started = timer()
        connected = False
        while not connected:
            time_running = timer() - time_started
            time_left = timeout_connection - time_running
            if time_left <= 0.0:
                logger.error("failed to connect to server: %s", base_url)
                raise ConnectionFailure
            try:
                r = requests.get(url, timeout=time_left)
                connected = r.status_code == 204
                logger.info("connected to server: %s", base_url)
            except requests.exceptions.ConnectionError:
                time.sleep(1.0)
            except requests.exceptions.Timeout:
                logger.error("failed to connect to server: %s", base_url)
                raise ConnectionFailure
            time.sleep(0.05)

    @property
    def base_url(self) -> str:
        """
        The base URL of the server.
        """
        return self.__base_url

    def handle_erroneous_response(self,
                                  response: requests.Response
                                  ) -> NoReturn:
        """
        Attempts to decode an erroneous response into an exception, and to
        subsequently throw that exception.

        Raises:
            ClientServerError: the exception described by the error response.
            UnexpectedResponse: if the response cannot be decoded to an
                exception.
        """
        logger.debug("handling erroneous response [%d]:\n%s",
                     response.status_code,
                     response.text)
        try:
            err = ClientServerError.from_dict(response.json())
            logger.debug("parsed erroneous response to: %s", repr(err))
        except Exception:
            logger.debug("unexpected response [%d]:\n%s",
                         response.status_code,
                         response.text)
            err = UnexpectedResponse(response)
        raise err

    def url(self, path: str) -> str:
        """
        Computes the URL to a resource located at a given path on the server.
        """
        return urljoin(self.__base_url, path)

    def get(self,
            path: str,
            params: Dict[str, Any] = None,
            **kwargs
            ) -> requests.Response:
        url = self.url(path)
        return requests.get(url, params, **kwargs)

    def post(self, path: str, data=None, **kwargs) -> requests.Response:
        url = self.url(path)
        return requests.post(url, data, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        url = self.url(path)
        return requests.put(url, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        url = self.url(path)
        return requests.delete(url, **kwargs)
