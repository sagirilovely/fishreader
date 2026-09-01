"""Parser factory."""

from __future__ import annotations

from .base import BaseParser, ParseError
from .txt_parser import TxtParser

_PARSERS: dict[str, BaseParser] = {
    "txt": TxtParser(),
}


def get_parser(extension_or_fmt: str) -> BaseParser | None:
    """Return a parser for the extension; None when unsupported."""
    fmt = extension_or_fmt.lower().lstrip(".")
    return _PARSERS.get(fmt)


__all__ = ["BaseParser", "ParseError", "get_parser"]