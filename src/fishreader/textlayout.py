"""Display width, text wrapping and pagination.

CJK width is handled via unicodedata.east_asian_width ('W'/'F' count as 2)
so wrapping and page geometry stay correct on mixed-script text.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

WIDE = ("W", "F")

# Characters that must not start a line (hang onto the previous line).
START_FORBIDDEN = set("。，、！？；：）】》」』…—”’")

TAB_WIDTH = 4


def char_width(ch: str) -> int:
    if ch == "\t":
        return TAB_WIDTH
    return 2 if unicodedata.east_asian_width(ch) in WIDE else 1


def display_width(s: str) -> int:
    """Visible width of a string (tabs count as 4 spaces)."""
    return sum(char_width(ch) for ch in s)


def _is_word_char(ch: str) -> bool:
    return (ch.isascii() and ch.isalnum()) or ch == "_"


def _wrap_para(para: str, width: int) -> list[tuple[str, int]]:
    """Greedy-wrap one paragraph.

    Returns a list of (line_text, consumed) where consumed is the number of
    source characters (from the start of para) that the line covers.
    """
    if not para:
        return [("", 0)]
    out: list[tuple[str, int]] = []
    line = ""
    w = 0
    pos = 0
    n = len(para)
    while pos < n:
        ch = para[pos]
        if _is_word_char(ch):
            end = pos
            while end < n and _is_word_char(para[end]):
                end += 1
            word = para[pos:end]
            if line and w + len(word) > width:
                out.append((line.rstrip(), pos))
                line, w = "", 0
            if len(word) > width:
                if line:
                    out.append((line.rstrip(), pos))
                    line, w = "", 0
                k = 0
                while k < len(word):
                    out.append((word[k : k + width], pos + min(k + width, len(word))))
                    k += width
                pos = end
                continue
            line += word
            w += len(word)
            pos = end
            continue

        cw = char_width(ch)
        if w + cw > width:
            # Flush the full line, then hang closing punctuation on to it so
            # it never starts the next line (行首禁则).
            out.append((line.rstrip(), pos))
            if ch in START_FORBIDDEN and out[-1][0]:
                out[-1] = (out[-1][0] + ch, pos + 1)
                line, w = "", 0
                pos += 1
                continue
            line, w = "", 0
            if ch == " ":
                pos += 1
                continue
        if ch != " " or line:  # drop leading spaces, keep interior ones
            line += ch
            w += cw
        pos += 1
    out.append((line.rstrip(), pos))
    return out


def wrap_text_with_offsets(text: str, width: int) -> list[tuple[str, int]]:
    """Wrap text to `width` columns.

    Explicit newlines are preserved: a blank line stays a blank line
    (paragraph boundary). Returns (line, char_offset) pairs where
    char_offset is the offset of the line in `text`.
    """
    if width < 1:
        width = 1
    result: list[tuple[str, int]] = []
    pos = 0
    for para in text.split("\n"):
        if not para:
            result.append(("", pos))
            pos += 1  # the newline itself
            continue
        for line, consumed in _wrap_para(para, width):
            result.append((line, pos))
        pos += len(para) + 1
    return result


def wrap_text(text: str, width: int) -> list[str]:
    return [line for line, _ in wrap_text_with_offsets(text, width)]


@dataclass
class Page:
    lines: list[str]
    first_char_offset: int
    next_page_start: int
    chapter_index: int
    eof: bool = False
    # bookkeeping for tests / status bar
    total_lines: int = 0


def chapter_index_at(chapters: list, char_offset: int) -> int:
    """Index of the chapter containing char_offset (binary search)."""
    lo, hi = 0, len(chapters)
    while lo < hi:
        mid = (lo + hi) // 2
        if chapters[mid].start_char <= char_offset:
            lo = mid + 1
        else:
            hi = mid
    return max(0, lo - 1)


def paginate(
    chapters: list,
    text: str,
    start_char: int,
    box_width: int,
    box_height: int,
    line_spacing: int = 0,
) -> Page:
    """Produce one page of `box_height` visible lines starting at start_char.

    Returns the page lines, the first char offset (= start_char), the char
    offset where the next page begins, and the containing chapter index.
    """
    if box_width < 1:
        box_width = 1
    if box_height < 1:
        box_height = 1
    total = len(text)
    start_char = max(0, min(start_char, total))
    ci = chapter_index_at(chapters, start_char)

    if start_char >= total:
        return Page([], start_char, start_char, ci, eof=True, total_lines=total)

    wrapped = wrap_text_with_offsets(text[start_char:], box_width)
    if not wrapped:
        return Page([], start_char, start_char, ci, eof=start_char >= total)

    visible = max(1, box_height // (1 + line_spacing))
    page_lines = [line for line, _ in wrapped[:visible]]
    last_consumed = wrapped[min(visible, len(wrapped)) - 1][1]
    next_start = start_char + last_consumed
    eof = next_start >= total
    return Page(
        lines=page_lines,
        first_char_offset=start_char,
        next_page_start=next_start,
        chapter_index=ci,
        eof=eof,
        total_lines=total,
    )