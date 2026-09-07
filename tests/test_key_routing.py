"""Arrow keys must belong to the reader, never to the decorative log.

Regression guards:
- ↑/↓ used to be eaten by the focused RichLog, so "scroll one line" was
  silently dead.
- ←/→ stopped paging once the log had horizontal scroll range (right after
  the boss key resizes the pane), because RichLog's scroll_left/scroll_right
  took over.
"""

import sys
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.app import FishApp  # noqa: E402
from fishreader.config import load_config  # noqa: E402
from fishreader.widgets.agent_log import AgentLog  # noqa: E402

# one long chapter so scrolling stays inside it
BODY = "第一章 开端\n\n" + "正文内容。" * 200 + "\n"


class ArrowKeyRoutingTest(unittest.IsolatedAsyncioTestCase):
    @asynccontextmanager
    async def _open(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "books").mkdir()
            (root / "books" / "novel.txt").write_text(BODY, encoding="utf-8")
            cfg = load_config(root / "fish.toml", project_root=root)
            app = FishApp(cfg, root)
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("escape")
                app.open_book(app.candidates[0].id)
                await pilot.pause()
                yield app, pilot

    def test_log_is_decoration_only(self):
        self.assertFalse(AgentLog.can_focus)
        keys = {str(b.key) for b in AgentLog.BINDINGS}
        for arrow in ("up", "down", "left", "right"):
            self.assertNotIn(arrow, keys)

    async def test_up_is_the_emergency_boss_key(self):
        async with self._open() as (app, pilot):
            self.assertFalse(app._boss_mode)
            await pilot.press("up")
            await pilot.pause()
            self.assertTrue(app._boss_mode)
            await pilot.press("up")
            await pilot.pause()
            self.assertFalse(app._boss_mode)

    async def test_down_scrolls_the_reader_one_line(self):
        async with self._open() as (app, pilot):
            self.assertEqual(app.line_index, 0)
            await pilot.press("down")
            await pilot.pause()
            self.assertEqual(app.line_index, 1)  # eaten by the log before the fix

    async def test_paging_survives_a_boss_mode_round_trip(self):
        """The reported bug: → stopped paging after ↑/老板键 hide+restore."""
        async with self._open() as (app, pilot):
            before = (app.chapter_index, app.line_index)
            await pilot.press("up")  # hide the reader
            await pilot.pause()
            await pilot.press("up")  # restore
            await pilot.pause()
            self.assertFalse(app._boss_mode)
            await pilot.press("right")
            await pilot.pause()
            self.assertNotEqual(
                (app.chapter_index, app.line_index),
                before,
                "→ was swallowed by the log pane after the boss key resized it",
            )

    async def test_arrow_keys_never_scroll_the_log_horizontally(self):
        async with self._open() as (app, pilot):
            log = app.query_one("#agent-log")
            self.assertEqual(log.scroll_offset.x, 0)
            for key in ("right", "left", "up", "down"):
                await pilot.press(key)
                await pilot.pause()
            self.assertEqual(log.scroll_offset.x, 0)


if __name__ == "__main__":
    unittest.main()
