"""Unit tests for fishreader.config (load, validation, defaults, accessors).

Covers the test points from docs/开发文档.md §7.1:
defaults generation, user overrides, invalid-value validation, deep merge.
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
    FONT_SIZE_SPACING,
    Config,
    ConfigError,
    load_config,
)


def _write_toml(directory: Path, name: str, body: str) -> Path:
    p = directory / name
    p.write_text(body, encoding="utf-8")
    return p


class ConfigDefaultsTest(unittest.TestCase):
    """Default file generation and default values."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_missing_file_generates_default_with_comments(self):
        path = self.root / "fish.toml"
        cfg = load_config(path, project_root=self.root)
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        # generated file carries the documented commented sample
        self.assertIn("# fish.toml", text)
        self.assertIn("[books]", text)
        self.assertIn("[reader]", text)
        self.assertIn("reader_width", text)
        self.assertIn("autosave_on_page", text)
        self.assertEqual(cfg.path, path)
        self.assertEqual(cfg.root, self.root)

    def test_generated_defaults_used(self):
        cfg = load_config(self.root / "fish.toml", project_root=self.root)
        self.assertEqual(cfg.reader["font_size"], "medium")
        self.assertEqual(cfg.reader["reader_width"], "30%")
        self.assertEqual(cfg.reader["reader_position"], "right")
        self.assertEqual(cfg.reader["novel_style"], "markdown")
        self.assertEqual(cfg.disguise["log_interval_min"], 0.8)
        self.assertEqual(cfg.disguise["log_interval_max"], 1.5)
        self.assertEqual(cfg.disguise["status_line"], "minimal")
        self.assertEqual(cfg.books["extensions"], [".epub", ".mobi", ".txt"])
        self.assertIs(cfg.autosave_on_page(), True)

    def test_create_if_missing_false_does_not_write(self):
        path = self.root / "nope.toml"
        cfg = load_config(path, project_root=self.root, create_if_missing=False)
        self.assertFalse(path.exists())
        self.assertEqual(cfg.reader["reader_width"], "30%")
        # root falls back to path.parent when project_root is not given
        cfg2 = load_config(self.root / "x.toml", create_if_missing=False)
        self.assertEqual(cfg2.root, self.root)


