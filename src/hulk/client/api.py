from typing import Dict, Union, List
from urllib.parse import urljoin, urlparse

import requests


class API(object):
    def __init__(self,
                 base_url: str,
                 *,
                 timeout: int = 30,
                 timeout_connection: int = 60
                 ) -> None:
        """
        Constructs a new low-level API client for communicating with a Hulk
        server at a given address.

        Parameters:
            base_url: the base URL of the Hulk server.
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

        # FIXME attempt to connect to server

    @property
    def base_url(self) -> str:
        """
        The base URL of the Hulk server.
        """
        return self.__base_url

    def url(self, path: str) -> str:
        """
        Computes the URL to a resource located at a given path on the server.
        """
        return urljoin(self.__base_url, path)

    def get(self,
            path: str,
            params: Dict[str, Union[str, List[str]]] = None,
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
