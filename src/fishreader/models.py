"""Core data models: Chapter and Book."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chapter:
    index: int
    title: str
    content: str  # pure text, paragraphs separated by blank lines
    start_char: int = 0  # offset of the title in the book's full_text
    end_char: int = 0    # offset one past the last char of the chapter content


@dataclass
class Book:
    id: str               # stable id: relative posix path from project root
    path: Path
    fmt: str              # txt / epub / mobi
    title: str
    author: str | None
    chapters: list[Chapter]
    readable: bool
    reason: str | None    # human-readable reason when readable is False
    total_chars: int
    full_text: str = ""   # all chapters joined; used for char-based pagination

    @property
    def is_unsupported(self) -> bool:
        return not self.readable

    def chapter_index_at(self, char_offset: int) -> int:
        """Index of the chapter containing char_offset (binary search)."""
        lo, hi = 0, len(self.chapters)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.chapters[mid].start_char <= char_offset:
                lo = mid + 1
            else:
                hi = mid
        return max(0, lo - 1)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)