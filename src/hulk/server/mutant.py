from typing import List

from bugzoo.client import Client as BugZooClient

from ..core import Mutant


class MutantManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient
                 ) -> None:
        self.__mutants = [] # type: List[Mutant]
        self.__bugzoo = client_bugzoo
