"""Novel reading pane: renders the current page in disguised styles."""

from __future__ import annotations

from textual.widgets import Static

from fishreader.textlayout import Page, blank_rows_after

# Extra width allowance subtracted from the pane for font_size density
# (on top of PANE_PADDING_WIDTH and STYLE_PREFIX_WIDTH).
FONT_WIDTH_BASIS = {"small": 0, "medium": 0, "large": 2}

# #reader-pane has `padding: 0 1`, so two columns are never usable for text.
PANE_PADDING_WIDTH = 2
# Every content line is prefixed with "- " / "# " (in every novel_style).
# Text must be wrapped that much narrower, otherwise the widget re-wraps the
# decorated line and the page grows taller than the pane — silently clipping
# the tail of every page and breaking page-to-page continuity.
STYLE_PREFIX_WIDTH = 2
# docstring style wraps the page in triple quotes: one row above, one below.
STYLE_CHROME_ROWS = {"markdown": 0, "comment": 0, "docstring": 2}


def chrome_rows(novel_style: str) -> int:
    """Screen rows the style itself consumes, on top of the text rows."""
    return STYLE_CHROME_ROWS.get(novel_style, 0)


def decorate_lines(
    lines: list[str],
    novel_style: str,
    line_spacing: float = 0,
    paragraph_spacing: float = 0,
) -> list[str]:
    """Apply the disguise style and spacing to a page's raw lines.

    - markdown:   every line prefixed with "- " (work-note style)
    - comment:    every line prefixed with "# "
    - docstring:  wrapped by triple-quote markers on the first and last line

    Spacing is measured in rows and may be fractional: `line_spacing=0.25`
    inserts one blank row every four content lines instead of a blank row
    after every line, which is the only way to tune density in a terminal
    (whose rows cannot be split). `paragraph_spacing` works the same way on
    paragraph breaks.
    """
    content_gaps = blank_rows_after(sum(1 for raw in lines if raw != ""), line_spacing)

    breaks: list[bool] = []
    prev_nonempty = False
    for raw in lines:
        breaks.append(raw == "" and prev_nonempty and paragraph_spacing > 0)
        prev_nonempty = raw != ""
    break_gaps = blank_rows_after(sum(breaks), paragraph_spacing)

    styled: list[str] = []
    content_i = 0
    break_i = 0
    prev_nonempty = False
    for raw, is_break in zip(lines, breaks):
        if raw == "":
            styled.append("")
            if is_break:
                styled.extend([""] * break_gaps[break_i])
                break_i += 1
            prev_nonempty = False
            continue
        prev_nonempty = True
        if novel_style == "comment":
            styled.append(f"# {raw}")
        else:
            styled.append(f"- {raw}")
        styled.extend([""] * content_gaps[content_i])
        content_i += 1
    if novel_style == "docstring":
        styled = ['"""'] + styled + ['"""']
    return styled


class ReaderPane(Static):
    """Static pane showing the current page of the open book."""

    def set_page(
        self,
        page: Page,
        novel_style: str = "markdown",
        line_spacing: float = 0,
        paragraph_spacing: float = 0,
    ) -> None:
        lines = decorate_lines(page.lines, novel_style, line_spacing, paragraph_spacing)
        if page.eof:
            lines.append("-- EOF --")
        self.update("\n".join(lines) if lines else "")

    def show_empty(self, message: str = "no book loaded") -> None:
        self.update(message)