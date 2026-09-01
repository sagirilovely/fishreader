"""Unit tests for ClaudeRobotPane."""

import unittest
from pathlib import Path
from rich.text import Text
from fishreader.widgets.claude_robot import ClaudeRobotPane, MASCOT_FRAMES


class ClaudeRobotTest(unittest.TestCase):
    def test_mascot_frames_defined(self):
        self.assertGreaterEqual(len(MASCOT_FRAMES), 4)
        for frame in MASCOT_FRAMES:
            self.assertGreaterEqual(len(frame), 5)
            for line in frame:
                self.assertIsInstance(line, str)

    def test_claude_pane_init_and_render(self):
        pane = ClaudeRobotPane(project_root=Path('/Users/sagiri/Desktop/fish'))
        self.assertIn('fish', pane.display_path)
        pane._render_frame()
        self.assertIsInstance(pane._current_text, Text)
        rendered_str = str(pane._current_text)
        self.assertIn('Claude Code', rendered_str)
        self.assertIn('claude-opus-4-8', rendered_str)

    def test_animation_tick_advances_frame(self):
        pane = ClaudeRobotPane()
        initial_frame = pane._frame_idx
        pane._tick()
        self.assertEqual(pane._frame_idx, (initial_frame + 1) % len(MASCOT_FRAMES))


if __name__ == '__main__':
    unittest.main()
