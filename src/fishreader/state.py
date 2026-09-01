"""Reading progress persistence (JSON, atomic writes, tolerant reads).

Schema:
{
  "last_book_id": "books/novel_01.txt",
  "books": {
    "books/novel_01.txt": {
      "chapter_index": 3,
      "char_offset": 12345,
      "scroll_line": 0,
      "updated_at": "2026-08-31T12:00:00"
    }
  }
}
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ProgressStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._data: dict[str, Any] = {"last_book_id": None, "books": {}}

    # -- load -------------------------------------------------------------

    def load(self) -> "ProgressStore":
        """Read the file; any failure (missing/corrupt/invalid fields) yields
        an empty store instead of raising."""
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return self
        books = raw.get("books") if isinstance(raw, dict) else None
        if not isinstance(books, dict):
            return self
        cleaned: dict[str, Any] = {}
        for book_id, entry in books.items():
            if not isinstance(entry, dict):
                continue
            entry = {
                "chapter_index": int(entry.get("chapter_index", 0)),
                "char_offset": int(entry.get("char_offset", 0)),
                "scroll_line": int(entry.get("scroll_line", 0)),
                "updated_at": str(entry.get("updated_at", "")),
            }
            cleaned[str(book_id)] = entry
        last = raw.get("last_book_id")
        self._data = {
            "last_book_id": str(last) if isinstance(last, str) else None,
            "books": cleaned,
        }
        return self

    # -- queries -----------------------------------------------------------

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

    def last_book_id(self) -> str | None:
        return self._data.get("last_book_id")

    def get(self, book_id: str) -> dict | None:
        return self._data["books"].get(book_id)

    def all_book_ids(self) -> list[str]:
        return list(self._data["books"].keys())

    # -- mutations ---------------------------------------------------------

    def update_book(
        self,
        book_id: str,
        chapter_index: int,
        char_offset: int,
        scroll_line: int,
    ) -> None:
        self._data["books"][book_id] = {
            "chapter_index": int(chapter_index),
            "char_offset": int(char_offset),
            "scroll_line": int(scroll_line),
            "updated_at": _now_iso(),
        }

    def set_last_book(self, book_id: str | None) -> None:
        self._data["last_book_id"] = book_id

    def drop_stale(self, valid_book_ids: set[str]) -> None:
        """Remove progress entries whose book file no longer exists."""
        stale = [bid for bid in self._data["books"] if bid not in valid_book_ids]
        for bid in stale:
            del self._data["books"][bid]
        if self._data["last_book_id"] not in valid_book_ids:
            self._data["last_book_id"] = None

    # -- save ---------------------------------------------------------------

    def save(self) -> None:
        """Atomic write: temp file in the same directory, then os.replace."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            self._data, ensure_ascii=False, indent=2, sort_keys=True
        )
        fd, tmp = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=self.path.name, suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise