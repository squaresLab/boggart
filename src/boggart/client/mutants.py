__all__ = ['MutantCollection']

from typing import Iterator
from uuid import UUID

from .api import API
from ..core import Mutant


class MutantCollection(object):
    """
    Provides access to the mutants that are registered with a given server.
    """
    def __init__(self, api: API) -> None:
        """
        Constructs a new mutant collection for a given server.

        Parameters:
            api: the low-level client API that should be used to interact
                with the server.
        """
        self.__api = api

    def clear(self) -> None:
        """
        Destroys all registered mutants.
        """
        r = self.__api.delete("/mutants")
        if r.status_code != 204:
            self.__api.handle_erroneous_response(r)

    def __iter__(self) -> Iterator[UUID]:
        """
        Returns an iterator over the UUIDs of mutants within this collection.
        """
        uuid_str_list = self.__api.get("/mutants").json()
        uuid_list = [UUID(hex=s) for s in uuid_str_list]
        yield from uuid_list

    def __len__(self) -> int:
        """
        Returns a count of the number of mutants in this collection.
        """
        return len(list(self))

    def __delitem__(self, uuid: UUID) -> None:
        """
        Destroys the mutant associated with a given UUID.

        Raises:
            KeyError: if no mutant is found with the given UUID.
        """
        r = self.__api.delete('mutants/{}'.format(uuid.hex))
        if r.status_code == 204:
            return
        if r.status_code == 404:
            msg = "no mutant found with given UUID: {}"
            msg = msg.format(uuid.hex)
            raise KeyError(msg)
        self.__api.handle_erroneous_response(r)

    def __getitem__(self, uuid: UUID) -> Mutant:
        """
        Returns the mutant associated with a given UUID.

        Raises:
            KeyError: if no mutant is found with the given UUID.
        """
        r = self.__api.get('mutants/{}'.format(uuid.hex))
        if r.status_code == 200:
            return Mutant.from_dict(r.json())
        if r.status_code == 404:
            msg = "no mutant found with given UUID: {}"
            msg = msg.format(uuid.hex)
            raise KeyError(msg)
        self.__api.handle_erroneous_response(r)
