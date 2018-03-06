from typing import Iterable, Dict
from ..base import Operator


class OperatorCollection(object):
    """
    Provides read-only access to the set of operator supported by a given
    server.
    """
    def __init__(self, client: 'Client'):
        """
        Constructs a new language collection for a given server.

        Parameters:
            client: the client object that should be used to communicate with
                the server.
        """
        dict_list = client._get("/operators").json()
        operators = [Operator.from_dict(d) for d in dict_list]
        self.__contents: Dict[str, Operator] = \
            {op.name: op for op in operators}

    def __iter__(self) -> Iterable[Operator]:
        """
        Returns an iterator over the operators within this collection.
        """
        for language in self.__contents.values():
            yield language

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
