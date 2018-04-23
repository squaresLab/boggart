from typing import List, Iterator
from uuid import UUID

from .mutation import Mutation

__all__ = ['Mutant']


class Mutant(object):
    def __init__(self,
                 uuid: UUID,
                 snapshot: str,
                 mutations: List[Mutation]
                 ) -> None:
        """
        Constructs a new Mutant description.

        Parameters:
            uuid: the UUID for the mutant.
            snapshot: the name of the snapshot that was used to generate the
                mutant.
            mutations: the sequence of mutations that were applied to the
                snapshot.
        """
        self.__uuid = uuid
        self.__snapshot = snapshot
        self.__mutations = mutations

    @property
    def uuid(self) -> UUID:
        """
        The UUID for this mutant.
        """
        return self.__uuid

    @property
    def snapshot(self) -> str:
        """
        The name of the snapshot that was used to generate this mutant.
        """
        return self.__snapshot

    @property
    def mutations(self) -> Iterator[Mutation]:
        """
        Returns an iterator over the mutations that were applied to the
        snapshot in order to generate this mutant.
        """
        return self.__mutations.__iter__()
