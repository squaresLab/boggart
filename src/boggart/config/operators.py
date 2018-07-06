from typing import Iterator, Any, List, Optional, Dict
import logging

from .languages import Languages
from ..core import Operator
from ..exceptions import LanguageNotFound

logger = logging.getLogger(__name__)

__all__ = ['Operators']


class Operators(object):
    """
    Maintains information about the mutation operators that are supported
    by Boggart.
    """
    @staticmethod
    def from_defs(defs: List[Any],
                  languages: 'Languages',
                  base: 'Operators' = None
                  ) -> 'Operators':
        """
        Loads an operator configuration from a list of definitions taken
        from a configuration file, together with an optionally provided
        parent (overall) configuration.

        Raises:
            LanguageNotFound: if one of the operators given by the provided
              definitions supports a language that is not contained within
              the given configuration.
        """
        logger.debug("Loading operators from definitions: %s", defs)
        operators = base if base else Operators()
        for d in defs:
            logger.debug("Loading operator from definition: %s", d)
            op = Operator.from_dict(d)
            operators = operators.add(op, languages)
        logger.debug("Loaded operators from definitions.")
        return operators

    def __init__(self,
                 operators: Optional[Dict[str, Operator]] = None
                 ) -> None:
        """
        Constructs a collection of operators for a set of operators provided
        in the form a dictionary, indexed by name.
        """
        self.__operators = dict(operators) if operators else {}

    def add(self, op: Operator, languages: Languages) -> 'Operators':
        """
        Returns a variant of this collection of mutation operators that also
        includes a given mutation operator.

        Params:
            op: the mutation operator that should be added.
            languages: the collection of languages that are supported by a
              particular configuration of Boggart.

        Raises:
            LanguageNotFound: if the given mutation operator supports a
              language that is not contained within the provided collection
              of languages.
        """
        logger.debug("Adding operator to collection: %s", op)
        for supported_language in op.languages:
            if supported_language not in languages:
                logger.error("Failed to add operator, %s, to collection: language not found (%s)",  # noqa: pycodestyle
                             op, supported_language)
                raise LanguageNotFound(supported_language)

        ops = dict(self.__operators)
        ops[op.name] = op
        logger.debug("Added operator to collection: %s", op)
        return Operators(ops)

    def __len__(self) -> int:
        """
        Returns the number of operators contained within this collection.
        """
        return len(self.__operators)

    def __iter__(self) -> Iterator[Operator]:
        """
        An iterator over the operators contained within this collection.
        """
        yield from self.__operators.values()

    def __getitem__(self, name: str) -> Operator:
        """
        Attempts to fetch the definition of the mutation operator associated
        with a given name.

        Raises:
            KeyError: if no mutation operator is found with the given name.
        """
        return self.__operators[name]

    def __contains__(self, name: str) -> bool:
        """
        Determines whether this collection of mutation operators contains one
        with a given name.
        """
        return name in self.__operators
