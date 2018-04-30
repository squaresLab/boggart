from typing import Optional

import yaml

from .languages import Languages
from .operators import Operators
from ..exceptions import BadConfigFile


class Configuration(object):
    @staticmethod
    def from_file(filename: str,
                  parent: Optional['Configuration'] = None
                  ) -> 'Configuration':
        """
        Loads a configuration file from a given file.
        """
        config = parent if parent else Configuration()
        languages = config.languages
        operators = config.operators

        with open(filename, 'r') as f:
            yml = yaml.load(f)

        if 'version' not in yml:
            raise BadConfigFile("expected 'version' property")
        if yml['version'] != '1.0':
            raise BadConfigFile("unexpected 'version' property; only '1.0' is currently supported.")

        # update the languages and operators provided by this configuration
        languages = \
            Languages.from_defs(yml.get('languages', []), languages)
        operators = \
            Operators.from_defs(yml.get('operators', []),
                                languages=languages,
                                base=operators)
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
