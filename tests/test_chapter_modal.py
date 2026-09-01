"""Tests for the table of contents (t key): cursor memory + status bar.

Regression: reopening the TOC used to show the list from the very top with
the highlight on chapter 1, even after jumping deep into the book (say
chapter 100) — the "current" marker existed but nothing scrolled to it.
"""

import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from textual.widgets import Static  # noqa: E402

from fishreader.app import FishApp  # noqa: E402
from fishreader.config import load_config  # noqa: E402
from fishreader.widgets.chapter_modal import ChapterModal  # noqa: E402


def _plain(widget: Static) -> str:
    content = widget.render()
    return getattr(content, "plain", str(content))


def _book_text(n: int) -> str:
    return "\n\n".join(
        f"第{i}章 测试章节{i}\n\n这一章的正文内容。" * 2 for i in range(1, n + 1)
    ) + "\n"


class TocCursorTest(unittest.IsolatedAsyncioTestCase):
    def _launch(self, tmp: Path, chapters: int = 30):
        (tmp / "books").mkdir()
        (tmp / "books" / "novel.txt").write_text(
            _book_text(chapters), encoding="utf-8"
        )
        cfg = load_config(tmp / "fish.toml", project_root=tmp)
        return FishApp(cfg, tmp)

    async def test_toc_opens_on_the_current_chapter(self):
        with tempfile.TemporaryDirectory() as td:
            app = self._launch(Path(td))
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("escape")
                app.open_book(app.candidates[0].id)
                await pilot.pause()
                # simulate a reader deep in the book
                app.chapter_index = 19
                app.line_index = 0
                app._render()
                await pilot.press("t")
                await pilot.pause()
                self.assertIsInstance(app.screen, ChapterModal)
                modal = app.screen
                self.assertEqual(modal._list.index, 19)
                await pilot.press("escape")

    async def test_toc_scrolls_the_current_chapter_into_view(self):
        with tempfile.TemporaryDirectory() as td:
            app = self._launch(Path(td), chapters=120)
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("escape")
                app.open_book(app.candidates[0].id)
                await pilot.pause()
                app.chapter_index = 99  # far past the first screenful
                app.line_index = 0
                app._render()
                await pilot.press("t")
                await pilot.pause()
                await pilot.pause()  # let the deferred centering run
                modal = app.screen
                # if it still showed the top of the list, this would be 0
                self.assertGreater(modal._list.scroll_offset.y, 0)
                await pilot.press("escape")

    async def test_toc_enter_jumps_and_statusbar_follows(self):
        with tempfile.TemporaryDirectory() as td:
            app = self._launch(Path(td))
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("escape")
                app.open_book(app.candidates[0].id)
                await pilot.pause()
                await pilot.press("t")
                await pilot.pause()
                modal = app.screen
                self.assertEqual(modal._list.index, 0)
                modal._list.index = 12
                await pilot.press("enter")
                await pilot.pause()
                self.assertEqual(app.chapter_index, 12)
                status = _plain(app.query_one("#statusbar", Static))
                self.assertIn("chap 13/30", status)
                self.assertNotIn("chap 1/30 |", status.replace("chap 13/30", ""))


if __name__ == "__main__":
    unittest.main()
