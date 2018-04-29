from typing import Dict, Union, List, Any
from urllib.parse import urljoin, urlparse
from timeit import default_timer as timer
import time

import requests

from ..exceptions import ConnectionFailure


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
          raise ValueError("invalid base URL provided: missing scheme (e.g., 'http').")

        self.__base_url = base_url
        self.__timeout = timeout

        # attempt to establish a connection
        url = self.url("status")
        time_left = float(timeout_connection)
        time_started = timer()
        connected = False
        while time_left > 0.0 and not connected:
            try:
                r = requests.get(url, timeout=time_left)
                connected = r.status_code == 204
            except requests.exceptions.ConnectionError:
                time.sleep(1.0)
            except requests.exceptions.Timeout:
                raise ConnectionFailure
            time.sleep(0.05)
            time_left -= timer() - time_started
        if not connected:
            raise ConnectionFailure

    @property
    def base_url(self) -> str:
        """
        The base URL of the server.
        """
        return self.__base_url

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
        """
        Sends a GET request to the server.

        Parameters:
            path:   the path of the resource.
        """
        url = self.url(path)
        return requests.get(url, params, **kwargs)

    def post(self, path: str, data = None, **kwargs) -> requests.Response:
        url = self.url(path)
        return requests.post(url, data, **kwargs)