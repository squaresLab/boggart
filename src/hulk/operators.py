from typing import List, Tuple, Dict, Optional
from hulk.exceptions import *
from hulk.base import Operator, Transformation, Language

# A registry of operators, stored by their names
__OPERATORS : Dict[str, Operator] = {}


# TODO: Load from YAML files!
def register(name: str,
             languages: List[Language],
             transformations: List[Tuple[str, str]]) -> None:
    """
    Constructs and registers a mutation operator with Hulk.

    Params:
        name: The unique name of the mutation operator.
        languages: A list of languages supported by the mutation operator.
        transformations: A list of transformations that implement this
            mutation operator, given as plaintext Rooibos (match, rewrite)
            pairs.

    Raises:
        OperatorNameAlreadyExists: if another operator is already registered
            under the provided name.
    """
    if name in __OPERATORS:
        raise OperatorNameAlreadyExists(name)

    transformations = \
        [Transformation(match, rewrite) for (match, rewrite) in transformations]
    op = Operator(name, languages, transformations)
    __OPERATORS[name] = op

    return op


def lookup(name: str) -> Optional[Operator]:
    """
    Attempts to retrieve the mutation operator associated with a given name.
    If there is no mutation operator registered with that name, `None` will be
    returned instead.
    """
    return __OPERATORS.get(name, None)


register("NEGATE_IF_CONDITION-CSTYLE",
         [Language.C, Language.CXX, Language.JAVA],
         [('if (:[1])', 'if (!(:[1]))')])
