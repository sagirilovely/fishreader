"""Shared text utilities: charset detection, normalization, chapter
splitting and HTML cleaning."""

from __future__ import annotations

import re

from .base import ParseError

# Decoding fallback order when charset detection is inconclusive.
CHARSET_CANDIDATES = ("utf-8", "gb18030", "gbk", "big5")

# Chinese chapter headings, e.g. 第一章 / 第3章 / 第一百二十章 / 卷一
_CN_TITLE = r"第[0-9零一二两三四五六七八九十百千万壹贰叁肆伍陆柒捌玖拾]+[章节卷回集篇][^\n]{0,50}$"
# English headings, e.g. Chapter 1 / CHAPTER IV
_EN_TITLE = r"Chapter\s+(?:\d+[^\n]{0,80}|[IVXLC]+\b)"

_TITLE_RE = re.compile(
    rf"^(?:{_CN_TITLE}|{_EN_TITLE})",
    re.MULTILINE | re.IGNORECASE,
)


def decode_text(raw: bytes) -> str:
    """Decode raw bytes to text.

    Uses charset-normalizer first; falls back to a fixed candidate order.
    Raises ParseError with a readable message when nothing works.
    """
    try:
        import charset_normalizer

        best = charset_normalizer.from_bytes(raw).best()
        if best is not None and best.encoding:
            try:
                return raw.decode(best.encoding)
            except (LookupError, UnicodeDecodeError):
                pass
    except ImportError:
        pass

    errors: list[str] = []
    for enc in CHARSET_CANDIDATES:
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError) as exc:
            errors.append(f"{enc}: {exc}")
    raise ParseError(
        "cannot decode text (tried charset detection and "
        f"{', '.join(CHARSET_CANDIDATES)}): {errors[0] if errors else 'unknown'}"
    )


def normalize_body(text: str) -> str:
    """Normalize raw decoded text into paragraph layout.

    - unify line endings (CRLF/CR -> LF)
    - collapse 3+ consecutive newlines into 2 (paragraph break)
    - strip each line, drop empty lines, keep intra-paragraph line breaks
    - join paragraphs with blank lines
    """
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    paragraphs: list[str] = []
    for para in t.split("\n\n"):
        lines = [ln.strip() for ln in para.split("\n") if ln.strip()]
        if lines:
            paragraphs.append("\n".join(lines))
    return "\n\n".join(paragraphs)


def split_chapters(text: str) -> list[tuple[str, str]]:
    """Split normalized text into (title, body) chapters.

    Lines matching the chapter-title patterns start a new chapter; leading
    content without a title becomes a '前言' (prologue) chapter; text with no
    chapter markers at all is returned as a single chapter.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chapters: list[tuple[str, str]] = []
    prelude: list[str] = []
    cur_title: str | None = None
    cur_body: list[str] = []

    for para in paragraphs:
        if _TITLE_RE.match(para):
            if cur_title is not None:
                chapters.append((cur_title, "\n\n".join(cur_body)))
            elif prelude:
                chapters.append(("前言", "\n\n".join(prelude)))
                prelude = []
            cur_title = para
            cur_body = []
        elif cur_title is None:
            prelude.append(para)
        else:
            cur_body.append(para)

    if cur_title is not None:
        chapters.append((cur_title, "\n\n".join(cur_body)))
    elif prelude:
        chapters.append(("前言", "\n\n".join(prelude)))

    if not chapters:
        chapters = [("前言", text.strip())]
    return chapters


_STRIP_TAGS = ("script", "style", "nav", "header", "footer", "noscript", "head")
_BLOCK_TAGS = (
    "p", "div", "section", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "pre", "tr", "table",
)


def html_to_text(html: str) -> str:
    """Clean XHTML/HTML into normalized paragraph text.

    Removes script/style/nav/footer/header, converts <br> and block elements
    into line/paragraph breaks, then collapses whitespace.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(_BLOCK_TAGS):
        tag.append(soup.new_string("\n"))

    text = soup.get_text("")
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n\n".join(lines)