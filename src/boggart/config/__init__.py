from typing import Optional
import logging

import yaml

from .languages import Languages
from .operators import Operators
from ..exceptions import BadConfigFile

logger = logging.getLogger(__name__)

__all__ = ['Configuration']


class Configuration(object):
    @staticmethod
    def from_file(filename: str,
                  parent: Optional['Configuration'] = None
                  ) -> 'Configuration':
        """
        Loads a configuration file from a given file.
        """
        logger.debug("Loading configuration from file: %s", filename)
        config = parent if parent else Configuration()
        logger.debug("Using parent configuration: %s", config)
        languages = config.languages
        operators = config.operators

        logger.debug("Attempting to read contents of config file: %s",
                     filename)
        with open(filename, 'r') as f:
            yml = yaml.load(f)
        logger.debug("Read YAML contents of config file: %s",
                     filename)

        if 'version' not in yml:
            logger.error("Bad configuration file: missing 'version' property.")
            raise BadConfigFile("expected 'version' property")
        if yml['version'] != '1.0':
            logger.error("Bad configuration file: unsupported version.")
            raise BadConfigFile("unexpected 'version' property; only '1.0' is currently supported.")  # noqa: pycodestyle

        # update the languages and operators provided by this configuration
        logger.debug("Loading languages from config file.")
        languages = \
            Languages.from_defs(yml.get('languages', []), languages)
        logger.debug("Loaded languages from config file.")
        logger.debug("Loading operators from config file.")
        operators = \
            Operators.from_defs(yml.get('operators', []),
                                languages=languages,
                                base=operators)
        logger.debug("Loaded operators from config file.")
        logger.debug("Loaded configuration from file: %s", filename)
        return Configuration(languages, operators)

    def __init__(self,
                 languages: Optional[Languages] = None,
                 operators: Optional[Operators] = None
                 ) -> None:
        """
        Constructs a configuration that supports a given set of operators and
        languages.
        """
        self.__languages = languages if languages else Languages()
        self.__operators = operators if operators else Operators()

    @property
    def languages(self) -> Languages:
        """
        The languages defined by this configuration.
        """
        return self.__languages

    @property
    def operators(self) -> Operators:
        """
        The mutation operators defined by this configuration.
        """
        return self.__operators
