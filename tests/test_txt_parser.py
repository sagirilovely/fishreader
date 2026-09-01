"""Unit tests for fishreader.parsers.txt_parser.

Covers the test points from docs/开发文档.md §7.1:
UTF-8 / GBK / Big5 decoding, chapter recognition, no-chapter fallback,
empty file, decode-failure raising ParseError.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.parsers.base import ParseError  # noqa: E402
from fishreader.parsers.txt_parser import TxtParser  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"

UTF8_TITLES = ["第一章 风雪夜归人", "第二章 灯下旧信", "第3章 市集", "第四章 归途"]


class TxtParserFixturesTest(unittest.TestCase):
    def setUp(self):
        self.parser = TxtParser()

    def test_utf8_book_fields(self):
        book = self.parser.parse(FIXTURES / "utf8.txt")
        self.assertEqual(book.fmt, "txt")
        self.assertEqual(book.title, "utf8")
        self.assertIsNone(book.author)
        self.assertTrue(book.readable)
        self.assertIsNone(book.reason)
        self.assertEqual([c.title for c in book.chapters], UTF8_TITLES)
        self.assertEqual(book.id, (FIXTURES / "utf8.txt").as_posix())
        self.assertEqual(book.total_chars, len(book.full_text))

    def test_utf8_chapter_offsets_consistent(self):
        book = self.parser.parse(FIXTURES / "utf8.txt")
        self.assertEqual(book.chapters[0].start_char, 0)
        for prev, cur in zip(book.chapters, book.chapters[1:]):
            self.assertEqual(cur.start_char, prev.end_char + 2)  # "\n\n" separator
        for ch in book.chapters:
            part = f"{ch.title}\n\n{ch.content}"
            self.assertEqual(ch.end_char - ch.start_char, len(part))
            # the title sits at start_char inside the full text
            self.assertEqual(book.full_text[ch.start_char : ch.start_char + len(ch.title)], ch.title)
        for i, ch in enumerate(book.chapters):
            self.assertEqual(ch.index, i)
        self.assertTrue(all(ch.content for ch in book.chapters))

    def test_chapter_index_at(self):
        book = self.parser.parse(FIXTURES / "utf8.txt")
        self.assertEqual(book.chapter_index_at(0), 0)
        self.assertEqual(book.chapter_index_at(book.total_chars - 1), 3)
        self.assertEqual(book.chapter_index_at(book.chapters[1].start_char), 1)
        self.assertEqual(book.chapter_index_at(book.chapters[1].start_char - 1), 0)

    def test_gbk_matches_utf8_verbatim(self):
        gbk = self.parser.parse(FIXTURES / "gbk.txt")
        utf8 = self.parser.parse(FIXTURES / "utf8.txt")
        self.assertEqual([c.title for c in gbk.chapters], UTF8_TITLES)
        self.assertEqual(gbk.full_text, utf8.full_text)

    def test_big5_is_traditional_chinese_variant(self):
        big5 = self.parser.parse(FIXTURES / "big5.txt")
        utf8 = self.parser.parse(FIXTURES / "utf8.txt")
        self.assertEqual(len(big5.chapters), 4)
        for ch in big5.chapters:
            self.assertIn("章", ch.title)
        # traditional characters: different from the simplified utf8 text
        self.assertNotEqual(big5.chapters[0].title, utf8.chapters[0].title)
        self.assertNotEqual(big5.full_text, utf8.full_text)
        self.assertTrue(big5.readable)

    def test_no_chapter_falls_back_to_prologue(self):
        book = self.parser.parse(FIXTURES / "no_chapter.txt")
        self.assertEqual(len(book.chapters), 1)
        self.assertEqual(book.chapters[0].title, "前言")
        self.assertIn("连日阴雨", book.chapters[0].content)
        self.assertEqual(book.chapters[0].start_char, 0)
        self.assertTrue(book.readable)

    def test_empty_file_readable(self):
        book = self.parser.parse(FIXTURES / "empty.txt")
        self.assertTrue(book.readable)
        self.assertEqual([c.title for c in book.chapters], ["前言"])
        self.assertEqual(book.chapters[0].content, "")
        self.assertEqual(book.total_chars, len(book.full_text))  # "前言\n\n"

    def test_missing_file_raises_parse_error(self):
        with self.assertRaises(ParseError) as ctx:
            self.parser.parse(FIXTURES / "does_not_exist.txt")
        self.assertIn("cannot read", str(ctx.exception))

    def test_undecodable_bytes_raise_parse_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "garbage.txt"
            p.write_bytes(b"\xff\x00\xff\x00" * 64)
            with self.assertRaises(ParseError) as ctx:
                self.parser.parse(p)
            msg = str(ctx.exception)
            self.assertIn("decode", msg)
            self.assertIn("utf-8", msg)


class TxtParserChapterRegexTest(unittest.TestCase):
    """Chapter-heading variants: 第一章/第3章/第一百二十章/Chapter 1/CHAPTER IV."""

    def test_all_heading_forms_recognized(self):
        body = (
            "第一章\n\n正文一。\n\n"
            "第3章\n\n正文二。\n\n"
            "第一百二十章\n\n正文三。\n\n"
            "Chapter 1\n\nEnglish body one.\n\n"
            "CHAPTER IV\n\nEnglish body four.\n"
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "heads.txt"
            p.write_text(body, encoding="utf-8")
            book = TxtParser().parse(p)
            self.assertEqual(
                [c.title for c in book.chapters],
                ["第一章", "第3章", "第一百二十章", "Chapter 1", "CHAPTER IV"],
            )
            self.assertEqual(len(book.chapters), 5)
            self.assertIn("正文一", book.chapters[0].content)
            self.assertIn("English body four", book.chapters[4].content)
            self.assertTrue(book.readable)

    def test_heading_with_trailing_text(self):
        body = "第一章 风雪夜归人\n\n雪下了整夜。\n\n第二章 灯下旧信\n\n信纸上字迹模糊。\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "titled_line.txt"
            p.write_text(body, encoding="utf-8")
            book = TxtParser().parse(p)
            self.assertEqual([c.title for c in book.chapters], ["第一章 风雪夜归人", "第二章 灯下旧信"])

    def test_heading_without_blank_line(self):
        # "第一章 xxx\n正文…" — heading and body on adjacent lines (no blank).
        body = "第一章 标题\n正文第一行。\n正文第二行。\n\n第二章 乙\n再一段。\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "tight.txt"
            p.write_text(body, encoding="utf-8")
            book = TxtParser().parse(p)
            self.assertEqual([c.title for c in book.chapters], ["第一章 标题", "第二章 乙"])
            self.assertIn("正文第一行", book.chapters[0].content)
            self.assertIn("再一段", book.chapters[1].content)

    def test_mid_paragraph_heading_keeps_prelude(self):
        body = "序言一段。\n第一章 甲\n正文。\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "mid.txt"
            p.write_text(body, encoding="utf-8")
            book = TxtParser().parse(p)
            self.assertEqual([c.title for c in book.chapters], ["前言", "第一章 甲"])
            self.assertIn("序言一段", book.chapters[0].content)
            self.assertIn("正文", book.chapters[1].content)


if __name__ == "__main__":
    unittest.main()