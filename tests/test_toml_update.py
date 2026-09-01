"""Tests for config.apply_toml_update: in-place key updates from the app.

The in-app settings menu mutates fish.toml one key at a time; comments and
unrelated keys must survive, missing keys/sections must be created, and the
file must stay valid TOML (validated before any write).
"""

import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.config import (  # noqa: E402
    DEFAULT_CONFIG_TEXT,
    apply_toml_update,
    load_config,
)


class ApplyTomlUpdateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_update_preserves_comments_and_other_keys(self):
        p = self.root / "fish.toml"
        p.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        apply_toml_update(p, "reader", {"font_size": "large"})
        text = p.read_text(encoding="utf-8")
        self.assertIn('font_size = "large"', text)
        self.assertIn("small | medium | large", text)  # trailing comment kept
        self.assertIn('novel_style = "markdown"', text)  # sibling key untouched
        self.assertIn("log_style = \"agent\"", text)
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.reader["font_size"], "large")

    def test_update_appends_missing_key_at_section_end(self):
        p = self.root / "fish.toml"
        p.write_text('[reader]\nfont_size = "medium"\n\n[disguise]\nlog_style = "agent"\n',
                     encoding="utf-8")
        apply_toml_update(p, "reader", {"novel_style": "comment"})
        text = p.read_text(encoding="utf-8")
        self.assertIn('novel_style = "comment"', text)
        self.assertLess(text.index("novel_style"), text.index("[disguise]"))
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.reader["novel_style"], "comment")

    def test_update_creates_missing_section(self):
        p = self.root / "fish.toml"
        p.write_text('[books]\nextensions = [".txt"]\n', encoding="utf-8")
        apply_toml_update(p, "disguise", {"log_style": "vite"})
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.disguise["log_style"], "vite")

    def test_repeated_updates_do_not_duplicate_keys(self):
        p = self.root / "fish.toml"
        p.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        apply_toml_update(p, "reader", {"line_spacing": 1})
        apply_toml_update(p, "reader", {"line_spacing": 2})
        text = p.read_text(encoding="utf-8")
        self.assertEqual(text.count("line_spacing ="), 1)
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.reader["line_spacing"], 2)

    def test_write_is_atomic_and_leaves_valid_file(self):
        p = self.root / "fish.toml"
        p.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        apply_toml_update(p, "disguise", {"log_style": "git"})
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.disguise["log_style"], "git")
        # no leftover temp files
        leftovers = [q.name for q in self.root.iterdir() if q.name != "fish.toml"]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
