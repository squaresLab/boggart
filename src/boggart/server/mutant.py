# TODO mutants are killed when the server is killed
from typing import List, Iterator, Dict
from uuid import UUID, uuid4
import tempfile
import logging

from bugzoo.core.bug import Bug
from bugzoo.core.patch import Patch
from bugzoo.client import Client as BugZooClient
from bugzoo.exceptions import BugZooException
from rooibos import Client as RooibosClient

from .sourcefile import SourceFileManager
from ..config.operators import Operators as OperatorManager
from ..core import Mutant, Mutation, Replacement
from ..exceptions import BuildFailure

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

    def clear(self) -> None:
        """
        Destroys all mutants that are registered with this manager.
        """
        logger.info("destroying all registered mutants")
        try:
            uuids = list(self)
            for uuid in uuids:
                del self[uuid]
        except Exception:
            logger.exception("failed to destroy all registered mutants")
            raise
        logger.info("destroyed all registered mutants")

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

        Raises:
            BuildFailure: if the mutant failed to build.
        """
        logger.info("generating mutant of snapshot '%s' by applying mutations: %s",  # noqa: pycodestyle
                    snapshot.name,
                    ', '.join([repr(m) for m in mutations]))
        bz = self.__bugzoo
        assert len(mutations) <= 1, \
            "higher-order mutation is currently unsupported"

        # NOTE this is *incredibly* unlikely to conflict
        logging.debug("generating UUID for mutant...")
        uuid = uuid4()
        logger.debug("generated UUID for mutant: %s", uuid.hex)
        try:
            assert uuid not in self.__mutants, "UUID already in use."
        except AssertionError:
            logger.exception("automatically generated UUID is already in use: %s",  # noqa: pycodestyle
                             uuid)
            raise
        logger.debug("constructing mutation description...")
        mutant = Mutant(uuid, snapshot.name, mutations)
        logger.debug("constructed mutant description: %s", mutant)

        # generate a diff for the mutant
        logger.debug("generating a unified diff for mutant")
        diff = \
            self.__sources.mutations_to_diff(snapshot, list(mutant.mutations))
        logger.debug("generated unified diff for mutant")

        # generate the Docker image on the BugZoo server
        logger.debug("provisioning container to persist mutant as a snapshot")
        container = bz.containers.provision(snapshot)
        logger.debug("provisioned container [%s] for mutant [%s].",
                     container.uid, mutant.uuid.hex)
        try:
            logger.debug("applying mutation patch to original source code.")
            bz.containers.patch(container, diff)
            logger.debug("applied mutation patch to original source code.")
            try:
                logger.debug("attempting to build source code for mutant.")
                outcome = bz.containers.build(container)
                logger.debug("built source code for mutant.")
            except BugZooException:
                raise BuildFailure
            bz.containers.persist(container, mutant.docker_image)
            logger.debug("persisted mutant to Docker image")
        finally:
            del bz.containers[container.uid]
            logger.debug("destroyed temporary container [%s] for mutant [%s].",
                         container.uid, mutant.uuid.hex)

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
