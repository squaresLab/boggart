# TODO mutants are killed when the server is killed
from typing import List, Iterator, Dict
from uuid import UUID, uuid4
import tempfile

from bugzoo.core.bug import Bug
from bugzoo.client import Client as BugZooClient

from .sourcefile import SourceFileManager
from ..config.operators import Operators as OperatorManager
from ..core import Mutant, Mutation, Replacement


# FIXME implement via rooibos.rewrite
def REWRITER(template: str, arguments: Dict[str, str]) -> str:
    return template


class MutantManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient,
                 operators: OperatorManager,
                 sources: SourceFileManager
                 ) -> None:
        self.__mutants = [] # type: Dict[UUID, Mutant]
        self.__bugzoo = client_bugzoo
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
        del self.__mutants[uuid]

    def __len__(self) -> int:
        """
        Returns a count of the number of registered mutants.
            """
        return len(self.__mutants)

    def generate(self, snapshot: Bug, mutations: List[Mutation]) -> Mutant:
        bz = self.__bugzoo
        assert len(mutations) <= 1, "higher-order mutation is currently unsupported"

        # NOTE this is *incredibly* unlikely to conflict
        uuid = uuid4()
        assert uuid not in self.__mutants, "UUID already in use."

        # determine the name of the Docker image for this mutant
        docker_image = "hulk:{}".format(uuid.hex)
        mutant_snapshot_name = docker_image

        # group mutations by file
        file_mutations = [] # type: Dict[str, List[Mutation]]
        for mutation in mutant.mutations:
            location = mutation.location
            filename = location.filename

            if filename not in file_mutations:
                file_mutations[filename] = []
            file_mutations[filename].append(mutation)

        # transform each mutation into a replacement and group by file
        replacements_in_file = {} # type: Dict[str, List[Replacement]]
        for mutation in mutant.mutations:
            location = mutation.location
            filename = location.filename
            if filename not in replacements_in_file:
                replacements_in_file[filename] = []

            operator = self.__operators[mutation.operator]
            transformation = operator.transformations[mutation.transformation_index]
            text_mutated = REWRITER(transformation.rewrite, mutation.arguments)

            replacement = Replacement(location, text_mutated)
            replacements_in_file[filename].append(replacement)

        # compute the mutated contents of each affected file
        mutated_files = {} # type: Dict[str, str]
        for filename in replacements_in_file:
            mutated_files[filename] = \
                self.__sources.apply(snapshot,
                                     filename,
                                     replacements_in_file[filename])

        # TODO generate a diff

        # generate the Docker image on the BugZoo server
        container = bz.containers.provision(snapshot)
        try:
            bz.containers.patch(diff)
            bz.containers.persist(snapshot, docker_image)
        finally:
            del bz.containers[container.uid]

        # build snapshot
        snapshot_mutated = Bug(name=mutant_snapshot_name,
                               image=docker_image,
                               languages=snapshot_original.languages,
                               harness=snapshot_original.harness,
                               compiler=snapshot_original.compiler,
                               files_to_instrument=snapshot_original.files_to_instrument)

        # TODO register with BugZoo

        # build and register the mutant
        mutant = Mutant(uuid, snapshot.name, mutations)
        return mutant
