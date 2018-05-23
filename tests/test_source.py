from typing import Callable, List
from unittest.mock import MagicMock

import pytest
from bugzoo.core.bug import Bug as Snapshot

from boggart.core import Replacement, FileLocationRange
from boggart.config.operators import Operators as OperatorManager
from boggart.server.sourcefile import SourceFileManager


class MockSourceFileManager(SourceFileManager):
    def __init__(self, src: str) -> None:
        super().__init__(None, None, OperatorManager())
        self.read_file = MagicMock(return_value=src)


class MockSnapshot(object):
    def name(self) -> str:
        return "foo"


def test_line_col_to_offset():
    def build(src: str) -> Callable[[int, int], int]:
        snapshot = MockSnapshot()
        mgr = MockSourceFileManager(src)
        def convert(line: int, col: int) -> int:
            return mgr.line_col_to_offset(snapshot, "foo.c", line, col)
        return convert

    convert = build("""
int sm = 0;
for (int i = 0; i < 10; ++i) {
  sm += i;
}
    """.strip())

    assert convert(1, 0) == 0
    assert convert(1, 11) == 11
    assert convert(2, 0) == 12
    assert convert(2, 5) == 17


def test_apply():
    fn = "foo.c"
    def r(loc: str, text: str) -> Replacement:
        loc = "{}@{}".format(fn, loc)
        return Replacement(FileLocationRange.from_string(loc), text)
    def apply(src: str, replacements: List[Replacement]) -> str:
        snapshot = MockSnapshot()
        mgr = MockSourceFileManager(src)
        return mgr.apply(snapshot, fn, replacements)

    src = """
int sm = 0;
for (int i = 0; i < 10; ++i) {
  sm += i;
}
    """.strip()
    replacements = [r("1:0::1:3", "unsigned int")]
    expected = """
unsigned int sm = 0;
for (int i = 0; i < 10; ++i) {
  sm += i;
}
    """.strip()
    assert apply(src, replacements) == expected
