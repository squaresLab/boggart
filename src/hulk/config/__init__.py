from typing import Iterable, Any, List, FrozenSet, Set, Optional
from hulk.base import Operator, Language, Transformation
from hulk.exceptions import BadConfigFile, IllegalConfig
import copy
import yaml


class Languages(object):
    """
    Maintains information about the languages that are supported by Hulk.
    """
    @staticmethod
    def from_dict(defs: List[Any],
                  parent: 'Optional[Languages]' = None
                  ) -> 'Languages':
        """
        Loads a language configuration from a list of definitions taken from
        a configuration file, and an optionally provided parent language
        configuration.
        """
        config = parent if parent else Languages()
        for d in defs:
            language = Language.from_dict(d)
            config = config.add(language)
        return config

    def __init__(self, languages: Optional[Dict[Languages]] = None):
        self.__languages = dict(languages) if languages else {}

    def add(self, language: Language) -> 'Languages':
        """
        Returns a variant of this configuration that adds support for a given
        language.
        """
        endings = set(self.supported_file_endings)

        # if there already exists a language with the given name, produce a
        # warning and remove its file endings from consideration.
        if language.name in self.__languages:
            old_version = self.__languages[language.name]
            msg = "config overwrites existing language definition: {}.".format(language.name)
            warnings.warn(msg, LanguageOverwriteWarning)
            endings -= set(old_version.file_endings)

        # are the file endings used by this language already in use?
        if language.file_endings & supported_file_endings:
            raise IllegalConfigError("file ending ambiguity: two or more languages share a common file ending.")

        languages = dict(self.__languages)
        languages[language.name] = language
        return Languages(languages)

    def __iter__(self) -> Iterable[Language]:
        """
        An iterator over the languages supported by this configuration.
        """
        for name in self.__languages:
            yield self.__languages[name]

    def __item__(self, name) -> Language:
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

    def supports(self, name: str) -> bool:
        """
        Determines whether this configuration supports a language with a given
        name.
        """
        return name in self.__languages

    @property
    def supported_file_endings(self) -> FrozenSet[str]:
        """
        The set of file endings that are supported by language autodetection
        using this configuration.
        """
        endings = set()
        for language in self:
            endings += language.file_endings
        return frozenset(endings)


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

    def __init__(self, languages=None, operators=None):
        """
        Constructs a configuration that supports a given set of operators and
        languages, each provided as dictionaries, respectively.
        """
        if not languages:
            languages = {}
        if not operators:
            operators = {}

        self.__languages: Dict[str, Language] = dict(languages)
        self.__operators: Dict[str, Operator] = dict(operators)

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
