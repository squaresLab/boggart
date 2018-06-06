from typing import Callable, List
from unittest.mock import MagicMock

import pytest
from bugzoo.core.bug import Bug as Snapshot

from boggart.core import Replacement, FileLocationRange, FileLine
from boggart.config.operators import Operators as OperatorManager
from boggart.server.sourcefile import SourceFileManager


class MockSourceFileManager(SourceFileManager):
    def __init__(self, src: str) -> None:
        super().__init__(None, None, OperatorManager())
        self.read_file = MagicMock(return_value=src)


class MockSnapshot(object):
    @property
    def name(self) -> str:
        return "foo"


def test_read_line():
    def build(src: str) -> Callable[[int], str]:
        snapshot = MockSnapshot()
        mgr = MockSourceFileManager(src)
        def read_line(num: int, *, keep_newline: bool = False) -> str:
            assert num > 0
            line = FileLine("foo.c", num)
            return mgr.read_line(snapshot, line, keep_newline=keep_newline)
        return read_line

    read_line = build("""
int sm = 0;
for (int i = 0; i < 10; ++i) {
  sm += i;
}
    """.strip())
    assert read_line(1) == "int sm = 0;"
    assert read_line(1, keep_newline=True) == "int sm = 0;\n"
    assert read_line(2) == "for (int i = 0; i < 10; ++i) {"
    assert read_line(2, keep_newline=True) == "for (int i = 0; i < 10; ++i) {\n"
    assert read_line(3) == "  sm += i;"
    assert read_line(3, keep_newline=True) == "  sm += i;\n"
    assert read_line(4) == "}"
    assert read_line(4, keep_newline=True) == "}"


def test_num_lines():
    def num_lines(src: str) -> int:
        src = src.strip()
        snapshot = MockSnapshot()
        mgr = MockSourceFileManager(src)
        return mgr.num_lines(snapshot, "foo.c")

    assert num_lines(
        """
        int x = 0;
        int y = 0;
        int z = x + y;
        """) == 3
    assert num_lines(
        """
        """) == 1


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
