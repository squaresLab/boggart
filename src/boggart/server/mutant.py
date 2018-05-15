# TODO mutants are killed when the server is killed
from typing import List, Iterator, Dict
from uuid import UUID, uuid4
from difflib import unified_diff
import tempfile
import logging

from bugzoo.core.bug import Bug
from bugzoo.core.patch import Patch
from bugzoo.client import Client as BugZooClient
from rooibos import Client as RooibosClient

from .sourcefile import SourceFileManager
from ..config.operators import Operators as OperatorManager
from ..core import Mutant, Mutation, Replacement

logger = logging.getLogger(__name__)


class MutantManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient,
                 client_rooibos: RooibosClient,
                 operators: OperatorManager,
                 sources: SourceFileManager
                 ) -> None:
        self.__mutants = {}  # type: Dict[UUID, Mutant]
        self.__bugzoo = client_bugzoo
        self.__rooibos = client_rooibos
        self.__operators = operators
        self.__sources = sources

    def __iter__(self) -> Iterator[UUID]:
        """
        Returns an iterator over the UUIDs of the mutants that are currently
        registered with this server.
        """
        yield from self.__mutants.keys()

    def __getitem__(self, uuid: UUID) -> Mutant:
        """
        Retrieves a registered mutant by its UUID.

        Raises:
            KeyError: if no mutant is registered under the given UUID.
        """
        return self.__mutants[uuid]

    def __delitem__(self, uuid: UUID) -> None:
        """
        Deletes a registered mutant and destroys its allocated resources.

        Raises:
            KeyError: if no mutant is registered under the given UUID.
        """
        logger.info("Attempting to destroy mutant with UUID: %s", uuid.hex)
        try:
            mutant = self[uuid]
        except KeyError:
            logger.exception("Failed to find mutant with UUID: %s", uuid.hex)
            raise
        try:
            self.__bugzoo.docker.delete_image(mutant.docker_image)
        except Exception:
            logger.exception("Failed to destroy docker image (%s) for mutant: %s",  # noqa: pycodestyle
                             mutant.docker_image,
                             mutant)
        # FIXME deregister the BugZoo snapshot
        del self.__mutants[uuid]

    def __len__(self) -> int:
        """
        Returns a count of the number of registered mutants.
            """
        return len(self.__mutants)

    def generate(self, snapshot: Bug, mutations: List[Mutation]) -> Mutant:
        """
        Generates a mutant by applying a given set of mutations to a BugZoo
        snapshot.

        Parameters:
            snapshot: the BugZoo snapshot to mutate.
            mutations: the mutations to apply to the snapshot.

        Returns:
            a description of the generated mutant.
        """
        logger.info("Generating mutant of snapshot '%s' by applying mutations: %s",  # noqa: pycodestyle
                    snapshot.name,
                    ', '.join([repr(m) for m in mutations]))
        bz = self.__bugzoo
        assert len(mutations) <= 1, \
            "higher-order mutation is currently unsupported"

        # NOTE this is *incredibly* unlikely to conflict
        logging.debug("Generating UUID for mutant...")
        uuid = uuid4()
        logger.debug("Generated UUID for mutant: %s", uuid.hex)
        try:
            assert uuid not in self.__mutants, "UUID already in use."
        except AssertionError:
            logger.exception("Automatically generated UUID is already in use: %s",  # noqa: pycodestyle
                             uuid)
            raise
        logger.debug("Constructing mutation description...")
        mutant = Mutant(uuid, snapshot.name, mutations)
        logger.debug("Constructed mutant description: %s", mutant)

        # group mutations by file
        logger.debug("Grouping mutations by file")
        file_mutations = {}  # type: Dict[str, List[Mutation]]
        for mutation in mutant.mutations:
            location = mutation.location
            filename = location.filename

            if filename not in file_mutations:
                file_mutations[filename] = []
            file_mutations[filename].append(mutation)
        logger.debug("Grouped mutations by file: %s", file_mutations)

        # transform each mutation into a replacement and group by file
        logger.debug("Transforming mutations into replacements")
        replacements_in_file = {}  # type: Dict[str, List[Replacement]]
        for mutation in mutant.mutations:
            location = mutation.location
            filename = location.filename
            if filename not in replacements_in_file:
                replacements_in_file[filename] = []

            operator = self.__operators[mutation.operator]
            transformation = \
                operator.transformations[mutation.transformation_index]
            text_mutated = self.__rooibos.substitute(transformation.rewrite,
                                                     mutation.arguments)

            replacement = Replacement(location, text_mutated)
            logger.info("Transformed mutation, %s, to replacement: %s",
                        mutation,
                        replacement)
            replacements_in_file[filename].append(replacement)
        logger.debug("Transformed mutations to replacements: %s",
                     replacements_in_file)

        # transform the replacements to a diff
        logger.debug("Transforming replacements to diff")
        file_diffs = []  # type: List[str]
        for filename in replacements_in_file:
            original = self.__sources.read_file(snapshot, filename)
            mutated = self.__sources.apply(snapshot,
                                           filename,
                                           replacements_in_file[filename])
            diff = ''.join(unified_diff(original.splitlines(True),
                                        mutated.splitlines(True),
                                        filename,
                                        filename))
            logger.debug("Transformed replacements to file to diff:\n%s",
                         diff)
            file_diffs.append(diff)
        diff_s = '\n'.join(file_diffs)
        logger.info("Transformed mutations to diff:\n%s", diff_s)
        mutant_diff = Patch.from_unidiff('\n'.join(file_diffs))

        # generate the Docker image on the BugZoo server
        logger.debug("Provisioning container to persist mutant as a snapshot")
        container = bz.containers.provision(snapshot)
        logger.debug("Provisioned container, %s, for mutant, %s",
                     container.uid,
                     mutant.uuid.hex)
        try:
            logger.debug("Applying mutation patch to original source code.")
            bz.containers.patch(container, diff)
            logger.debug("Applied mutation patch to original source code.")
            bz.containers.persist(container, mutant.docker_image)
        finally:
            del bz.containers[container.uid]
            logger.debug("Destroyed temporary container, %s, for mutant, %s",
                         container.uid,
                         mutant.uuid.hex)

        # build and register a BugZoo snapshot
        files_to_instrument = snapshot.files_to_instrument
        snapshot_mutated = Bug(name=mutant.snapshot,
                               image=mutant.docker_image,
                               program=snapshot.program,
                               dataset=None,
                               source=None,
                               source_dir=snapshot.source_dir,
                               languages=snapshot.languages,
                               harness=snapshot.harness,
                               compiler=snapshot.compiler,
                               files_to_instrument=files_to_instrument)
        logger.debug("Registering snapshot for mutant with BugZoo: %s",
                     mutant.uuid.hex)
        bz.bugs.register(snapshot_mutated)
        logger.debug("Registered snapshot for mutant with BugZoo: %s",
                     mutant.uuid.hex)

        # track the mutant
        logger.debug("Registering mutant with UUID '%s': %s",
                     mutant.uuid.hex,
                     mutant)
        self.__mutants[mutant.uuid] = mutant
        logger.debug("Registered mutant with UUID '%s'", mutant.uuid.hex)
        logger.info("Generated mutant: %s", mutant)
        return mutant
