from typing import Optional, Tuple, Dict, Iterator, List
import os
import logging

import rooibos
from bugzoo.client import Client as BugZooClient
from bugzoo.core.bug import Bug
from bugzoo.core.fileline import FileLine
from rooibos import Client as RooibosClient

from .mutant import MutantManager
from .sourcefile import SourceFileManager
from ..exceptions import *
from ..core import Language, Mutation, Operator, Mutant, FileLocationRange, \
                   Location, LocationRange
from ..config import Configuration, Languages, Operators

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

__all__ = ['Installation']


class Installation(object):
    """
    Used to manage a local installation of boggart.
    """
    @classmethod
    def default_user_config_path(cls) -> str:
        """
        The default path to the user-level configuration file.
        """
        if 'BOGGART_USER_CONFIG_PATH' in os.environ:
            return os.environ['BOGGART_USER_CONFIG_PATH']

        home = os.environ['HOME']
        default_path = os.path.join(home, '.boggart.yml')
        return default_path

    @classmethod
    def sys_config_path(cls) -> str:
        """
        The path to the system-level configuration file.
        """
        src_dir = os.path.dirname(__file__)
        cfg_fn = os.path.join(src_dir, '../config/sys.boggart.yml')
        return cfg_fn

    @classmethod
    def load(cls,
             client_bugzoo: BugZooClient,
             client_rooibos: RooibosClient,
             *,
             user_config_path: Optional[str] = None
             ) -> 'Installation':
        """
        Loads a boggart installation.

        Parameters:
            client_bugzoo: A connection to the BugZoo server that should be
                used by this boggart server.
            config_filepath: The path to the user configuration file for
                boggart. If left unspecified,
                `Installation.default_user_config_path` will be used instead.
        """
        logger.info("loading boggart installation")
        if not user_config_path:
            user_config_path = Installation.default_user_config_path()
            logger.info("no user config path provided -- using default user config path, '%s', instead",  # noqa: pycodestyle
                        user_config_path)

        logger.info("loading system configuration from file: %s",
                    cls.sys_config_path())
        system_cfg = Configuration.from_file(Installation.sys_config_path())
        logger.info("loading system configuration")

        if not os.path.isfile(user_config_path):
            logger.info("no user configuration file found at %s",
                        user_config_path)
            return Installation(system_cfg, client_bugzoo, client_rooibos)

        logger.info("loading user configuration from file: %s",
                    user_config_path)
        user_cfg = Configuration.from_file(user_config_path, system_cfg)
        logger.info("loaded user configuration from file: %s",
                    user_config_path)
        return Installation(user_cfg, client_bugzoo, client_rooibos)

    def __init__(self,
                 config: Configuration,
                 client_bugzoo: BugZooClient,
                 client_rooibos: RooibosClient
                 ) -> None:
        self.__config = config
        self.__bugzoo = client_bugzoo
        self.__rooibos = client_rooibos
        self.__sources = SourceFileManager(client_bugzoo,
                                           client_rooibos,
                                           config.operators)
        self.__mutants = MutantManager(client_bugzoo,
                                       client_rooibos,
                                       config.operators,
                                       self.__sources)

    @property
    def bugzoo(self) -> BugZooClient:
        """
        A connection to the BugZoo server to which this boggart server is
        attached.
        """
        return self.__bugzoo

    @property
    def rooibos(self) -> RooibosClient:
        """
        A connection to the Rooibos server to which this boggart server is
        attached.
        """
        return self.__rooibos

    @property
    def sources(self) -> SourceFileManager:
        """
        Provides access to the contents and caches the contents of source code
        belonging to BugZoo snapshots.
        """
        return self.__sources

    @property
    def languages(self) -> Languages:
        """
        The languages registered with this installation.
        """
        return self.__config.languages

    @property
    def operators(self) -> Operators:
        """
        The mutation operators registered with this installation.
        """
        return self.__config.operators

    @property
    def mutants(self) -> MutantManager:
        """
        The active mutants that are registered with this installation.
        """
        return self.__mutants

    def mutations(self,
                  snapshot: Bug,
                  filepath: str,
                  *,
                  language: Language = None,
                  operators: List[Operator] = None,
                  restrict_to_lines: Optional[List[int]] = None
                  ) -> Iterator[Mutation]:
        """
        Computes all of the first-order mutations that can be applied to a
        given file belonging to a specified BugZoo snapshot.

        Returns:
            an iterator over the possible mutations.

        Raises:
            LanguageNotDetected: if no language is specified and the language
                used by the file cannot be automatically determined.
            FileNotFound: if the given file is not found inside the snapshot.
        """
        logger.info("Computing mutations to file, '%s', in snapshot, '%s'",
                    filepath,
                    snapshot.name)
        sources = self.sources

        def match_to_mutation(op_name: str,
                              transformation_index: int,
                              match: rooibos.Match
                              ) -> Mutation:
            logger.debug("Transforming template match to mutation: %s", match)
            start = Location(match.location.start.line,
                             match.location.start.col)
            stop = Location(match.location.stop.line,
                            match.location.stop.col)
            location = FileLocationRange(filepath, LocationRange(start, stop))

            args = {}  # type: Dict[str, str]
            for term in match.environment:
                value = match.environment[term].fragment
                args[term] = value

            mut = Mutation(op_name, transformation_index, location, args)
            logger.debug("Transformed match, %s, to mutation: %s", match, mut)
            return mut

        if operators is None:
            logger.info("No mutation operators specified -- attempting to use all available operators.")  # noqa: pycodestyle
            operators = list(self.operators)
        logger.info("Using mutation operators: %s",
                    ', '.join([op.name for op in operators]))

        logger.debug("Obtaining source code for specified file: %s", filepath)
        text = sources.read_file(snapshot, filepath)
        logger.debug("Obtained source code for file %s", filepath)

        if language is None:
            logger.debug("Attempting to automatically detect language used by file: %s",  # noqa: pycodestyle
                         filepath)
            language = self.languages.detect(filepath)
        logger.debug("Treating '%s' as a %s file.", filepath, language.name)

        for operator in operators:
            logger.debug("Using operator to find mutations: %s", operator.name)
            for (idx, transformation) in enumerate(operator.transformations):
                logger.debug("Finding all instances of match template in source code: %s",  # noqa: pycodestyle
                             transformation.match)
                for match in self.rooibos.matches(text, transformation.match):
                    line = match.location.start.line
                    if restrict_to_lines and line not in restrict_to_lines:
                        continue

                    # FIXME this is a horrible hack
                    offset_start = \
                        sources.line_col_to_offset(snapshot,
                                                   filepath,
                                                   match.location.start.line,
                                                   match.location.start.col)
                    offset_stop = \
                        sources.line_col_to_offset(snapshot,
                                                   filepath,
                                                   match.location.stop.line,
                                                   match.location.stop.col)
                    content_match = text[offset_start:offset_stop]

                    logger.debug("Found possible template match:\n%s",
                                 content_match)
                    is_sat = \
                        transformation.satisfies_constraints(match,
                                                             text,
                                                             offset_start,
                                                             offset_stop)
                    if is_sat:
                        yield match_to_mutation(operator.name, idx, match)
                    else:
                        logger.debug("Template match doesn't satisfy transformation constraints: %s", match)  # noqa: pycodestyle
