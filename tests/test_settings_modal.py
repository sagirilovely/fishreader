"""Pilot tests for the settings modal (arrow cycling + live apply callback)."""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from textual.app import App  # noqa: E402

from fishreader.widgets.settings_modal import SettingsModal  # noqa: E402

ROWS = [
    ("reader", "font_size", "font size", ["small", "medium", "large"], {}),
    ("reader", "reader_position", "reader position", ["left", "right", "bottom"], {}),
    ("reader", "line_spacing", "line spacing", [0, 1, 2], {0: "auto"}),
]
VALUES = {
    ("reader", "font_size"): "medium",
    ("reader", "reader_position"): "right",
    ("reader", "line_spacing"): 0,
}


class _Harness(App):
    def __init__(self, changes):
        super().__init__()
        self.changes = changes

    def on_mount(self):
        self.push_screen(
            SettingsModal(
                ROWS,
                VALUES,
                lambda s, k, v: self.changes.append((s, k, v)),
            )
        )


class SettingsModalTest(unittest.IsolatedAsyncioTestCase):
    async def test_cycle_apply_and_wrap(self):
        changes = []
        app = _Harness(changes)
        async with app.run_test() as pilot:
            await pilot.press("right")            # font size medium -> large
            self.assertEqual(changes[-1], ("reader", "font_size", "large"))
            await pilot.press("down")             # -> reader position
            await pilot.press("right")            # right -> bottom
            self.assertEqual(changes[-1], ("reader", "reader_position", "bottom"))
            await pilot.press("down")             # -> line spacing
            await pilot.press("right")            # 0 -> 1
            self.assertEqual(changes[-1], ("reader", "line_spacing", 1))
            await pilot.press("left")             # 1 -> 0
            self.assertEqual(changes[-1], ("reader", "line_spacing", 0))
            await pilot.press("right", "right")   # 0 -> 1 -> 2
            self.assertEqual(changes[-1], ("reader", "line_spacing", 2))
            await pilot.press("escape")
        self.assertEqual(changes[0], ("reader", "font_size", "large"))

    async def test_cycling_wraps_around(self):
        changes = []
        app = _Harness(changes)
        async with app.run_test() as pilot:
            await pilot.press("left")             # medium -> small
            self.assertEqual(changes[-1], ("reader", "font_size", "small"))
            await pilot.press("left")             # small -> large (wrap)
            self.assertEqual(changes[-1], ("reader", "font_size", "large"))
            await pilot.press("q")
        self.assertEqual(len(changes), 2)


if __name__ == "__main__":
    unittest.main()
