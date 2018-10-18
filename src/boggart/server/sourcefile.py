from typing import Dict, Tuple, List
from difflib import unified_diff
import logging

from bugzoo.core.patch import Patch
from bugzoo.core.bug import Bug
from bugzoo.client import Client as BugZooClient
from rooibos import Client as RooibosClient

from ..config.operators import Operators as OperatorManager
from ..core import FileLocationRange, Replacement, Mutation, FileLine, Location
from ..exceptions import *

logger = logging.getLogger(__name__)

__all__ = ['SourceFileManager']


class SourceFileManager(object):
    def __init__(self,
                 client_bugzoo: BugZooClient,
                 client_rooibos: RooibosClient,
                 operators: OperatorManager
                 ) -> None:
        self.__bugzoo = client_bugzoo
        self.__rooibos = client_rooibos
        self.__operators = operators
        self.__cache_file_contents = {}  # type: Dict[Tuple[str, str], str]
        self.__cache_offsets = {}  # type: Dict[Tuple[str, str], List[int]]

    def num_lines(self, snapshot: Bug, filepath: str) -> int:
        """
        Computes the number of lines that belong to a particular file in a
        given snapshot.

        Raises:
            FileNotFound: if the given file is not found within the provided
                snapshot.
        """
        return len(self._line_offsets(snapshot, filepath))

    def _forget_file(self, snapshot: Bug, filepath: str) -> None:
        """
        Removes all stored information for a particular file belonging to a
        given snapshot.
        """
        try:
            cache_key = (snapshot.name, filepath)
            del self.__cache_offsets[cache_key]
            del self.__cache_file_contents[cache_key]
        except KeyError:
            pass

    def _fetch_files(self, snapshot: Bug, filepaths: List[str]) -> None:
        """
        Pre-emptively stores the contents of a given list of files for a
        particular snapshot.
        """
        bgz = self.__bugzoo
        container = bgz.containers.provision(snapshot)
        try:
            for filepath in filepaths:
                key = (snapshot.name, filepath)
                try:
                    if key in self.__cache_file_contents:
                        continue
                    self.__cache_file_contents[key] = \
                        bgz.files.read(container, filepath)
                except KeyError:
                    logger.exception("Failed to read source file, '%s/%s': file not found",  # noqa: pycodestyle
                                     snapshot.name, filepath)
                    raise FileNotFound(filepath)
        finally:
            del bgz.containers[container.uid]

    def _line_offsets(self, snapshot: Bug, filepath: str) -> List[int]:
        """
        Returns a list specifying the offset for the first character on each
        line in a given file belonging to a BugZoo snapshot.
        """
        logger.debug("Fetching line offsets for file, '%s', in snapshot, '%s'",  # noqa: pycodestyle
                     filepath,
                     snapshot.name)
        key_cache = (snapshot.name, filepath)
        if key_cache in self.__cache_offsets:
            logger.debug("Retrieving line offsets for file, '%s', in snapshot, '%s', from cache.",  # noqa: pycodestyle
                         filepath,
                         snapshot.name)
            return self.__cache_offsets[key_cache]

        logger.debug("Computing line offsets for file, '%s', in snapshot, '%s'",  # noqa: pycodestyle
                     filepath,
                     snapshot.name)
        contents = self.read_file(snapshot, filepath)

        # find all indices of newline characters
        offsets = [0]
        last_offset = 0
        while True:
            next_line_break = contents.find('\n', last_offset)
            if next_line_break == -1:
                break
            last_offset = next_line_break + 1
            offsets.append(last_offset)

        logger.debug("Saving line offsets for file, '%s', in snapshot, '%s', to cache.",  # noqa: pycodestyle
                     filepath,
                     snapshot.name)
        self.__cache_offsets[key_cache] = offsets
        return offsets

    def line_col_to_offset(self,
                           snapshot: Bug,
                           filepath: str,
                           line_num: int,
                           col_num: int
                           ) -> int:
        """
        Transforms a line-column number for a given file belonging to a
        BugZoo snapshot into a zero-indexed character offset.
        """
        assert line_num > 0
        assert col_num >= 0
        line_col_s = "%s/%s[%d:%d]".format(snapshot.name,
                                           filepath,
                                           line_num,
                                           col_num)
        logger.debug("Transforming line-column, '%s', into a character offset",  # noqa: pycodestyle
                     line_col_s)
        line_offsets = self._line_offsets(snapshot, filepath)
        line_starts_at = line_offsets[line_num - 1]
        offset = line_starts_at + col_num
        logger.debug("Transformed line-column, '%s', into character offset: %s",  # noqa: pycodestyle
                     line_col_s,
                     offset)
        return offset

    def mutations_to_diff(self,
                          snapshot: Bug,
                          mutations: List[Mutation]
                          ) -> Patch:
        """
        Transforms a list of mutations to a given snapshot into a unified diff
        that can be applied to that snapshot.
        """
        replacements = self.mutations_to_replacements(snapshot, mutations)
        diff = self.replacements_to_diff(snapshot, replacements)
        return diff

    def mutations_to_replacements(self,
                                  snapshot: Bug,
                                  mutations: List[Mutation]
                                  ) -> Dict[str, List[Replacement]]:
        """
        Transforms a list of mutations to a given snapshot into a set of
        source code replacements.

        Parameters:
            snapshot: the snapshot to which the mutations should be applied.
            mutations: the mutations to apply to the snapshot.

        Returns:
            a mapping from (modified) files in the snapshot, given by their
            paths relative to the source directory for the snapshot, to a list
            of source code replacements in that file.
        """
        logger.debug("transforming mutations into replacements")
        file_to_replacements = {}  # type: Dict[str, List[Replacement]]
        for mutation in mutations:
            fn = mutation.location.filename
            if fn not in file_to_replacements:
                file_to_replacements[fn] = []
            replacement = self.mutation_to_replacement(snapshot, mutation)
            file_to_replacements[fn].append(replacement)
        logger.debug("transformed mutations to replacements: %s",
                     file_to_replacements)
        return file_to_replacements

    def mutation_to_replacement(self,
                                snapshot: Bug,
                                mutation: Mutation
                                ) -> Replacement:
        """
        Transforms a given mutation to a snapshot into a replacement.
        """
        logger.debug("transforming mutation [%s] to replacement.", mutation)
        operator = self.__operators[mutation.operator]
        transformation = \
            operator.transformations[mutation.transformation_index]
        text_mutated = self.__rooibos.substitute(transformation.rewrite,
                                                 mutation.arguments)
        replacement = Replacement(mutation.location, text_mutated)
        logger.debug("transformed mutation [%s] to replacement [%s].",
                     mutation, replacement)
        return replacement

    def replacements_to_diff(self,
                             snapshot: Bug,
                             file_to_replacements: Dict[str, List[Replacement]]
                             ) -> Patch:
        """
        Transforms a set of replacements into a unified diff for a given
        snapshot.

        Parameters:
            snapshot: the snapshot to which the replacements should be
                applied.
            file_to_replacements: a mapping from files, indexed by their path
                relative to the source directory for the snapshot, to
                replacements in that file.

        Returns:
            a unified diff that applies all of the given replacements to the
            source code for the given snapshot.
        """
        logger.debug("transforming replacements to diff")
        file_diffs = []  # type: List[str]
        for (filename, replacements) in file_to_replacements.items():
            original = self.read_file(snapshot, filename)
            mutated = self.apply(snapshot, filename, replacements)
            diff = ''.join(unified_diff(original.splitlines(True),
                                        mutated.splitlines(True),
                                        filename, filename))
            logger.debug("transformed replacements to file to diff:\n%s", diff)
            file_diffs.append(diff)
        diff_s = '\n'.join(file_diffs)
        logger.debug("transformed mutations to diff:\n%s", diff_s)
        diff = Patch.from_unidiff('\n'.join(file_diffs))
        return diff

    def read_file(self, snapshot: Bug, filepath: str) -> str:
        """
        Fetches the contents of a specified source code file belonging to a
        given BugZoo snapshot.

        Raises:
            FileNotFound: if the given file is not found inside the snapshot.
        """
        logger.debug("Reading contents of source file: %s/%s",  # noqa: pycodestyle
                     snapshot.name, filepath)
        # TODO normalise file path

        bgz = self.__bugzoo
        key_cache = (snapshot.name, filepath)
        if key_cache in self.__cache_file_contents:
            contents = self.__cache_file_contents[key_cache]
            logger.debug("Found contents of source file, '%s/%s', in cache.",  # noqa: pycodestyle
                         snapshot.name, filepath)
            return contents

        logger.debug("Provisioning a temporary container to fetch contents of file")  # noqa: pycodestyle
        container = bgz.containers.provision(snapshot)
        try:
            contents = bgz.files.read(container, filepath)
        except KeyError:
            logger.exception("Failed to read source file, '%s/%s': file not found",  # noqa: pycodestyle
                             snapshot.name, filepath)
            raise FileNotFound(filepath)
        finally:
            del bgz.containers[container.uid]
        logger.debug("Read contents of source file, '%s/%s'",
                     snapshot.name, filepath)

        self.__cache_file_contents[key_cache] = contents
        return contents

    def read_line(self,
                  snapshot: Bug,
                  location: FileLine,
                  *,
                  keep_newline: bool = False
                  ) -> str:
        """
        Fetches the contents of a given line belonging to a particular
        BugZoo snapshot.

        Raises:
            FileNotFound: if the file associated with the given line is
                not found inside the snapshot.

        TODO: LineNotFound
        """
        content_file = self.read_file(snapshot, location.filename)
        line_offsets = self._line_offsets(snapshot, location.filename)
        start_at = line_offsets[location.num - 1]
        if len(line_offsets) == location.num:
            content_line = content_file[start_at:]
        else:
            end_at = line_offsets[location.num]
            content_line = content_file[start_at:end_at]
        return content_line if keep_newline else content_line.rstrip('\n')

    def read_chars(self, snapshot: Bug, location: FileLocationRange) -> str:
        """
        Fetches a specified sequence of characters from a source code file
        belonging to a BugZoo snapshot.

        Raises:
            FileNotFound: if the given file is not found inside the snapshot.
        """
        # logger.debug("Reading characters at %s in snapshot, %s",
        #              location, snapshot.name)
        filename = location.filename
        contents_file = self.read_file(snapshot, filename)

        start_at = self.line_col_to_offset(snapshot,
                                           filename,
                                           location.start.line,
                                           location.start.column)
        stop_at = self.line_col_to_offset(snapshot,
                                          filename,
                                          location.stop.line,
                                          location.stop.column)

        contents = contents_file[start_at:stop_at + 1]
        # logger.debug("Read characters at %s in snapshot, %s: %s",
        #              location, snapshot.name, contents)
        return contents

    def apply(self,
              snapshot: Bug,
              filename: str,
              replacements: List[Replacement]
              ) -> str:
        # TODO ensure all replacements are in the same file
        logger.debug("applying replacements to source file, '%s/%s': %s",
                     snapshot.name, filename, replacements)

        # exclude conflicting replacements
        replacements = Replacement.resolve(replacements)

        content = self.read_file(snapshot, filename)
        for replacement in replacements:
            location = replacement.location
            start_at = self.line_col_to_offset(snapshot,
                                               filename,
                                               location.start.line,
                                               location.start.column)
            stop_at = self.line_col_to_offset(snapshot,
                                              filename,
                                              location.stop.line,
                                              location.stop.column)
            content = \
                content[:start_at] + replacement.text + content[stop_at:]
        logger.debug("applied replacements to source file, '%s/%s': %s",
                     snapshot.name, filename, replacements)
        return content
