# TODO mutants are killed when the server is killed
from typing import Optional, Union, Dict, List, Iterator, Tuple
from urllib.parse import urljoin, urlparse
import difflib
import tempfile
import os

import requests
from bugzoo.core.bug import Bug
from bugzoo.core.fileline import FileLine

from ..exceptions import *
from ..base import Operator, Language, Mutation
from .languages import LanguageCollection
from .operators import OperatorCollection


__all__ = ['Client']


class Client(object):
    """
    A client for communicating with a Hulk server.
    """
    def __init__(self,
                 base_url: str,
                 timeout: int = 30
                 ) -> None:
        """
        Constructs a new client for communicating with a given Hulk server.

        Parameters:
            base_url:   the URL of the Hulk server.
            timeout:    the default timeout for API calls (in seconds).

        Raises:
            ValueError: if the provided URL lacks a scheme (e.g., 'http').
        """
        if not urlparse(base_url).scheme:
          raise ValueError("invalid base URL provided: missing scheme (e.g., 'http').")

        self.__base_url = base_url
        self.__timeout = timeout

        # maintain a local cache of the contents of files for BugZoo snapshots
        # map from (snapshot-name, filename) to contents of the file
        self.__cache_file_contents = {} # type: Dict[Tuple[str, str], str]

    @property
    def languages(self) -> LanguageCollection:
        """
        The set of languages that are supported (i.e., can be mutated)
        by the server.
        """
        # TODO: cache?
        return LanguageCollection(client=self)

    @property
    def operators(self) -> OperatorCollection:
        """
        The set of mutation operators that are supported by the server.
        """
        # TODO: cache?
        return OperatorCollection(client=self)

    def _url(self, path: str) -> str:
        """
        Computes the URL to a resource located at a given path on the server.
        """
        return urljoin(self.__base_url, path)

    def _get(self,
             path: str,
             params: Dict[str, Union[str, List[str]]] = None,
             **kwargs
             ) -> requests.Response:
        """
        Sends a GET request to the server.

        Parameters:
            path:   the path of the resource.
        """
        url = self._url(path)
        return requests.get(url, params, **kwargs)

    def mutations_to_snapshot(self,
                              snapshot: Bug,
                              filepath: str,
                              *,
                              language: Optional[Language] = None,
                              operators: Optional[List[Operator]] = None,
                              restrict_to_lines: Optional[List[FileLine]] = None
                              ) -> Iterator[Mutation]:
        """
        Returns an iterator over all of the mutations that can be applied to
        a given file belonging to a BugZoo snapshot.

        Parameters:
            snapshot: the BugZoo snapshot.
            filepath: the path to the source code file inside the snapshot,
                relative to its source directory.
            language: the language that the source code file is written in. If
                left unspecified, Hulk will attempt to automatically determine
                the language based on the file ending.
            operators: an optional list of mutation operators that should be
                used to generate mutations. If no list is provided, then all
                registered mutation operators for the specified language will
                be used as a default.

        Returns:
            an iterator over the possible mutations.

        Raises:
            SnapshotNotFound: if the given snapshot does not appear to be
                registered with the BugZoo server that is attached to this
                Hulk server.
            FileNotFound: if no file is found with the given name in the
                snapshot.
        """
        raise NotImplementedError

    def mutations_to_text(self,
                          text: str,
                          language: Language,
                          operators: Optional[List[Operator]] = None
                          ) -> Iterator[Mutation]:
        """
        Returns an iterator over all of the mutations that can be applied to
        a given body of text.

        Parameters:
            text: the text whose mutations should be computed.
            language: the language that the source text is written in.
            operators: an optional list of mutation operators that should be
                used to generate mutations. If no list is provided, then all
                registered mutation operators for the specified language will
                be used as a default.

        Returns:
            an iterator over the possible mutations.

        Raises:
            LanguageNotFound: given language is not registered with server.
            OperatorNotFound: one or more of the given operators is not
                registered with the server.
        """
        assert operators is None or len(operators) > 0

        path = "mutations/{}".format(filepath)
        params = {}
        if language:
            params['language'] = language.name
        if operators:
            params['operators'] = ';'.join([op.name for op in operators])

        response = self._get(path, params, data=text)

        # TODO handle errors

        if response.status_code == 200:
            for jsn_mutation in response.json():
                yield Mutation.from_dict(jsn_mutation)

    def mutate_text(self,
                    text: str,
                    mutation: Mutation
                    ) -> str:
        """
        Applies a given mutation to a body of text.

        Parameters:
            text: the body of text that should be mutated.
            mutation: the mutation to apply to the text.

        Returns:
            a variant of the text that contains the given mutation.

        Raises:
            LocationNotFound: if the location described in the mutation does
                not exist in the given text.
        """
        raise NotImplementedError

    def mutate_snapshot(self,
                        snapshot_original: Bug,
                        mutation: Mutation
                        ) -> Bug:
        """
        Applies a given mutation to a snapshot.

        Parameters:
            snapshot_original: the snapshot to mutate.
            mutation: the mutation to apply to the snapshot.

        Returns:
            a variant of the given snapshot that has been subjected to the
            given mutation.
        """
        # TODO move to server
        # create a temporary dir for the mutant
        dir_temp = tempfile.mkdtemp(suffix='.hulk')

        # TODO generate a name for the mutant

        # transform mutation to diff
        filepath = TODO
        text_original = self.read_file(snapshot_original, filepath)
        text_mutated = self.mutate_text(text_original, mutation)
        diff = difflib.unified_diff(text_original.splitlines(True),
                                    text_mutated.splitlines(True),
                                    filepath,
                                    filepath)
        fn_diff = os.path.join(dir_temp, 'mutant.diff')
        with open(fn_diff, 'w') as f:
            r.write(diff)

        # build the docker file
        fn_dockerfile = os.path.join(dir_temp, 'Dockerfile')
        with open(fn_dockerfile, 'w') as f:
            contents = [
                "FROM {}".format(snapshot_original.image),
                "WORKDIR {}".format(snapshot_original.source_dir),
                "COPY mutant.diff .",
                "RUN patch -p0 < mutant.diff"
            ]
            f.writelines(contents)

        # build bug description
        snapshot_mutated = Bug(name=snapshot_mutated_name,
                               image=docker_image_name,
                               languages=snapshot_original.languages,
                               harness=snapshot_original.harness,
                               compiler=snapshot_original.compiler,
                               files_to_instrument=snapshot_original.files_to_instrument)

        # register with BugZoo

        # build Docker image

        return snapshot_mutated
