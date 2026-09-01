"""TXT parser: charset detection, normalization, chapter splitting."""

from __future__ import annotations

from pathlib import Path

from fishreader.models import Book

from .base import BaseParser, ParseError, build_book
from .textutils import decode_text, normalize_body, split_chapters


class TxtParser(BaseParser):
    fmt = "txt"

    def parse(self, path: Path) -> Book:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ParseError(f"cannot read {path.name}: {exc}") from exc

        if not raw:
            chapters = [("前言", "")]
        else:
            text = decode_text(raw)
            chapters = split_chapters(normalize_body(text))
            if not chapters:
                chapters = [("前言", "")]

        return build_book(
            book_id=path.as_posix(),
            path=path,
            fmt="txt",
            title=path.stem or path.name,
            author=None,
            chapters=chapters,
        )