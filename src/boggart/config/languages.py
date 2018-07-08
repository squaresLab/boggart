from typing import Iterator, Any, List, FrozenSet, Optional, Dict, Set
import warnings
import os
import logging

from ..core import Language
from ..exceptions import IllegalConfig, LanguageNotDetected
from ..warnings import LanguageOverwriteWarning

logger = logging.getLogger(__name__)

__all__ = ['Languages']


class Languages(object):
    """
    Maintains information about the languages that are supported by Hulk.
    """
    @staticmethod
    def from_defs(defs: List[Any], base: 'Languages' = None) -> 'Languages':
        """
        Loads an operator configuration from a list of definitions taken
        from a configuration file, together with an optionally provided
        parent (overall) configuration.
        """
        logger.debug("Loading languages from definitions: %s", defs)
        config = base if base else Languages()
        for d in defs:
            logger.debug("Loading language from definition: %s", d)
            language = Language.from_dict(d)
            logger.debug("Adding loaded language to configuration: %s",
                         language)
            config = config.add(language)
        logger.debug("Loaded languages from definitions.")
        return config

    def __init__(self,
                 languages: Optional[Dict[str, Language]] = None
                 ) -> None:
        """
        Constructs a collection of lamnguages for a set of languages provided
        in the form a dictionary, indexed by name.
        """
        self.__languages = dict(languages) if languages else {}

    def add(self, language: Language) -> 'Languages':
        """
        Returns a variant of this collection of languages that also includes a
        given language.
        """
        logger.debug("Added language to collection: %s", language)
        endings = set(self.supported_file_endings)

        # if there already exists a language with the given name, produce a
        # warning and remove its file endings from consideration.
        if language.name in self.__languages:
            old_version = self.__languages[language.name]
            msg = "config overwrites existing language definition: {}."
            msg = msg.format(language.name)
            warnings.warn(msg, LanguageOverwriteWarning)
            endings -= set(old_version.file_endings)

        # are the file endings used by this language already in use?
        if set(language.file_endings) & endings:
            logger.error("failed to load language due to an existing language sharing a common file ending.")  # noqa: pycodestyle
            raise IllegalConfig("file ending ambiguity: two or more languages share a common file ending.")  # noqa: pycodestyle

        languages = dict(self.__languages)
        languages[language.name] = language
        logger.debug("Added language to collection: %s", language)
        return Languages(languages)

    def __iter__(self) -> Iterator[Language]:
        """
        Returns an iterator over the languages within this collection.
        """
        yield from self.__languages.values()

    def __getitem__(self, name: str) -> Language:
        """
        Attempts to fetch the definition of the language associated with a
        supplied name.

        Raises:
            KeyError: if no language is found with the given name.
        """
        return self.__languages[name]

    def __contains__(self, name: str) -> bool:
        """
        Provides an alias for `supports`.
        """
        return self.supports(name)

    def __len__(self) -> int:
        """
        Returns the number of languages contained within this collection.
        """
        return len(self.__languages)

    def supports(self, name: str) -> bool:
        """
        Determines whether this colelctions contains a language with a given
        name.
        """
        return name in self.__languages

    @property
    def supported_file_endings(self) -> FrozenSet[str]:
        """
        The set of file endings that are used by languages within this
        collection.
        """
        endings = set()  # type: Set[str]
        for language in self:
            endings.union(language.file_endings)
        return frozenset(endings)

    def detect(self, filename: str) -> Language:
        """
        Attempts to automatically detect the language used by a file based
        on its file ending.

        Returns:
            The language associated with the file ending used by the given
            file.

        Raises:
            LanguageNotDetected: if the language used by the filename could not
                be automatically detected.
        """
        logger.debug("Attempting to detect language used by file: %s",
                     filename)
        _, suffix = os.path.splitext(filename)
        logger.debug("Using suffix of file, '%s': '%s'",
                     filename, suffix)
        for language in self:
            if suffix in language.file_endings:
                logger.debug("Detected language used by file, '%s': %s",
                             filename, language)
                return language
        logger.error("Failed to detect language used by file: %s", filename)
        raise LanguageNotDetected(filename)
