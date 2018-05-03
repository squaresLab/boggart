from typing import Iterator, Dict

from .api import API
from ..core import Language

__all__ = ['LanguageCollection']


class LanguageCollection(object):
    """
    Provides read-only access to the set of languages supported by a given
    server.
    """
    def __init__(self, api: API) -> None:
        """
        Constructs a new language collection for a given server.

        Parameters:
            api: the low-level client API that should be used to interact
                with the server.
        """
        language_dict_list = api.get("/languages").json()
        languages = [Language.from_dict(d) for d in language_dict_list]
        self.__contents = \
            {lang.name: lang for lang in languages}  # type: Dict[str, Language]  # noqa: pycodestyle

    def __iter__(self) -> Iterator[Language]:
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

        Raises:
            KeyError: if no language is found with the given name.
        """
        return self.__contents[name]