class ConfigOverrideTest(unittest.TestCase):
    """User overrides, deep merge, unknown keys."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_partial_override_keeps_other_defaults(self):
        p = _write_toml(
            self.root,
            "over.toml",
            '[reader]\nfont_size = "large"\nreader_width = "35%"',
        )
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.reader["font_size"], "large")
        self.assertEqual(cfg.reader["reader_width"], "35%")
        # untouched sibling sections keep defaults
        self.assertEqual(cfg.theme["accent"], "green")
        self.assertEqual(cfg.disguise["agent_name"], "CodeAgent")
        self.assertEqual(cfg.progress["file"], ".fish_progress.json")

    def test_unknown_keys_ignored(self):
        p = _write_toml(
            self.root,
            "unknown.toml",
            'mystery = 1\n[reader]\noutlandish = true\nfont_size = "small"\n'
            "[disguise]\nfoo_bar = 42\n",
        )
        cfg = load_config(p, project_root=self.root)
        self.assertNotIn("mystery", cfg.raw)
        self.assertNotIn("outlandish", cfg.reader)
        self.assertNotIn("foo_bar", cfg.disguise)
        self.assertEqual(cfg.reader["font_size"], "small")

    def test_override_is_not_mutating_defaults(self):
        p = _write_toml(self.root, "a.toml", '[reader]\nfont_size = "large"')
        load_config(p, project_root=self.root)
        # a fresh load of a default file still sees defaults
        d = load_config(self.root / "b.toml", project_root=self.root)
        self.assertEqual(d.reader["font_size"], "medium")

    def test_extensions_normalized(self):
        p = _write_toml(
            self.root,
            "ext.toml",
            '[books]\nextensions = ["EPUB", ".TXT", "mobi"]',
        )
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.extensions(), (".epub", ".txt", ".mobi"))

    def test_bad_toml_syntax_raises(self):
        p = _write_toml(self.root, "bad.toml", "[reader\nnope")
        with self.assertRaises(ConfigError):
            load_config(p)


class ConfigValidationTest(unittest.TestCase):
    """Invalid values raise ConfigError; boundary values are accepted."""

    INVALID_CASES = [
        # (toml body, message fragment)
        ('[reader]\nreader_width = "24%"', "reader_width"),
        ('[reader]\nreader_width = "41%"', "reader_width"),
        ('[reader]\nreader_width = "abc%"', "reader_width"),
        ('[reader]\nreader_width = "1%x"', "reader_width"),
        ('[reader]\nreader_width = 7', "reader_width"),
        ('[reader]\nreader_width = "wide"', "reader_width"),
        ('[reader]\nreader_width = 3.5', "reader_width"),
        ('[reader]\nfont_size = "huge"', "font_size"),
        ('[reader]\nnovel_style = "html"', "novel_style"),
        ('[reader]\nreader_position = "top"', "reader_position"),
        ('[reader]\nline_spacing = 5', "line_spacing"),
        ('[reader]\nline_spacing = 1.5', "line_spacing"),
        ('[reader]\nparagraph_spacing = -1', "paragraph_spacing"),
        ('[disguise]\nlog_interval_min = 2.0\nlog_interval_max = 1.0',
         "log_interval"),
        ('[disguise]\nlog_interval_min = 0', "log_interval"),
        ('[disguise]\nlog_interval_min = -1', "log_interval"),
        ('[disguise]\nstatus_line = "fullx"', "status_line"),
        ('[disguise]\nboss_key = "esc"', "boss_key"),
        ('[disguise]\nboss_key = ""', "boss_key"),
        ('[disguise]\nlog_style = "chinese"', "log_style"),
        ("[books]\nextensions = []", "extensions"),
        ("[books]\nextensions = [1, 2]", "extensions"),
        ("[books]\nextensions = ['ok', 3]", "extensions"),
    ]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_invalid_values_raise_config_error(self):
        for i, (body, fragment) in enumerate(self.INVALID_CASES):
            with self.subTest(body=body):
                p = _write_toml(self.root, f"bad{i}.toml", body)
                with self.assertRaises(ConfigError) as ctx:
                    load_config(p, project_root=self.root)
                self.assertIn(fragment, str(ctx.exception))

    def test_boundary_widths_accepted(self):
        for width in ("25%", "40%", 8, 12, 200):
            with self.subTest(width=width):
                p = _write_toml(
                    self.root,
                    f"w{str(width).replace('%', 'pct')}.toml",
                    f'[reader]\nreader_width = {width!r}'.replace("'", '"'),
                )
                cfg = load_config(p, project_root=self.root)
                self.assertEqual(cfg.reader["reader_width"], width)

    def test_log_style_values_accepted(self):
        for style in ("agent", "vite", "npm", "git"):
            with self.subTest(style=style):
                p = _write_toml(
                    self.root,
                    f"ls-{style}.toml",
                    f'[disguise]\nlog_style = "{style}"',
                )
                cfg = load_config(p, project_root=self.root)
                self.assertEqual(cfg.disguise["log_style"], style)

    def test_legacy_english_log_style_normalized(self):
        p = _write_toml(self.root, "ls-legacy.toml", '[disguise]\nlog_style = "english"')
        cfg = load_config(p, project_root=self.root)
        self.assertEqual(cfg.disguise["log_style"], "agent")

    def test_reader_positions_accepted(self):
        for pos in ("left", "right", "bottom"):
            with self.subTest(pos=pos):
                p = _write_toml(
                    self.root,
                    f"pos-{pos}.toml",
                    f'[reader]\nreader_position = "{pos}"',
                )
                cfg = load_config(p, project_root=self.root)
                self.assertEqual(cfg.reader["reader_position"], pos)


class ConfigAccessorTest(unittest.TestCase):
    """Accessors: effective_spacing, reader_width_columns, paths, flags."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _config_with(self, body: str) -> Config:
        p = _write_toml(self.root, "cfg.toml", body)
        return load_config(p, project_root=self.root)

    def test_effective_spacing_font_mapping(self):
        for size, expected in FONT_SIZE_SPACING.items():
            with self.subTest(size=size):
                cfg = self._config_with(f'[reader]\nfont_size = "{size}"')
                self.assertEqual(cfg.effective_spacing(), expected)
        # default medium
        cfg = load_config(self.root / "d.toml", project_root=self.root)
        self.assertEqual(cfg.effective_spacing(), (0, 1))

    def test_effective_spacing_explicit_override(self):
        # any non-zero explicit value overrides the font_size mapping
        cfg = self._config_with('[reader]\nfont_size = "small"\nline_spacing = 2')
        self.assertEqual(cfg.effective_spacing(), (2, 0))
        cfg = self._config_with('[reader]\nfont_size = "large"\nparagraph_spacing = 1')
        self.assertEqual(cfg.effective_spacing(), (0, 1))

    def test_reader_width_columns(self):
        cfg = load_config(self.root / "d.toml", project_root=self.root)  # 30%
        self.assertEqual(cfg.reader_width_columns(100), 30)
        self.assertEqual(cfg.reader_width_columns(30), 9)
        cfg = self._config_with("[reader]\nreader_width = 20")
        self.assertEqual(cfg.reader_width_columns(80), 20)
        # clamped into the terminal
        self.assertLessEqual(cfg.reader_width_columns(80), 79)
        self.assertGreaterEqual(cfg.reader_width_columns(2), 1)

    def test_scan_dirs_resolution(self):
        cfg = load_config(self.root / "d.toml", project_root=self.root)
        self.assertEqual(cfg.scan_dirs(), [self.root / "books"])
        outside = self.root / "elsewhere"
        outside.mkdir()
        cfg = self._config_with(f'[books]\nscan_dirs = ["{outside}"]')
        self.assertEqual(cfg.scan_dirs(), [outside])

    def test_progress_path(self):
        cfg = load_config(self.root / "d.toml", project_root=self.root)
        self.assertEqual(cfg.progress_path(), self.root / ".fish_progress.json")
        cfg = self._config_with('[progress]\nfile = "state/pos.json"')
        self.assertEqual(cfg.progress_path(), self.root / "state/pos.json")
        cfg = self._config_with(f'[progress]\nfile = "{self.root}/abs.json"')
        self.assertEqual(cfg.progress_path(), self.root / "abs.json")

    def test_autosave_on_page(self):
        cfg = load_config(self.root / "d.toml", project_root=self.root)
        self.assertTrue(cfg.autosave_on_page())
        cfg = self._config_with("[progress]\nautosave_on_page = false")
        self.assertFalse(cfg.autosave_on_page())

    def test_misc_accessors(self):
        cfg = load_config(self.root / "d.toml", project_root=self.root)
        self.assertEqual(cfg.novel_style, "markdown")
        self.assertEqual(cfg.boss_key, "b")
        self.assertEqual(cfg.agent_name, "CodeAgent")
        self.assertEqual(cfg.agent_version, "0.4.2")
        self.assertEqual(cfg.log_interval_range(), (0.8, 1.5))
        self.assertEqual(cfg.disguise["status_line"], "minimal")
        self.assertIs(cfg.reader["resume_last"], True)

    def test_reader_width_fraction(self):
        cfg = load_config(self.root / "d.toml", project_root=self.root)  # 30%
        self.assertAlmostEqual(cfg.reader_width_fraction(), 0.3)
        cfg = self._config_with("[reader]\nreader_width = 40")
        frac = cfg.reader_width_fraction()
        self.assertGreaterEqual(frac, 0.2)
        self.assertLessEqual(frac, 0.5)


if __name__ == "__main__":
    unittest.main()