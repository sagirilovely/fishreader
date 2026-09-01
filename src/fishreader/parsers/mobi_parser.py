"""MOBI parser: extract via the `mobi` package (or kindleunpack fallback).

A failed extract (DRM, unsupported format, missing dependency) raises
ParseError with a readable reason; library.py turns that into an
unreadable Book so other books are never blocked.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseParser, ParseError, build_book
from .textutils import html_to_text, split_chapters


def _largest_html(dirpath: Path) -> Path:
    htmls = [p for p in dirpath.rglob("*.html") if p.is_file()]
    htmls.extend(p for p in dirpath.rglob("*.htm") if p.is_file())
    if not htmls:
        raise ParseError("MOBI extracted but no HTML content found")
    return max(htmls, key=lambda p: p.stat().st_size)


def _try_kindleunpack(path: Path, out_dir: Path) -> Path:
    """Fallback: pull text via the kindleunpack CLI if available."""
    exe = shutil.which("kindleunpack")
    if exe is None:
        raise ParseError("kindleunpack not found on PATH")
    try:
        proc = subprocess.run(
            [exe, str(path), str(out_dir)],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ParseError(f"kindleunpack failed: {exc}") from exc
    if proc.returncode != 0:
        raise ParseError(
            f"kindleunpack failed: {proc.stderr.strip() or proc.stdout.strip() or 'exit ' + str(proc.returncode)}"
        )
    return _largest_html(out_dir)


class MobiParser(BaseParser):
    fmt = "mobi"

    def __init__(self, allow_kindleunpack: bool = False):
        self.allow_kindleunpack = allow_kindleunpack

    def _extract_html(self, path: Path) -> Path:
        try:
            import mobi
        except ImportError as exc:
            raise ParseError("mobi package not installed (pip install mobi)") from exc

        try:
            tempdir, filepath = mobi.extract(str(path))
        except Exception:
            if self.allow_kindleunpack:
                out = Path(tempfile.mkdtemp(prefix="fishreader_kup_"))
                try:
                    return _try_kindleunpack(path, out)
                except ParseError:
                    shutil.rmtree(out, ignore_errors=True)
                    raise
            raise ParseError("DRM protected or unsupported MOBI")
        else:
            extracted = Path(filepath)
            if extracted.is_dir():
                extracted = _largest_html(extracted)
            return extracted

    def parse(self, path: Path) -> Book:
        html_path = self._extract_html(path)
        hook_dir = html_path  # keep for cleanup
        try:
            html = html_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise ParseError(f"cannot read extracted MOBI HTML: {exc}") from exc
        finally:
            # mobi.extract cleans its own temp dir on failure only; drop the
            # directory we were handed to avoid leaking temp files.
            import os

            parent = html_path.parent
            if "fishreader_kup_" in parent.name or parent.name.startswith("mobi"):
                shutil.rmtree(parent, ignore_errors=True)

        text = html_to_text(html)
        chapters = split_chapters(text) if text.strip() else [("前言", "")]
        return build_book(
            book_id=path.as_posix(),
            path=path,
            fmt="mobi",
            title=path.stem,
            author=None,
            chapters=chapters,
        )