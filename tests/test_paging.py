"""Paging continuity: page N+1 must start exactly where page N ended.

Regression guard for two bugs that made pages look disconnected:

1. `wrap_width` did not reserve the two columns taken by the "- "/"# "
   style prefix, so the widget re-wrapped every line into two rows. The
   page grew taller than the pane and `overflow-y: hidden` silently ate
   its tail — lines that were then never shown, because the next page
   starts *after* them.
2. The per-page line count only accounted for `line_spacing`, ignoring
   paragraph spacing and the docstring markers, with the same effect.
"""

import sys
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from textual.widgets import Static  # noqa: E402

from fishreader.app import FishApp  # noqa: E402
from fishreader.config import load_config  # noqa: E402
from fishreader.textlayout import display_width  # noqa: E402

# Paragraphs of varying length; each opens with a unique token so a rendered
# line can be traced back to its source line.
_PARAGRAPHS = [f"P{i:04d} 这是一段正文内容。" * (1 + i % 3) for i in range(1, 90)]
BODY = (
    "第一章 开端\n\n"
    + "\n\n".join(_PARAGRAPHS[:45])
    + "\n\n第二章 继续\n\n"
    + "\n\n".join(_PARAGRAPHS[45:])
    + "\n"
)


def _rows(pane: Static) -> list[str]:
    content = pane.render()
    return getattr(content, "plain", str(content)).splitlines()


def _content_line(row: str, style: str) -> str | None:
    """Source text of a rendered row, or None for blank/chrome rows."""
    if not row.strip() or row.strip() == '"""':
        return None
    if style == "comment":
        return row[2:] if row.startswith("# ") else row
    return row[2:] if row.startswith("- ") else row


class FishAppPagingTest(unittest.IsolatedAsyncioTestCase):
    CASES = [
        (0, 0, "markdown"),
        (0.25, 0.25, "markdown"),
        (0.5, 0.5, "markdown"),
        (1, 1, "markdown"),
        (0.5, 0.5, "comment"),
        (0.5, 0.5, "docstring"),
    ]

    def _launch(self, tmp: Path, ls, ps, style, size=(120, 40)):
        (tmp / "books").mkdir()
        (tmp / "books" / "novel.txt").write_text(BODY, encoding="utf-8")
        cfg = load_config(tmp / "fish.toml", project_root=tmp)
        cfg.raw["reader"]["line_spacing"] = ls
        cfg.raw["reader"]["paragraph_spacing"] = ps
        cfg.raw["reader"]["novel_style"] = style
        return FishApp(cfg, tmp), size

    @staticmethod
    def _src_lines(app):
        lines = app._chapter_lines(app.current, app.chapter_index, app.wrap_width)
        return [ln for ln, _ in lines]

    @asynccontextmanager
    async def _open(self, app, size):
        async with app.run_test(size=size) as pilot:
            await pilot.press("escape")
            app.open_book(app.candidates[0].id)
            await pilot.pause()
            yield pilot

    async def test_no_page_overflows_the_pane(self):
        """Pages must fit the pane in both dimensions.

        Vertical overflow hides the page tail (the next page starts after
        it — the reported "pages not continuous" bug). Horizontal overflow
        makes the widget crop the tail of every long line.
        """
        for ls, ps, style in self.CASES:
            with self.subTest(ls=ls, ps=ps, style=style):
                with tempfile.TemporaryDirectory() as td:
                    app, size = self._launch(Path(td), ls, ps, style)
                    async with self._open(app, size) as pilot:
                        pane = app.query_one("#reader-pane", Static)
                        height = pane.size.height
                        width = pane.size.width
                        for _ in range(6):
                            rows = _rows(pane)
                            self.assertLessEqual(
                                len(rows),
                                height,
                                f"page at src {app.line_index} renders "
                                f"{len(rows)} rows into a {height}-row pane",
                            )
                            for row in rows:
                                self.assertLessEqual(
                                    display_width(row),
                                    width,
                                    f"row {row!r} is {display_width(row)} cols "
                                    f"wide in a {width}-col pane (would crop)",
                                )
                            await pilot.press("right")
                            await pilot.pause()

    async def test_pages_follow_each_other_without_gaps(self):
        """Content of page N+1 continues exactly where page N ended."""
        for ls, ps, style in self.CASES:
            with self.subTest(ls=ls, ps=ps, style=style):
                with tempfile.TemporaryDirectory() as td:
                    app, size = self._launch(Path(td), ls, ps, style)
                    async with self._open(app, size) as pilot:
                        pane = app.query_one("#reader-pane", Static)
                        src_nb = [ln for ln in self._src_lines(app) if ln]
                        cursor = 0
                        for page in range(5):
                            for row in _rows(pane):
                                text = _content_line(row, style)
                                if text is None:
                                    continue
                                found = next(
                                    (
                                        k
                                        for k in range(cursor, len(src_nb))
                                        if src_nb[k] == text
                                    ),
                                    None,
                                )
                                self.assertIsNotNone(
                                    found,
                                    f"page {page} row {row!r} is not a source line",
                                )
                                self.assertEqual(
                                    found,
                                    cursor,
                                    f"page {page} skipped or repeated lines "
                                    f"(expected #{cursor}, got #{found})",
                                )
                                cursor += 1
                            await pilot.press("right")
                            await pilot.pause()

    async def test_forward_then_back_returns_to_the_same_pages(self):
        for ls, ps, style in self.CASES:
            with self.subTest(ls=ls, ps=ps, style=style):
                with tempfile.TemporaryDirectory() as td:
                    app, size = self._launch(Path(td), ls, ps, style)
                    async with self._open(app, size) as pilot:
                        boundaries = [app.line_index]
                        for _ in range(4):
                            await pilot.press("right")
                            await pilot.pause()
                            boundaries.append(app.line_index)
                        for expected in reversed(boundaries[:-1]):
                            await pilot.press("left")
                            await pilot.pause()
                            self.assertEqual(app.line_index, expected)

    async def test_prev_chapter_lands_on_its_last_page(self):
        with tempfile.TemporaryDirectory() as td:
            app, size = self._launch(Path(td), 0.5, 0.5, "markdown")
            async with self._open(app, size) as pilot:
                app.chapter_index = 1
                app.line_index = 0
                app._render()
                await pilot.pause()
                self.assertEqual(app.chapter_index, 1)
                await pilot.press("left")
                await pilot.pause()
                self.assertEqual(app.chapter_index, 0)
                src = self._src_lines(app)
                start = app.line_index
                self.assertGreater(start, 0)
                # the last page is the one that reaches the end of the chapter
                self.assertGreaterEqual(
                    start + app._visible_lines(lines=src, start=start), len(src)
                )

    async def test_eof_marker_fits_inside_the_pane(self):
        with tempfile.TemporaryDirectory() as td:
            app, size = self._launch(Path(td), 0, 0, "markdown")
            async with self._open(app, size) as pilot:
                pane = app.query_one("#reader-pane", Static)
                last = len(app.current.chapters) - 1
                for _ in range(80):
                    rows = _rows(pane)
                    if app.chapter_index == last and any("-- EOF --" in r for r in rows):
                        break
                    await pilot.press("right")
                    await pilot.pause()
                rows = _rows(pane)
                if any("-- EOF --" in r for r in rows):
                    self.assertLessEqual(len(rows), pane.size.height)


if __name__ == "__main__":
    unittest.main()
