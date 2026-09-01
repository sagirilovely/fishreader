"""Unit tests for fishreader.textlayout.

Covers the test points from docs/开发文档.md §7.1:
display_width (ASCII/CJK/fullwidth/Tab/emoji), wrap_text (Chinese folding,
word keeping, line-start punctuation rule, undersized width), paginate
(page continuity, first char offset, empty text, exact-full page).

Expected values below were verified against the current implementation.
"""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.models import Chapter  # noqa: E402
from fishreader.textlayout import (  # noqa: E402
    Page,
    blank_rows_after,
    chapter_index_at,
    display_width,
    fit_lines,
    paginate,
    spacing_rows,
    wrap_text,
    wrap_text_with_offsets,
)


class DisplayWidthTest(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(display_width(""), 0)
        self.assertEqual(display_width("abc"), 3)
        self.assertEqual(display_width("hello world"), 11)

    def test_cjk_and_fullwidth(self):
        self.assertEqual(display_width("中文"), 4)
        self.assertEqual(display_width("，。"), 4)
        self.assertEqual(display_width("Ａ"), 2)  # fullwidth
        self.assertEqual(display_width("ｱ"), 1)  # halfwidth kana

    def test_tab_and_emoji(self):
        self.assertEqual(display_width("\t"), 4)
        self.assertEqual(display_width("😀"), 2)  # W-category emoji
        self.assertEqual(display_width("a\t中"), 1 + 4 + 2)

    def test_mixed(self):
        self.assertEqual(display_width("a中b"), 1 + 2 + 1)


class WrapTextTest(unittest.TestCase):
    def test_chinese_folding(self):
        self.assertEqual(wrap_text("中文折行测试", 4), ["中文", "折行", "测试"])
        self.assertEqual(
            wrap_text("这是测试文本用于折行", 6), ["这是测", "试文本", "用于折", "行"]
        )

    def test_trailing_offsets_of_content(self):
        # a single run shorter than the width stays on one line
        text = "一二三四五六七八九十"
        self.assertEqual(wrap_text(text, 4), ["一二", "三四", "五六", "七八", "九十"])

    def test_english_words_not_broken(self):
        self.assertEqual(
            wrap_text("hello world foo bar", 10), ["hello", "world foo", "bar"]
        )
        self.assertEqual(
            wrap_text("Multiple words in a sentence wrap here", 12),
            ["Multiple", "words in a", "sentence", "wrap here"],
        )

    def test_oversized_word_is_chunked(self):
        lines = wrap_text("verylongwordalpha", 5)
        # the word is chopped into width-sized chunks when wider than the line
        self.assertEqual(lines[:3], ["veryl", "ongwo", "rdalp"])
        self.assertTrue(lines[3].startswith("ha"))

    def test_undersized_width_is_coerced(self):
        self.assertEqual(wrap_text("abc", 0), ["a", "b", "c"])

    def test_blank_paragraphs_stay_blank(self):
        self.assertEqual(wrap_text("a\n\nb", 2), ["a", "", "b"])
        self.assertEqual(wrap_text("\n", 2), ["", ""])

    def test_closing_punctuation_hangs_on_previous_line(self):
        # 。 must not start a line: it is appended to the previous line.
        lines = wrap_text("你说得对。", 4)
        self.assertEqual(lines[0], "你说")
        self.assertTrue(lines[1].endswith("。"))
        for line in lines:
            if line:
                self.assertNotIn(line[0], "。，、！？；：）】》」』…—")
        # same rule across a fresh flush boundary
        lines2 = wrap_text("谢谢你。", 3)
        self.assertTrue(any("。" in ln for ln in lines2))

    def test_leading_spaces_dropped(self):
        self.assertEqual(wrap_text("   a b", 10), ["a b"])


class WrapTextOffsetsTest(unittest.TestCase):
    def test_offsets_are_line_first_char(self):
        # "hello world": "hello" starts at 0; "world" at 6 (after the space)
        self.assertEqual(wrap_text_with_offsets("hello world", 10), [("hello", 0), ("world", 6)])
        self.assertEqual(
            wrap_text_with_offsets("abc\ndef\n", 10),
            [("abc", 0), ("def", 4), ("", 8)],
        )

    def test_cjk_offsets_by_source_chars(self):
        got = wrap_text_with_offsets("一二三四五六七八九十", 4)
        self.assertEqual(got[0], ("一二", 0))
        self.assertEqual(got[2], ("五六", 4))
        self.assertEqual(got[4], ("九十", 8))


def _two_chapters() -> list:
    return [
        Chapter(index=0, title="一", content="x", start_char=0, end_char=3),
        Chapter(index=1, title="二", content="y", start_char=5, end_char=9),
    ]


class PaginateTest(unittest.TestCase):
    def test_empty_text_is_eof_page(self):
        page = paginate(_two_chapters(), "", 0, 5, 3)
        self.assertIsInstance(page, Page)
        self.assertEqual(page.lines, [])
        self.assertEqual(page.first_char_offset, 0)
        self.assertEqual(page.next_page_start, 0)
        self.assertTrue(page.eof)

    def test_start_at_total_is_eof_page(self):
        page = paginate(_two_chapters(), "abc", 3, 4, 4)
        self.assertEqual(page.lines, [])
        self.assertTrue(page.eof)
        self.assertEqual(page.next_page_start, 3)

    def test_first_char_offset_matches_requested_start(self):
        for start in (0, 2, 7, 9):
            with self.subTest(start=start):
                page = paginate(_two_chapters(), "一二三四五六七八九十", start, 4, 4)
                self.assertEqual(page.first_char_offset, start)

    def test_negative_start_clamped(self):
        page = paginate(_two_chapters(), "abc", -5, 4, 4)
        self.assertEqual(page.first_char_offset, 0)
        self.assertEqual(page.lines, ["abc"])

    def test_page_shows_first_visible_wrapped_lines(self):
        text = "一二三四五六七八九十"
        page = paginate(_two_chapters(), text, 0, 4, 4)
        self.assertEqual(page.lines, ["一二", "三四", "五六", "七八"])
        page = paginate(_two_chapters(), text, 8, 4, 4)
        self.assertEqual(page.lines, ["九十"])
        self.assertTrue(page.eof)  # page holding the whole tail

    def test_page_continuity_walk_until_eof(self):
        chapters = [
            Chapter(0, "第一章", "第一章正文内容。", 0, 11),
            Chapter(1, "第二章", "第二章正文内容。", 13, 24),
        ]
        text = "第一章\n\n第一章正文内容。\n\n第二章\n\n第二章正文内容。"
        starts = [0, 4, 7, 11, 15, 19, 22, 26]
        s = 0
        seen = []
        for _ in range(12):
            page = paginate(chapters, text, s, 5, 2)
            seen.append((s, tuple(page.lines), page.next_page_start, page.eof))
            self.assertEqual(page.first_char_offset, s)
            self.assertGreaterEqual(page.next_page_start, s)
            if page.eof or page.next_page_start <= s:
                break
            s = page.next_page_start
        # pages advance monotonically and reach the end of the book
        self.assertEqual([x[0] for x in seen], starts)
        self.assertEqual(seen[-1][1], ("容。",))
        self.assertTrue(seen[-1][3])

    def test_chapter_index_tracks_offset(self):
        chapters = _two_chapters()
        self.assertEqual(chapter_index_at(chapters, 0), 0)
        self.assertEqual(chapter_index_at(chapters, 4), 0)
        self.assertEqual(chapter_index_at(chapters, 5), 1)
        self.assertEqual(chapter_index_at(chapters, 99), 1)
        self.assertEqual(chapter_index_at([], 5), 0)
        page = paginate(chapters, "abcdef", 5, 1, 1)
        self.assertEqual(page.chapter_index, 1)

    def test_exactly_full_page_then_eof(self):
        # two single-line paragraphs fill the page exactly; the next page is EOF
        chapters = _two_chapters()
        p1 = paginate(chapters, "ab\ncd\n", 0, 2, 2)
        self.assertEqual(p1.lines, ["ab", "cd"])
        self.assertEqual(p1.next_page_start, len("ab\ncd\n"))
        self.assertFalse(p1.eof)
        p2 = paginate(chapters, "ab\ncd\n", p1.next_page_start, 2, 2)
        self.assertTrue(p2.eof)
        self.assertEqual(p2.next_page_start, len("ab\ncd\n"))

    def test_line_spacing_reduces_visible_lines(self):
        chapters = _two_chapters()
        text = "一二三四五六七八九十"
        loose = paginate(chapters, text, 0, 4, 8, line_spacing=1)
        tight = paginate(chapters, text, 0, 4, 4, line_spacing=0)
        self.assertEqual(len(loose.lines), 4)
        self.assertEqual(len(tight.lines), 4)
        # 8 rows with 1 blank line per row == 4 rows without spacing
        self.assertEqual(loose.lines, wrap_text(text, 4)[:4])
        one_line = paginate(chapters, text, 0, 4, 10, line_spacing=1)
        self.assertEqual(len(one_line.lines), 5)
        self.assertEqual(one_line.lines, wrap_text(text, 4))

    def test_box_dimensions_coerced(self):
        page = paginate(_two_chapters(), "abcdef", 0, 0, 0)
        self.assertEqual(page.lines, ["a"])  # width 1, height 1
        self.assertEqual(page.next_page_start, 1)

    def test_single_paragraph_text_advances(self):
        # regression guard: paging a single-paragraph text must progress
        chapters = _two_chapters()
        p1 = paginate(chapters, "abcdefghij", 0, 2, 5)
        self.assertEqual(p1.lines, ["ab", "cd", "ef", "gh", "ij"])
        self.assertEqual(p1.next_page_start, 10)
        self.assertGreater(p1.next_page_start, p1.first_char_offset)
        p2 = paginate(chapters, "abcdefghij", p1.next_page_start, 2, 5)
        self.assertTrue(p2.eof)

    def test_next_page_does_not_skip_text(self):
        # pages continue exactly at the first char of the next line
        chapters = _two_chapters()
        text = "hello world foo bar"
        p1 = paginate(chapters, text, 0, 6, 1)
        self.assertEqual(p1.lines, ["hello"])
        self.assertEqual(p1.next_page_start, 6)  # "world" starts at char 6
        p2 = paginate(chapters, text, 6, 6, 1)
        self.assertEqual(p2.lines, ["world"])
        self.assertEqual(p2.next_page_start, 12)  # "foo" starts at char 12


class SpacingRowMathTest(unittest.TestCase):
    """Fractional spacing: blank rows spread over a page, line count fitted exactly."""

    def test_blank_rows_after_spreads_fractions(self):
        self.assertEqual(blank_rows_after(4, 0), [0, 0, 0, 0])
        self.assertEqual(blank_rows_after(4, 1), [1, 1, 1, 1])
        self.assertEqual(blank_rows_after(4, 2), [2, 2, 2, 2])
        # one blank row every four / two lines
        self.assertEqual(blank_rows_after(8, 0.25), [0, 0, 0, 1, 0, 0, 0, 1])
        self.assertEqual(blank_rows_after(4, 0.5), [0, 1, 0, 1])
        # a fraction smaller than one line still yields something
        self.assertEqual(blank_rows_after(2, 0.25), [0, 0])

    def test_spacing_rows_matches_the_spread(self):
        for spacing in (0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2):
            for count in range(1, 40):
                with self.subTest(spacing=spacing, count=count):
                    self.assertEqual(
                        sum(blank_rows_after(count, spacing)),
                        spacing_rows(count, spacing),
                    )
        # average gap stays equal to the requested spacing
        self.assertEqual(spacing_rows(100, 0.25), 25)
        self.assertEqual(spacing_rows(9, 0.5), 4)

    def test_fit_lines_is_exact(self):
        for spacing in (0, 0.25, 0.5, 0.75, 1, 1.5, 2):
            smallest_page = 1 + spacing_rows(1, spacing)
            for height in range(1, 40):
                with self.subTest(spacing=spacing, height=height):
                    n = fit_lines(height, spacing)
                    self.assertGreaterEqual(n, 1)
                    if height < smallest_page:
                        self.assertEqual(n, 1)  # even one line overflows: clamp
                        continue
                    self.assertLessEqual(n + spacing_rows(n, spacing), height)
                    # one more line would not fit
                    self.assertGreater(n + 1 + spacing_rows(n + 1, spacing), height)

    def test_fit_lines_denser_than_integer_spacing(self):
        # 30 rows: spacing 1 fits 15 lines, 0.25 fits 24 — the finer knob
        # really does buy extra lines per page.
        self.assertEqual(fit_lines(30, 1), 15)
        self.assertEqual(fit_lines(30, 0.25), 24)
        self.assertEqual(fit_lines(30, 0), 30)

    def test_paginate_accepts_fractional_spacing(self):
        chapters = _two_chapters()
        text = "一二三四五六七八九十" * 3
        tight = paginate(chapters, text, 0, 4, 10, line_spacing=0)
        half = paginate(chapters, text, 0, 4, 10, line_spacing=0.5)
        loose = paginate(chapters, text, 0, 4, 10, line_spacing=1)
        self.assertGreater(len(half.lines), len(loose.lines))
        self.assertLess(len(half.lines), len(tight.lines))


if __name__ == "__main__":
    unittest.main()