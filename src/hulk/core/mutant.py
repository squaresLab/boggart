from .mutation import Mutation

__all__ = ['Mutant']


class Mutant(object):
    def __init__(self,
                 snapshot: str
                 ) -> None:
        self.__snapshot = snapshot

    @property
    def snapshot(self) -> str:
        """
        The name of the snapshot that was used to generate this mutant.
        """
        return self.__snapshot
