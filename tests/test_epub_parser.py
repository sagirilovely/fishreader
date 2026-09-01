"""Unit tests for fishreader.parsers.epub_parser and mobi_parser failure path.

Covers the test points from docs/开发文档.md §7.1: the mini EPUB fixture
(spine order, tag stripping) plus the corrupt-epub / broken-mobi failure
mode (ParseError).
"""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.parsers import get_parser  # noqa: E402
from fishreader.parsers.base import ParseError  # noqa: E402
from fishreader.parsers.epub_parser import EpubParser  # noqa: E402
from fishreader.parsers.mobi_parser import MobiParser  # noqa: E402
from fishreader.parsers.txt_parser import TxtParser  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class EpubParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = EpubParser()

    def test_mini_epub_meta_and_chapters(self):
        book = self.parser.parse(FIXTURES / "mini.epub")
        self.assertEqual(book.title, "Field Notes Compilation")
        self.assertEqual(book.author, "Anonymous")
        self.assertEqual(book.fmt, "epub")
        self.assertTrue(book.readable)
        self.assertIsNone(book.reason)
        self.assertEqual(
            [c.title for c in book.chapters],
            ["第一章 暗河", "第2章 回声", "第三章 尾声"],
        )
        self.assertEqual(book.chapter_count, 3)
        self.assertEqual(book.total_chars, len(book.full_text))

    def test_spine_order_preserved(self):
        book = self.parser.parse(FIXTURES / "mini.epub")
        self.assertIn("河水暗沉", book.chapters[0].content)
        self.assertIn("石壁", book.chapters[1].content)
        self.assertIn("鞠了一躬", book.chapters[2].content)
        # chapters concatenate into full_text with the documented separators
        self.assertTrue(book.full_text.startswith(f"{book.chapters[0].title}\n\n"))

    def test_chapter_offsets(self):
        book = self.parser.parse(FIXTURES / "mini.epub")
        self.assertEqual(book.chapters[0].start_char, 0)
        self.assertEqual(book.chapters[1].start_char, book.chapters[0].end_char + 2)
        self.assertEqual(book.chapters[2].start_char, book.chapters[1].end_char + 2)

    def test_style_script_head_stripped(self):
        book = self.parser.parse(FIXTURES / "mini.epub")
        c1 = book.chapters[0].content
        self.assertNotIn("style", c1.lower())
        self.assertNotIn("script", c1.lower())
        self.assertNotIn("color", c1.lower())
        self.assertNotIn("var x", c1)
        self.assertNotIn("<", c1)          # no raw markup left
        self.assertNotIn("p{", c1)
        # body text survives
        self.assertIn("河水暗沉", c1)
        self.assertIn("暮色压下来", c1)

    def test_br_and_li_handling(self):
        book = self.parser.parse(FIXTURES / "mini.epub")
        c1 = book.chapters[0].content
        # <br/> becomes a paragraph break
        self.assertIn("没见到任何活物。", c1)
        # <li> text is kept (block element appended to the paragraph)
        self.assertIn("外婆曾说，暗河尽头住着守护水脉的老龟。", c1)

    def test_headings_become_chapter_titles_not_body(self):
        book = self.parser.parse(FIXTURES / "mini.epub")
        for ch in book.chapters:
            self.assertIn("章", ch.title)  # titles come from <h1>, not "前言"
        self.assertNotIn("前言", [c.title for c in book.chapters])

    def test_corrupt_epub_raises_parse_error(self):
        with self.assertRaises(ParseError) as ctx:
            self.parser.parse(FIXTURES / "corrupt.epub")
        self.assertIn("container.xml", str(ctx.exception))

    def test_missing_file_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.parser.parse(FIXTURES / "missing.epub")


class MobiFailureTest(unittest.TestCase):
    def test_broken_mobi_raises_parse_error_with_reason(self):
        with self.assertRaises(ParseError) as ctx:
            MobiParser().parse(FIXTURES / "broken.mobi")
        msg = str(ctx.exception)
        self.assertTrue("DRM" in msg or "unsupported" in msg)


class ParserFactoryTest(unittest.TestCase):
    def test_get_parser_mapping(self):
        self.assertIsInstance(get_parser("txt"), TxtParser)
        self.assertIsInstance(get_parser(".txt"), TxtParser)
        self.assertIsInstance(get_parser("epub"), EpubParser)
        self.assertIsInstance(get_parser("mobi"), MobiParser)
        self.assertIsNone(get_parser("zzz"))
        self.assertIsNone(get_parser(""))


if __name__ == "__main__":
    unittest.main()