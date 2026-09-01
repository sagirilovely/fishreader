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

# What FishApp builds for the spacing rows (0 = auto, then 0.25 steps).
FRACTIONAL_ROWS = [
    ("reader", "line_spacing", "line spacing",
     [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0], {0.0: "auto"}),
]
FRACTIONAL_VALUES = {("reader", "line_spacing"): 1.0}


class _Harness(App):
    def __init__(self, changes, rows=ROWS, values=VALUES):
        super().__init__()
        self.changes = changes
        self.rows = rows
        self.values = values

    def on_mount(self):
        self.push_screen(
            SettingsModal(
                self.rows,
                self.values,
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

    async def test_fractional_spacing_steps(self):
        """The spacing row must step by 0.25, not by whole blank lines."""
        changes = []
        app = _Harness(changes, FRACTIONAL_ROWS, FRACTIONAL_VALUES)
        async with app.run_test() as pilot:
            await pilot.press("left")             # 1.0 -> 0.75
            self.assertEqual(changes[-1], ("reader", "line_spacing", 0.75))
            await pilot.press("left", "left")     # 0.75 -> 0.5 -> 0.25
            self.assertEqual(changes[-1], ("reader", "line_spacing", 0.25))
            await pilot.press("left")             # 0.25 -> 0.0 (auto)
            self.assertEqual(changes[-1], ("reader", "line_spacing", 0.0))
            await pilot.press("right")            # auto -> 0.25
            self.assertEqual(changes[-1], ("reader", "line_spacing", 0.25))
            await pilot.press("escape")
        self.assertEqual([c[2] for c in changes], [0.75, 0.5, 0.25, 0.0, 0.25])


if __name__ == "__main__":
    unittest.main()
