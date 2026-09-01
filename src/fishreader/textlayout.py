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

    Returns a list of (line_text, start_offset) where start_offset is the
    position of the line's first character within the paragraph.
    """
    if not para:
        return [("", 0)]
    out: list[tuple[str, int]] = []
    line = ""
    w = 0
    pos = 0
    line_start = 0
    n = len(para)
    while pos < n:
        ch = para[pos]
        if _is_word_char(ch):
            end = pos
            while end < n and _is_word_char(para[end]):
                end += 1
            word = para[pos:end]
            if line and w + len(word) > width:
                out.append((line.rstrip(), line_start))
                line_start = pos
                line, w = "", 0
            if len(word) > width:
                if line:
                    out.append((line.rstrip(), line_start))
                    line, w = "", 0
                k = 0
                while k < len(word):
                    out.append((word[k : k + width], pos + k))
                    k += width
                pos = end
                line_start = pos
                continue
            line += word
            w += len(word)
            pos = end
            continue

        cw = char_width(ch)
        if w + cw > width:
            # Flush the full line, then hang closing punctuation on to it so
            # it never starts the next line (行首禁则).
            out.append((line.rstrip(), line_start))
            if ch in START_FORBIDDEN and out[-1][0]:
                out[-1] = (out[-1][0] + ch, out[-1][1])
                line, w = "", 0
                line_start = pos + 1
                pos += 1
                continue
            line, w = "", 0
            if ch == " ":
                line_start = pos + 1
                pos += 1
                continue
            line_start = pos
        if ch != " " or line:  # drop leading spaces, keep interior ones
            line += ch
            w += cw
        pos += 1
    if line:
        out.append((line.rstrip(), line_start))
    return out


def wrap_text_with_offsets(text: str, width: int) -> list[tuple[str, int]]:
    """Wrap text to `width` columns.

    Explicit newlines are preserved: a blank line stays a blank line
    (paragraph boundary). Returns (line, char_offset) pairs where
    char_offset is the offset of the line's first character in `text`.
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
        for line, start_in_para in _wrap_para(para, width):
            result.append((line, pos + start_in_para))
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


def spacing_rows(item_count: int, spacing: float) -> int:
    """Total blank rows added between `item_count` items at `spacing`.

    Spacing is fractional (e.g. 0.25 rows per line). Terminals can only draw
    whole rows, so the fraction is spread over the page: the blank rows are
    distributed as evenly as possible, which makes the *total* exactly
    floor(item_count * spacing) — the average gap is still `spacing`.
    """
    if spacing <= 0 or item_count <= 0:
        return 0
    return int(item_count * spacing + 1e-9)


def blank_rows_after(count: int, spacing: float) -> list[int]:
    """Blank rows to insert after each of `count` items.

    `blank_rows_after(4, 0.25) == [0, 0, 0, 1]`: one blank row every four
    lines. Summing the list yields spacing_rows(count, spacing).
    """
    if spacing <= 0 or count <= 0:
        return [0] * count
    out: list[int] = []
    previous = 0
    for i in range(1, count + 1):
        total = int(i * spacing + 1e-9)
        out.append(total - previous)
        previous = total
    return out


def fit_lines(box_height: int, spacing: float) -> int:
    """How many content lines fit in `box_height` terminal rows.

    Exact (not an approximation): finds the largest n with
    n + spacing_rows(n, spacing) <= box_height.
    """
    if box_height < 1:
        return 1
    if spacing <= 0:
        return box_height
    n = int(box_height / (1 + spacing))
    n = max(1, min(n, box_height))
    while n > 1 and n + spacing_rows(n, spacing) > box_height:
        n -= 1
    while n + 1 + spacing_rows(n + 1, spacing) <= box_height:
        n += 1
    return max(1, n)


