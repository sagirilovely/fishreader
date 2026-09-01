"""Tests for the CLI bootstrap (project root resolution)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fishreader import cli


class ProjectRootTest(unittest.TestCase):
    def _make_repo(self, base: Path) -> Path:
        """Minimal repo layout: <base>/run.py + <base>/src/fishreader/cli.py."""
        pkg = base / "src" / "fishreader"
        pkg.mkdir(parents=True)
        (base / "run.py").write_text("", encoding="utf-8")
        (pkg / "cli.py").write_text("", encoding="utf-8")
        return base

    def test_resolves_repo_root_from_package_location(self):
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(Path(td))
            fake_pkg = repo / "src" / "fishreader" / "cli.py"
            with mock.patch("fishreader.cli.__file__", str(fake_pkg)):
                self.assertEqual(cli._project_root(), repo.resolve())

    def test_falls_back_to_cwd_without_repo_marker(self):
        with tempfile.TemporaryDirectory() as td:
            pkg_dir = Path(td) / "site-packages" / "fishreader"
            pkg_dir.mkdir(parents=True)
            fake_pkg = pkg_dir / "cli.py"
            self.assertFalse((Path(td) / "run.py").exists())
            old_cwd = os.getcwd()
            try:
                os.chdir(td)
                with mock.patch("fishreader.cli.__file__", str(fake_pkg)):
                    self.assertEqual(cli._project_root(), Path(td).resolve())
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()