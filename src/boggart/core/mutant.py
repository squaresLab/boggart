from typing import List, Iterator, Dict, Any
from uuid import UUID

from .mutation import Mutation

__all__ = ['Mutant']


class Mutant(object):
    @staticmethod
    def from_dict(jsn: Any) -> 'Mutant':
        """
        Constructs a mutant description from a dictionary.
        """
        assert isinstance(jsn, dict)

        uuid = UUID(hex=jsn['uuid'])
        base = jsn['base']
        mutations = [Mutation.from_dict(m) for m in jsn['mutations']]

        return Mutant(uuid, base, mutations)

    def __init__(self,
                 uuid: UUID,
                 base: str,
                 mutations: List[Mutation]
                 ) -> None:
        """
        Constructs a new Mutant description.

        Parameters:
            uuid: the UUID for the mutant.
            base: the name of the snapshot that was used to generate the
                mutant.
            mutations: the sequence of mutations that were applied to the
                snapshot.
        """
        self.__uuid = uuid
        self.__base = base
        self.__mutations = mutations

    def __repr__(self) -> str:
        return "Mutant({}, {}, {})".format(self.uuid,
                                           self.base,
                                           repr(self.mutations))

    @property
    def uuid(self) -> UUID:
        """
        The UUID for this mutant.
        """
        return self.__uuid

    @property
    def base(self) -> str:
        """
        The name of the snapshot that was used to generate this mutant.
        """
        return self.__base

    @property
    def snapshot(self) -> str:
        """
        The name of the BugZoo snapshot for this mutant.
        """
        return "boggart:{}".format(self.uuid)

    @property
    def docker_image(self) -> str:
        """
        The name of the Docker image for this mutant.
        """
        return "boggart/{}".format(self.uuid)

    @property
    def mutations(self) -> Iterator[Mutation]:
        """
        Returns an iterator over the mutations that were applied to the
        snapshot in order to generate this mutant.
        """
        return self.__mutations.__iter__()

    def to_dict(self) -> Dict[str, Any]:
        """
        Produces a dictionary-based description of this mutant, ready to be
        serialized as, for instance, YAML or JSON.
        """
        return {
            'uuid': self.__uuid.hex,
            'base': self.__base,
            'mutations': [m.to_dict() for m in self.mutations]
        }
