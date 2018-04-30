# TODO mutants are killed when the server is killed
from typing import List, Iterator, Dict
from uuid import UUID, uuid4
from difflib import unified_diff
import tempfile

from bugzoo.core.bug import Bug
from bugzoo.core.patch import Patch
from bugzoo.client import Client as BugZooClient
from rooibos import Client as RooibosClient

from .sourcefile import SourceFileManager
from ..config.operators import Operators as OperatorManager
from ..core import Mutant, Mutation, Replacement


class MutantManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient,
                 client_rooibos: RooibosClient,
                 operators: OperatorManager,
                 sources: SourceFileManager
                 ) -> None:
        self.__mutants = {} # type: Dict[UUID, Mutant]
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
        mutant = self[uuid]
        self.__bugzoo.docker.delete_image(mutant.docker_image)
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
        bz = self.__bugzoo
        assert len(mutations) <= 1, "higher-order mutation is currently unsupported"

        # NOTE this is *incredibly* unlikely to conflict
        uuid = uuid4()
        assert uuid not in self.__mutants, "UUID already in use."
        mutant = Mutant(uuid, snapshot.name, mutations)

        # group mutations by file
        file_mutations = {} # type: Dict[str, List[Mutation]]
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
            text_mutated = self.__rooibos.substitute(transformation.rewrite,
                                                     mutation.arguments)

            replacement = Replacement(location, text_mutated)
            replacements_in_file[filename].append(replacement)

        # transform the replacements to a diff
        file_diffs = [] # type: List[str]
        for filename in replacements_in_file:
            original = self.__sources.read_file(snapshot, filename)
            mutated = self.__sources.apply(snapshot,
                                           filename,
                                           replacements_in_file[filename])
            # print("ORIGINAL:\n{}".format(original))
            # print("MUTATED:\n{}".format(mutated))
            diff = ''.join(unified_diff(original.splitlines(True),
                                        mutated.splitlines(True),
                                        filename,
                                        filename))
            file_diffs.append(diff)
        diff_s = '\n'.join(file_diffs)
        mutant_diff = Patch.from_unidiff('\n'.join(file_diffs))
        # print(str(mutant_diff))

        # generate the Docker image on the BugZoo server
        container = bz.containers.provision(snapshot)
        try:
            bz.containers.patch(container, diff)
            bz.containers.persist(container, mutant.docker_image)
        finally:
            del bz.containers[container.uid]

        # build and register a BugZoo snapshot
        snapshot_mutated = Bug(name=mutant.snapshot,
                               image=mutant.docker_image,
                               program=snapshot.program,
                               dataset=None,
                               source=None,
                               source_dir=snapshot.source_dir,
                               languages=snapshot.languages,
                               harness=snapshot.harness,
                               compiler=snapshot.compiler,
                               files_to_instrument=snapshot.files_to_instrument)
        bz.bugs.register(snapshot_mutated)

        # track the mutant
        self.__mutants[mutant.uuid] = mutant
        return mutant
