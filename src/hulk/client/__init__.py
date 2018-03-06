import urllib.parse
import requests
from .languages import LanguageCollection


class Client(object):
    """
    A client for communicating with a Hulk server.
    """
    def __init__(self,
                 base_url: str,
                 timeout: int = 30):
        """
        Constructs a new client for communicating with a given Hulk server.

        Parameters:
            base_url:   the URL of the Hulk server.
            timeout:    the default timeout for API calls (in seconds).
        """
        self.__base_url = base_url
        self.__timeout = timeout

    @property
    def languages(self) -> LanguageCollection:
        """
        The set of languages that are supported (i.e., can be mutated)
        by the server.
        """
        # TODO: cache?
        return LanguageCollection(client=self)

    def _url(self, path: str) -> str:
        """
        Computes the URL to a resource located at a given path on the server.
        """
        url = urllib.parse.urljoin(self.__base_url, path)
        return str(url)

    def _get(self, path: str, params = None, **kwargs) -> requests.Response:
        """
        Sends a GET request to the server.

        Parameters:
            path:   the path of the resource.
        """
        url = self._url(path)
        return requests.get(url, params, **kwargs)
