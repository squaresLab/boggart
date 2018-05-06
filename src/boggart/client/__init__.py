from typing import Optional, Union, Dict, List, Iterator, Tuple, NoReturn
import logging

import requests
from bugzoo.core.bug import Bug

from .api import API
from .languages import LanguageCollection
from .operators import OperatorCollection
from ..exceptions import *
from ..core import Operator, Language, Mutation, Mutant


logger = logging.getLogger(__name__)


__all__ = ['Client']


class Client(object):
    """
    A client for communicating with a boggart server.
    """
    def __init__(self,
                 base_url: str,
                 *,
                 timeout: int = 30,
                 timeout_connection: int = 60
                 ) -> None:
        """
        Constructs a new client for communicating with a given boggart server.

        Parameters:
            base_url:   the URL of the boggart server.
            timeout:    the default timeout for API calls (in seconds).

        Raises:
            ValueError: if the provided URL lacks a scheme (e.g., 'http').
        """
        logger.info("constructing client for boggart server: %s", base_url)
        self.__api = API(base_url,
                         timeout=timeout,
                         timeout_connection=timeout_connection)
        self.__languages = LanguageCollection(api=self.api)
        self.__operators = OperatorCollection(api=self.api)
        logger.info("registered languages: %s",
                    ', '.join([l.name for l in self.__languages]))
        logger.info("registered operators: %s",
                    ', '.join([op.name for op in self.__operators]))
        logger.info("constructed client for boggart server: %s", base_url)

    @property
    def base_url_bugzoo(self) -> str:
        """
        The base URL of the BugZoo server to which this boggart server is
        attached.
        """
        raise NotImplementedError

    @property
    def base_url_rooibos(self) -> str:
        """
        The base URL of the Rooibos server to which this boggart server is
        attached.
        """
        raise NotImplementedError

    @property
    def api(self) -> API:
        """
        The low-level client API used to communicate with the server.
        """
        return self.__api

    @property
    def languages(self) -> LanguageCollection:
        """
        The set of languages that are supported (i.e., can be mutated)
        by the server.
        """
        return self.__languages

    @property
    def operators(self) -> OperatorCollection:
        """
        The set of mutation operators that are supported by the server.
        """
        return self.__operators

    def __handle_error_response(self, response: requests.Response) -> NoReturn:
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

    def mutations(self,
                  snapshot: Bug,
                  filepath: str,
                  *,
                  language: Optional[Language] = None,
                  operators: Optional[List[Operator]] = None,
                  restrict_to_lines: Optional[List[int]] = None
                  ) -> Iterator[Mutation]:
        """
        Returns an iterator over all of the mutations that can be applied to
        a given file belonging to a BugZoo snapshot.

        Parameters:
            snapshot: the BugZoo snapshot.
            filepath: the path to the source code file inside the snapshot,
                relative to its source directory.
            language: the language that the source code file is written in. If
                left unspecified, boggart will attempt to automatically
                determine the language based on the file ending.
            operators: an optional list of mutation operators that should be
                used to generate mutations. If no list is provided, then all
                registered mutation operators for the specified language will
                be used as a default.

        Returns:
            an iterator over the possible mutations.

        Raises:
            SnapshotNotFound: if the given snapshot does not appear to be
                registered with the BugZoo server that is attached to this
                boggart server.
            FileNotFound: if no file is found with the given name in the
                snapshot.
        """
        assert operators is None or len(operators) > 0

        logger.info("Finding mutations in file '%s' belonging to snapshot '%s'.",  # noqa: pycodestyle
                    filepath,
                    snapshot.name)
        path = "mutations/{}/{}".format(snapshot.name, filepath)
        params = {}
        if language:
            params['language'] = language.name
        if operators:
            params['operators'] = ';'.join([op.name for op in operators])

        response = self.api.get(path, params)

        if response.status_code == 200:
            for jsn_mutation in response.json():
                logger.debug("Decoding mutation.",
                             extra={'mutation': jsn_mutation})
                mutation = Mutation.from_dict(jsn_mutation)
                logger.info("Found mutation: %s", repr(mutation))
                yield mutation
        else:
            logger.info("An error occurred whilst attempting to find mutations.")  # noqa: pycodestyle
            self.__handle_error_response(response)

    def mutate(self,
               snapshot: Bug,
               mutations: List[Mutation]
               ) -> Mutant:
        """
        Applies a given mutation to a snapshot.

        Parameters:
            snapshot: the snapshot that should be mutated.
            mutations: the mutations to apply to the snapshot.

        Returns:
            a description of the generated mutant.
        """
        payload = {
            'snapshot': snapshot.name,
            'mutations': [m.to_dict() for m in mutations]
        }
        logger.info("Applying mutations to snapshot '%s': %s",
                    snapshot.name,
                    ', '.join(repr(m) for m in mutations),
                    extra=payload)
        response = self.api.post("mutants", json=payload)

        if response.status_code == 200:
            mutant = Mutant.from_dict(response.json())
            logger.info("Applied mutations to snapshot '%s' to generate mutant: %s",  # noqa: pycodestyle
                        snapshot.name,
                        repr(mutant),
                        extra={'mutant': response.json()})
            return mutant
        else:
            logger.info("An error occurred whilst attempting to mutate snapshot.")  # noqa: pycodestyle
            self.__handle_error_response(response)
