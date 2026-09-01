"""End-to-end smoke test of FishApp driven by the Textual pilot (headless).

Exercises the settings key end to end: opens the settings popup, cycles a
value, verifies the runtime config *and* fish.toml are updated, and checks
the status bar advertises [t]oc / [s]ettings.
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
from fishreader.widgets.settings_modal import SettingsModal  # noqa: E402


def _plain(widget: Static) -> str:
    content = widget.render()
    return getattr(content, "plain", str(content))


class FishAppSmokeTest(unittest.IsolatedAsyncioTestCase):
    async def test_settings_key_updates_runtime_and_fish_toml(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "books").mkdir()
            (root / "books" / "novel.txt").write_text(
                "第一章 测试\n\n正文开始。\n\n第二章 更多\n\n第二段。\n",
                encoding="utf-8",
            )
            cfg = load_config(root / "fish.toml", project_root=root)
            app = FishApp(cfg, root)
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("escape")  # close the library picker
                status = _plain(app.query_one("#statusbar", Static))
                self.assertIn("[t]", status)
                self.assertIn("[s]", status)
                await pilot.press("s")  # settings popup
                await pilot.press("right")  # font size medium -> large
                await pilot.press("escape")  # close popup
                self.assertEqual(cfg.reader["font_size"], "large")
                reloaded = load_config(root / "fish.toml", project_root=root)
                self.assertEqual(reloaded.reader["font_size"], "large")

    async def test_boss_key_works_while_settings_open(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "books").mkdir()
            (root / "books" / "novel.txt").write_text("第一章\n\n正文。\n", encoding="utf-8")
            cfg = load_config(root / "fish.toml", project_root=root)
            app = FishApp(cfg, root)
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("escape")
                await pilot.press("s")
                self.assertIsInstance(app.screen, SettingsModal)
                await pilot.press("b")  # boss key is priority: must beat the modal
                await pilot.pause()
                self.assertTrue(app._boss_mode)
                self.assertNotIsInstance(app.screen, SettingsModal)


if __name__ == "__main__":
    unittest.main()
