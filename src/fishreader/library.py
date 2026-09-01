"""Book scanning and parse-on-demand loading."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fishreader.config import Config
from fishreader.models import Book

from .parsers import ParseError, get_parser
from .parsers.base import unreadable_book

FMT_ORDER = {"txt": 0, "epub": 1, "mobi": 2}


def natural_key(name: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


@dataclass
class Candidate:
    id: str       # stable id: posix path relative to project root,
                  # or absolute path for scan dirs outside the root
    path: Path
    fmt: str
    size: int

    @property
    def display_name(self) -> str:
        return self.path.name


def scan_library(config: Config) -> list[Candidate]:
    """Recursively scan configured directories for supported books.

    Skips hidden files/directories and system temporaries. Sorted by format
    (txt < epub < mobi) then natural filename order.
    """
    extensions = config.extensions()
    found: list[Candidate] = []
    for base in config.scan_dirs():
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part.startswith(".") for part in p.relative_to(base).parts):
                continue  # hidden files / directories
            if p.name.startswith((".", "~", "#")) or p.name.endswith(("~", ".tmp")):
                continue  # editor temp files
            ext = p.suffix.lower()
            if ext not in extensions:
                continue
            try:
                cid = p.relative_to(config.root).as_posix()
            except ValueError:
                cid = str(p)  # scan dir outside the project root
            found.append(
                Candidate(
                    id=cid,
                    path=p,
                    fmt=ext.lstrip("."),
                    size=p.stat().st_size,
                )
            )
    found.sort(key=lambda c: (FMT_ORDER.get(c.fmt, 9), natural_key(c.path.name)))
    return found


def load_book(candidate: Candidate, config: Config) -> Book:
    """Parse a candidate into a Book; failures produce an unreadable Book.

    A single bad file never raises into the caller.
    """
    parser = get_parser(candidate.fmt, config)
    if parser is None:
        return unreadable_book(
            candidate.id, candidate.path, candidate.fmt,
            candidate.path.stem, f"unsupported format: .{candidate.fmt}",
        )
    try:
        book = parser.parse(candidate.path)
        book.id = candidate.id
        return book
    except ParseError as exc:
        return unreadable_book(
            candidate.id, candidate.path, candidate.fmt,
            candidate.path.stem, str(exc),
        )
    except Exception as exc:  # defensive: never crash the app
        return unreadable_book(
            candidate.id, candidate.path, candidate.fmt,
            candidate.path.stem, f"parse error: {exc}",
        )