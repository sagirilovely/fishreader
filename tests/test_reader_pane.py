"""Unit tests for reader_pane.decorate_lines (disguise styles + spacing).

The fractional-spacing cases are the point of this file: a terminal can only
draw whole rows, so a spacing of 0.25 must insert one blank row every four
lines instead of rounding up to a blank row per line.
"""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.widgets.reader_pane import decorate_lines  # noqa: E402


class DecorateStyleTest(unittest.TestCase):
    def test_markdown_prefix(self):
        self.assertEqual(
            decorate_lines(["a", "b"], "markdown"), ["- a", "- b"]
        )

    def test_comment_prefix(self):
        self.assertEqual(decorate_lines(["a"], "comment"), ["# a"])

    def test_docstring_wraps(self):
        self.assertEqual(
            decorate_lines(["a"], "docstring"), ['"""', "- a", '"""']
        )

    def test_empty_lines_kept(self):
        self.assertEqual(
            decorate_lines(["a", "", "b"], "markdown"), ["- a", "", "- b"]
        )


class DecorateSpacingTest(unittest.TestCase):
    def test_whole_line_spacing(self):
        self.assertEqual(
            decorate_lines(["a", "b", "c"], "markdown", line_spacing=1),
            ["- a", "", "- b", "", "- c", ""],
        )
        self.assertEqual(
            decorate_lines(["a", "b"], "markdown", line_spacing=2),
            ["- a", "", "", "- b", "", ""],
        )

    def test_fractional_spacing_spreads_blank_rows(self):
        # 0.25 -> one blank row every four lines
        self.assertEqual(
            decorate_lines(["a", "b", "c", "d"], "markdown", line_spacing=0.25),
            ["- a", "- b", "- c", "- d", ""],
        )
        # 0.5 -> one blank row every two lines
        self.assertEqual(
            decorate_lines(["a", "b", "c", "d"], "markdown", line_spacing=0.5),
            ["- a", "- b", "", "- c", "- d", ""],
        )

    def test_fraction_is_tighter_than_one_blank_line(self):
        lines = [f"line{i}" for i in range(8)]
        tight = decorate_lines(lines, "markdown", line_spacing=0.25)
        loose = decorate_lines(lines, "markdown", line_spacing=1)
        self.assertLess(len(tight), len(loose))
        # 8 lines + 2 blank rows vs 8 lines + 8 blank rows
        self.assertEqual(len(tight), 10)
        self.assertEqual(len(loose), 16)

    def test_paragraph_spacing_spreads_too(self):
        text = ["a", "", "b", "", "c", "", "d", ""]
        out = decorate_lines(text, "markdown", paragraph_spacing=0.5)
        self.assertEqual(out.count(""), 6)  # 4 source + 2 inserted

    def test_zero_spacing_adds_nothing(self):
        self.assertEqual(
            decorate_lines(["a", "", "b"], "markdown", 0, 0), ["- a", "", "- b"]
        )

    def test_paragraph_spacing_ignores_leading_blank(self):
        # a paragraph break is only a blank line that follows content
        self.assertEqual(
            decorate_lines(["", "a"], "markdown", paragraph_spacing=1),
            ["", "- a"],
        )


if __name__ == "__main__":
    unittest.main()
