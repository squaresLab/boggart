from typing import Iterable, Any, List, FrozenSet, Set, Optional
from hulk.base import Operator, Language, Transformation
from hulk.exceptions import BadConfigFile, IllegalConfig
from hulk.config.languages import Languages
import yaml


class Config(object):
    @classmethod
    def from_file(cls,
                  filename: str,
                  parent: 'Optional[Config]' = None
                  ) -> 'Config':
        """
        Loads a configuration file from a given file.
        """
        config = parent if parent else Config()

        with open(filename, 'r') as f:
            yml = yaml.load(f)

        if 'version' not in yml:
            raise BadConfigFile("expected 'version' property")

        if yml['version'] != '1.0':
            raise BadConfigFile("unexpected 'version' property; only '1.0' is currently supported.")


        # load the supported operators
        # TODO: ensure that operators are immutable
        for op_dict in yml['operators']:
            op = Language.from_dict(op_dict)
            config = config.with_operator(op)

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

    def with_operator(self, operator: Operator) -> Config:
        """
        Returns a variant of this configuration that adds support for a given
        mutation operator.

        Raises:
            - LanguageNotFound: if at least one language supported by this
                operator has no matching definition within this configuration.
        """
        if operator.name in self.__operators:
            msg = "config overwrites existing operator definition: {}.".format(operator.name)
            warnings.warn(msg, OperatorOverwriteWarning)

        for language in operator.languages:
            if language not in self.__languages:
                raise LanguageNotFound(language)

        operators = dict(self.__operators)
        operators[operator.name] = operator
        return Config(languages=self.__languages,
                      operators=operators)

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
