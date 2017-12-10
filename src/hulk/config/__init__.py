from typing import Optional
from hulk.exceptions import BadConfigFile
from hulk.config.languages import Languages
from hulk.config.operators import Operators
import yaml


class Configuration(object):
    @classmethod
    def from_file(cls,
                  filename: str,
                  parent: 'Optional[Config]' = None
                  ) -> 'Configuration':
        """
        Loads a configuration file from a given file.
        """
        config = parent if parent else Configuration()
        languages = parent.languages
        operators = parent.operators

        with open(filename, 'r') as f:
            yml = yaml.load(f)

        if 'version' not in yml:
            raise BadConfigFile("expected 'version' property")
        if yml['version'] != '1.0':
            raise BadConfigFile("unexpected 'version' property; only '1.0' is currently supported.")

        # update the languages provided by this configuration
        languages = Languages.from_defs(yml.get('languages', []), config)
        config = Configuration(languages, operators)

        # update the operators provided by this configuration
        operators = Operators.from_defs(yml.get('operators', []), config)
        config = Configuration(languages, operators)

        return config

    def __init__(self,
                 languages: Optional[Languages] = None,
                 operators: Optional[Operators] = None
                 ):
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
    def operators(self) -> ConfigOperators:
        """
        The mutation operators defined by this configuration.
        """
        return self.__operators


class SystemConfig(Config):
    pass

class UserConfig(Config):
    pass
