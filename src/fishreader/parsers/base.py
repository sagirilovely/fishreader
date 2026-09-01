"""Parser base classes and chapter/Book assembly helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from fishreader.models import Book, Chapter


class ParseError(Exception):
    """Raised when a book file cannot be parsed."""


class BaseParser(ABC):
    fmt: str = ""

    @abstractmethod
    def parse(self, path: Path) -> Book:
        """Return a parsed Book; raise ParseError on failure."""


def build_book(
    book_id: str,
    path: Path,
    fmt: str,
    title: str,
    author: str | None,
    chapters: list[tuple[str, str]],  # (title, body)
    readable: bool = True,
    reason: str | None = None,
) -> Book:
    """Assemble a Book from (title, body) chapter pairs.

    The full text is built as title + "\\n\\n" + body per chapter, joined
    with "\\n\\n"; Chapter.start_char/end_char are offsets into it.
    """
    built: list[Chapter] = []
    parts: list[str] = []
    pos = 0
    for index, (ctitle, cbody) in enumerate(chapters):
        part = f"{ctitle}\n\n{cbody}"
        parts.append(part)
        built.append(
            Chapter(
                index=index,
                title=ctitle,
                content=cbody,
                start_char=pos,
                end_char=pos + len(part),
            )
        )
        pos += len(part) + 2  # trailing "\n\n" separator (except on the last)

    full_text = "\n\n".join(parts)
    return Book(
        id=book_id,
        path=path,
        fmt=fmt,
        title=title,
        author=author,
        chapters=built,
        readable=readable,
        reason=reason,
        total_chars=len(full_text),
        full_text=full_text,
    )


def unreadable_book(
    book_id: str, path: Path, fmt: str, title: str, reason: str
) -> Book:
    return Book(
        id=book_id,
        path=path,
        fmt=fmt,
        title=title,
        author=None,
        chapters=[],
        readable=False,
        reason=reason,
        total_chars=0,
        full_text="",
    )