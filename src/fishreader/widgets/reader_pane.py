"""Novel reading pane: renders the current page in disguised styles."""

from __future__ import annotations

from textual.widgets import Static

from fishreader.textlayout import Page

# Base width allowance subtracted from the pane for font_size density.
FONT_WIDTH_BASIS = {"small": 2, "medium": 2, "large": 6}


def decorate_lines(
    lines: list[str],
    novel_style: str,
    line_spacing: int = 0,
    paragraph_spacing: int = 0,
) -> list[str]:
    """Apply the disguise style and spacing to a page's raw lines.

    - markdown:   every line prefixed with "- " (work-note style)
    - comment:    every line prefixed with "# "
    - docstring:  wrapped by quote markers on the first and last line
    Spacing: `line_spacing` blank lines after every content line;
    `paragraph_spacing` extra blank lines after paragraph breaks.
    """
    styled: list[str] = []
    prev_nonempty = False
    for raw in lines:
        if raw == "":
            styled.append("")
            if prev_nonempty and paragraph_spacing > 0:
                styled.extend([""] * paragraph_spacing)
            prev_nonempty = False
            continue
        prev_nonempty = True
        if novel_style == "comment":
            styled.append(f"# {raw}")
        else:
            styled.append(f"- {raw}")
        if line_spacing > 0:
            styled.extend([""] * line_spacing)
    return styled


class ReaderPane(Static):
    """Static pane showing the current page of the open book."""

    def set_page(
        self,
        page: Page,
        novel_style: str = "markdown",
        line_spacing: int = 0,
        paragraph_spacing: int = 0,
    ) -> None:
        lines = decorate_lines(page.lines, novel_style, line_spacing, paragraph_spacing)
        if page.eof:
            lines.append("-- EOF --")
        self.update("\n".join(lines) if lines else "")

    def show_empty(self, message: str = "no book loaded") -> None:
        self.update(message)