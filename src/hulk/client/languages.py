from typing import Iterable, Dict

from ..base import Language


class LanguageCollection(object):
    """
    Provides read-only access to the set of languages supported by a given
    server.
    """
    def __init__(self, client: 'Client') -> None:
        """
        Constructs a new language collection for a given server.

        Parameters:
            client: the client object that should be used to communicate with
                the server.
        """
        language_dict_list = client._get("/languages").json()
        languages = [Language.from_dict(d) for d in language_dict_list]
        self.__contents = \
            {lang.name: lang for lang in languages} # type: Dict[str, Language]

    def __iter__(self) -> Iterable[Language]:
        """
        Returns an iterator over the languages within this collection.
        """
        return self.__contents.values().__iter__()

    def __len__(self) -> int:
        """
        Returns a count of the number of languages within this collection.
        """
        return len(self.__contents)

    def __getitem__(self, name: str) -> Language:
        """
        Returns the language associated with a given name.

        TODO: should we raise a KeyError or LanguageNotFound exception?

        Raises:
            KeyError: if no language is found with the given name.
        """
        return self.__contents[name]