def fit_page_rows(
    lines: list[str],
    start: int,
    height: int,
    line_spacing: float = 0,
    paragraph_spacing: float = 0,
    chrome_rows: int = 0,
) -> int:
    """How many source lines starting at `start` fit in `height` screen rows.

    Counts every row the renderer will actually emit: one per source line,
    plus the blank rows spread by line/paragraph spacing, plus the style
    chrome. Paging has to measure the page in *rows* — a line count that
    only knows about line_spacing lets paragraph spacing (and the docstring
    markers) push the page past the bottom of the pane, where
    `overflow-y: hidden` silently eats the tail. The tail is then never
    shown, because the next page starts after it: that is exactly what makes
    page N+1 look disconnected from page N.
    """
    total = len(lines)
    if total == 0:
        return 0
    start = max(0, min(start, total - 1))
    budget = height - chrome_rows
    if budget < 1:
        return 1
    content = 0
    breaks = 0
    prev_nonempty = False
    i = start
    while i < total:
        raw = lines[i]
        # mirrors decorate_lines(): a break is a blank line *after* content
        is_break = raw == "" and prev_nonempty and paragraph_spacing > 0
        next_content = content if raw == "" else content + 1
        next_breaks = breaks + 1 if is_break else breaks
        rows = (
            (i - start + 1)
            + spacing_rows(next_content, line_spacing)
            + spacing_rows(next_breaks, paragraph_spacing)
        )
        if rows > budget and i > start:
            break  # the page is full; at least the first line always fits
        content = next_content
        breaks = next_breaks
        prev_nonempty = raw != ""
        i += 1
    return max(1, min(i - start, total - start))


def _page_end(lines, start, height, line_spacing, paragraph_spacing, chrome_rows) -> int:
    """First source line *after* the page starting at `start`."""
    return start + fit_page_rows(
        lines, start, height, line_spacing, paragraph_spacing, chrome_rows
    )


def fit_page_start_before(
    lines: list[str],
    limit: int,
    height: int,
    line_spacing: float = 0,
    paragraph_spacing: float = 0,
    chrome_rows: int = 0,
) -> int:
    """Start of the page that ends at (or just before) `limit`.

    Inverse of forward paging: `fit_page_rows` from the returned index lands
    back on `limit`, so ←/→ walk the exact same page boundaries.
    """
    total = len(lines)
    if total == 0 or limit <= 0:
        return 0
    limit = min(limit, total)
    lo, hi = 0, limit - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _page_end(lines, mid, height, line_spacing, paragraph_spacing, chrome_rows) <= limit:
            lo = mid
        else:
            hi = mid - 1
    return lo


def fit_page_start_last(
    lines: list[str],
    height: int,
    line_spacing: float = 0,
    paragraph_spacing: float = 0,
    chrome_rows: int = 0,
) -> int:
    """Start of the last page of `lines` (used when paging into a prev chapter)."""
    total = len(lines)
    if total == 0:
        return 0
    if _page_end(lines, 0, height, line_spacing, paragraph_spacing, chrome_rows) >= total:
        return 0
    lo, hi = 0, total - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if _page_end(lines, mid, height, line_spacing, paragraph_spacing, chrome_rows) >= total:
            hi = mid
        else:
            lo = mid + 1
    return lo


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
    line_spacing: float = 0,
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

    visible = fit_lines(box_height, line_spacing)

    # Only wrap what a single page can hold: each wrapped line consumes at
    # most width+1 source characters, so this cap always yields >= visible
    # lines when the remaining text is long enough — keeping page flips O(page)
    # instead of O(whole book).
    cap = visible * (box_width + 1) + box_width
    chunk = text[start_char : start_char + cap]
    wrapped = wrap_text_with_offsets(chunk, box_width)
    if not wrapped:
        return Page([], start_char, start_char, ci, eof=start_char >= total)

    page_lines = [line for line, _ in wrapped[:visible]]
    if len(wrapped) > visible:
        # There is a next line: the next page starts at its first character.
        next_start = start_char + wrapped[visible][1]
        eof = False
    else:
        # The page consumed the whole remaining chunk (which is the tail of
        # the book thanks to the cap above); nothing follows.
        next_start = min(start_char + cap, total)
        eof = next_start >= total
    return Page(
        lines=page_lines,
        first_char_offset=start_char,
        next_page_start=next_start,
        chapter_index=ci,
        eof=eof,
        total_lines=total,
    )