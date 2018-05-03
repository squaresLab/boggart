from typing import Iterator, Dict

from .api import API
from ..core import Operator


class OperatorCollection(object):
    """
    Provides read-only access to the set of operator supported by a given
    server.
    """
    def __init__(self, api: API) -> None:
        """
        Constructs a new language collection for a given server.

        Parameters:
            api: the low-level client API that should be used to interact
                with the server.
        """
        dict_list = api.get("/operators").json()
        operators = [Operator.from_dict(d) for d in dict_list]
        self.__contents = \
            {op.name: op for op in operators}  # type: Dict[str, Operator]

    def __iter__(self) -> Iterator[Operator]:
        """
        Returns an iterator over the operators within this collection.
        """
        return self.__contents.values().__iter__()

    def __len__(self) -> int:
        """
        Returns a count of the number of operators within this collection.
        """
        return len(self.__contents)

    def __getitem__(self, name: str) -> Operator:
        """
        Returns the operator associated with a given name.

        Raises:
            KeyError: if no operator is found with the given name.
        """
        return self.__contents[name]
