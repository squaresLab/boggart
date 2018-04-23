from typing import List, Iterator, Dict
from uuid import UUID, uuid4

from bugzoo.core.bug import Bug
from bugzoo.client import Client as BugZooClient

from ..core import Mutant, Mutation


class MutantManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient
                 ) -> None:
        self.__mutants = [] # type: Dict[UUID, Mutant]
        self.__bugzoo = client_bugzoo

    @property
    def bugzoo(self) -> BugZooClient:
        """
        Provides a connection to a BugZoo server.
        WARNING: Currently assumed to be running on the same machine.
        """
        return self.__bugzoo

    def __iter__(self) -> Iterator[UUID]:
        """
        Returns an iterator over the UUIDs of the mutants that are currently
        registered with this server.
        """
        yield from self.__mutants.keys()

    def __getitem__(self, uuid: UUID) -> Mutant:
        """
        Retrieves a registered mutant by its UUID.

        Raises:
            KeyError: if no mutant is registered under the given UUID.
        """
        return self.__mutants[uuid]

    def __delitem__(self, uuid: UUID) -> None:
        """
        Deletes a registered mutant and destroys its allocated resources.

        Raises:
            KeyError: if no mutant is registered under the given UUID.
        """
        del self.__mutants[uuid]

    def __len__(self) -> int:
        """
        Returns a count of the number of registered mutants.
        """
        return len(self.__mutants)

    def generate(self, snapshot: Bug, mutations: List[Mutation]) -> Mutant:
        # FIXME this is *incredibly* unlikely to conflict
        uuid = uuid4()
        assert uuid not in self.__mutants, "UUID already in use."

        mutant = Mutant(uuid, snapshot.name, mutations)

        # obtain a diff for the mutant -- save to disk

        # construct files for the mutant
        # - Dockerfile

        # register with BugZoo
        # - attempt to build image

        return mutant
