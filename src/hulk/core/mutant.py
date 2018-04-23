from typing import List, Iterator

from .mutation import Mutation

__all__ = ['Mutant']


class Mutant(object):
    def __init__(self,
                 snapshot: str,
                 mutations: List[Mutation]
                 ) -> None:
        """
        Constructs a new Mutant description.

        Parameters:
            snapshot: the name of the snapshot that was used to generate the
                mutant.
            mutations: the sequence of mutations that were applied to the
                snapshot.
        """
        self.__snapshot = snapshot
        self.__mutations = mutations

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
