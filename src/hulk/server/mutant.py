from typing import List, Iterator, Dict
from uuid import UUID

from bugzoo.client import Client as BugZooClient

from ..core import Mutant


class MutantManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient
                 ) -> None:
        self.__mutants = [] # type: Dict[UUID, Mutant]
        self.__bugzoo = client_bugzoo

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

    def __len__(self) -> int:
        """
        Returns a count of the number of registered mutants.
        """
        return len(self.__mutants)
