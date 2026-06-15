from __future__ import annotations

import copy
import re
from html.parser import HTMLParser
from pathlib import PurePosixPath
from typing import Any

_UNDERLINE_CLASSES = frozenset({"underline"})
_UNWRAP_SPAN_CLASSES = frozenset({"custom-style"}) | _UNDERLINE_CLASSES


def normalize_ast_for_gfm(ast: dict[str, Any]) -> dict[str, Any]:
    """Przygotowuje AST Pandoc do zapisu GFM (obrazy, underline→bold, rozwinięcie Span/Div)."""
    out = copy.deepcopy(ast)
    out["blocks"] = _normalize_blocks(out.get("blocks") or [])
    return out


def normalize_markdown_html(md: str) -> str:
    """Safety net: zamiana pozostałego HTML (img, proste tabele) na składnię Markdown."""
    md = _replace_figure_blocks(md)
    md = _replace_img_tags(md)
    return _replace_simple_html_tables(md)


def _normalize_blocks(blocks: list[Any]) -> list[Any]:
    result: list[Any] = []
    for block in blocks:
        result.extend(_normalize_block(block))
    return result


def _normalize_block(block: Any) -> list[Any]:
    if not isinstance(block, dict):
        return [block]
    t = block.get("t")
    if t == "Figure":
        return _figure_to_paras(block)
    if t == "Para":
        inlines = _normalize_inlines(block.get("c") or [])
        return [{"t": "Para", "c": inlines}] if inlines else []
    if t == "Plain":
        inlines = _normalize_inlines(block.get("c") or [])
        return [{"t": "Plain", "c": inlines}] if inlines else []
    if t == "Header":
        c = block.get("c")
        if isinstance(c, list) and len(c) >= 3 and isinstance(c[2], list):
            new_block = copy.deepcopy(block)
            new_block["c"] = [c[0], c[1], _normalize_inlines(c[2])]
            return [new_block]
        return [block]
    if t == "BlockQuote":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list):
            new_block["c"] = _normalize_blocks(c)
        return [new_block]
    if t == "BulletList":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list):
            new_block["c"] = [_normalize_blocks(item) for item in c if isinstance(item, list)]
        return [new_block]
    if t == "OrderedList":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list) and len(c) >= 2 and isinstance(c[1], list):
            new_block["c"] = [c[0], [_normalize_blocks(item) for item in c[1] if isinstance(item, list)]]
        return [new_block]
    if t == "Table":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list) and len(c) >= 5 and isinstance(c[4], list):
            body = c[4]
            new_body = []
            for row in body:
                if isinstance(row, list):
                    new_body.append(
                        [_normalize_blocks(cell) if isinstance(cell, list) else cell for cell in row]
                    )
                else:
                    new_body.append(row)
            new_c = list(c)
            new_c[4] = new_body
            new_block["c"] = new_c
        elif isinstance(c, list) and len(c) >= 4 and isinstance(c[3], list):
            body = c[3]
            new_body = []
            for row in body:
                if isinstance(row, list):
                    new_body.append(
                        [_normalize_blocks(cell) if isinstance(cell, list) else cell for cell in row]
                    )
                else:
                    new_body.append(row)
            new_c = list(c)
            new_c[3] = new_body
            new_block["c"] = new_c
        return [new_block]
    if t == "Div":
        c = block.get("c")
        if isinstance(c, list) and len(c) >= 2 and isinstance(c[1], list):
            return _normalize_blocks(c[1])
        return []
    return [block]


def _figure_to_paras(block: dict[str, Any]) -> list[Any]:
    c = block.get("c")
    if not isinstance(c, list) or len(c) < 3:
        return []
    caption_blocks = c[1][1] if isinstance(c[1], list) and len(c[1]) > 1 else []
    alt = _blocks_to_plain_text(caption_blocks)
    content = c[2] if isinstance(c[2], list) else []
    images: list[Any] = []
    for sub in content:
        if isinstance(sub, dict) and sub.get("t") == "Plain":
            for il in sub.get("c") or []:
                if isinstance(il, dict) and il.get("t") == "Image":
                    images.append(_clean_image(il, alt))
    if not images:
        return []
    return [{"t": "Para", "c": images}]


def _blocks_to_plain_text(blocks: list[Any]) -> str:
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, dict) and block.get("t") == "Para":
            for il in block.get("c") or []:
                if isinstance(il, dict) and il.get("t") == "Str":
                    parts.append(str(il.get("c", "")))
                elif isinstance(il, dict) and il.get("t") == "Space":
                    parts.append(" ")
    return "".join(parts).strip()


def _clean_image(image: dict[str, Any], alt_override: str = "") -> dict[str, Any]:
    _attr, caption, target = image.get("c") or [[], [], ["", ""]]
    url, title = target if isinstance(target, list) and len(target) >= 2 else ["", ""]
    url = _normalize_media_url(str(url))
    alt_inlines = caption if isinstance(caption, list) else []
    alt = alt_override or _inlines_to_text(alt_inlines)
    return {"t": "Image", "c": [["", [], []], [], [url, alt or str(title or "")]]}


def _normalize_media_url(url: str) -> str:
    normalized = url.replace("\\", "/")
    if "media/" in normalized:
        basename = normalized.split("media/")[-1].split("/")[-1]
        return f"media/{basename}"
    name = PurePosixPath(normalized).name
    return f"media/{name}" if name else normalized


def _normalize_inlines(inlines: list[Any]) -> list[Any]:
    out: list[Any] = []
    for inline in inlines:
        out.extend(_normalize_inline(inline))
    return out


def _normalize_inline(inline: Any) -> list[Any]:
    if not isinstance(inline, dict):
        return [inline]
    t = inline.get("t")
    if t == "Image":
        return [_clean_image(inline)]
    if t == "Underline":
        inner = _normalize_inlines(inline.get("c") or [])
        return [{"t": "Strong", "c": inner}] if inner else []
    if t == "Span":
        attrs, content = inline.get("c") or [[], []]
        classes = set(attrs[1] if isinstance(attrs, list) and len(attrs) > 1 else [])
        children = content if isinstance(content, list) else []
        inner = _normalize_inlines(children)
        if classes & _UNDERLINE_CLASSES:
            return [{"t": "Strong", "c": inner}] if inner else []
        if classes & _UNWRAP_SPAN_CLASSES or not classes:
            return inner
        if not inner:
            return []
        return [{"t": "Span", "c": [attrs, inner]}]
    if t in ("Strong", "Emph", "Strikeout", "SmallCaps"):
        c = inline.get("c")
        if isinstance(c, list):
            return [{**inline, "c": _normalize_inlines(c)}]
    if t == "Link":
        c = inline.get("c")
        if isinstance(c, list) and len(c) >= 3:
            return [{**inline, "c": [c[0], _normalize_inlines(c[1]), c[2]]}]
    if t == "Quoted":
        c = inline.get("c")
        if isinstance(c, list) and len(c) >= 2:
            return [{**inline, "c": [c[0], _normalize_inlines(c[1])]}]
    if t == "Note":
        c = inline.get("c")
        if isinstance(c, list):
            return [{**inline, "c": [_normalize_blocks(c[0])]}]
    return [inline]


def _inlines_to_text(inlines: list[Any]) -> str:
    parts: list[str] = []
    for inline in inlines:
        if not isinstance(inline, dict):
            continue
        it = inline.get("t")
        if it == "Str":
            parts.append(str(inline.get("c", "")))
        elif it == "Space":
            parts.append(" ")
    return "".join(parts)


def _replace_figure_blocks(md: str) -> str:
    pattern = re.compile(
        r"<figure>\s*<img[^>]+src=\"([^\"]+)\"[^>]*/>\s*(?:<figcaption[^>]*>.*?</figcaption>\s*)?</figure>",
        re.DOTALL | re.IGNORECASE,
    )

    def repl(match: re.Match[str]) -> str:
        url = _normalize_media_url(match.group(1))
        return f"![]({url})"

    return pattern.sub(repl, md)


def _replace_img_tags(md: str) -> str:
    pattern = re.compile(r"<img[^>]+src=\"([^\"]+)\"[^>]*/?>", re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        url = _normalize_media_url(match.group(1))
        alt_match = re.search(r'alt="([^"]*)"', match.group(0), re.IGNORECASE)
        alt = alt_match.group(1) if alt_match else ""
        return f"![{alt}]({url})"

    return pattern.sub(repl, md)


def _replace_simple_html_tables(md: str) -> str:
    pattern = re.compile(r"<table\b[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        html = match.group(0)
        if re.search(r"\b(colspan|rowspan)\s*=", html, re.IGNORECASE):
            return html
        rows = _HtmlTableParser.parse(html)
        if not rows:
            return html
        if len(rows) == 1:
            return _single_row_table_to_stacked(rows[0])
        return _rows_to_pipe_table(rows)

    return pattern.sub(repl, md)


def _single_row_table_to_stacked(cells: list[str]) -> str:
    parts = [_html_cell_to_markdown(cell) for cell in cells]
    parts = [p for p in parts if p]
    return "\n\n".join(parts) + "\n" if parts else ""


def _html_cell_to_markdown(cell_html: str) -> str:
    cell = cell_html.strip()
    if not cell:
        return ""

    img_md = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", cell)
    if img_md:
        alt, url = img_md.group(1), img_md.group(2)
        return f"![{alt}]({_normalize_media_url(url)})"

    img_tag = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", cell, re.IGNORECASE)
    if img_tag:
        alt_match = re.search(r"""alt=["']([^"']*)["']""", cell, re.IGNORECASE)
        alt = alt_match.group(1) if alt_match else ""
        url = _normalize_media_url(img_tag.group(1))
        return f"![{alt}]({url})"

    blockquote = _blockquote_html_to_markdown(cell)
    if blockquote:
        return blockquote

    return _html_paragraphs_to_markdown(cell)


def _blockquote_html_to_markdown(cell_html: str) -> str | None:
    match = re.search(r"<blockquote\b[^>]*>(.*)</blockquote>", cell_html, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    inner = match.group(1)
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", inner, re.DOTALL | re.IGNORECASE)
    if not paragraphs:
        text = _inline_html_to_markdown(re.sub(r"<[^>]+>", "", inner).strip())
        return f"> {text}" if text else None
    lines: list[str] = []
    for i, para in enumerate(paragraphs):
        text = _inline_html_to_markdown(para.strip())
        if not text:
            continue
        if i > 0:
            lines.append(">")
        for line in text.splitlines():
            lines.append(f"> {line}")
    return "\n".join(lines) if lines else None


def _html_paragraphs_to_markdown(cell_html: str) -> str:
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", cell_html, re.DOTALL | re.IGNORECASE)
    if paragraphs:
        parts = [_inline_html_to_markdown(p.strip()) for p in paragraphs]
        return "\n\n".join(p for p in parts if p)
    text = re.sub(r"<br\s*/?>", "\n", cell_html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _inline_html_to_markdown(html: str) -> str:
    text = html
    text = re.sub(r"<strong\b[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<b\b[^>]*>(.*?)</b>", r"**\1**", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<em\b[^>]*>(.*?)</em>", r"*\1*", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<i\b[^>]*>(.*?)</i>", r"*\1*", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def _html_cell_to_plain_text(cell_html: str) -> str:
    return _inline_html_to_markdown(_html_paragraphs_to_markdown(cell_html) or cell_html)


def _rows_to_pipe_table(rows: list[list[str]]) -> str:
    plain_rows = [[_html_cell_to_plain_text(cell) for cell in row] for row in rows]
    header = plain_rows[0]
    body = plain_rows[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines) + "\n"


class _HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._cell_parts: list[str] = []
        self._in_cell = False

    @classmethod
    def parse(cls, html: str) -> list[list[str]]:
        parser = cls()
        parser.feed(html)
        parser.close()
        return parser.rows

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("td", "th") and not self._in_cell:
            self._in_cell = True
            self._cell_parts = []
            return
        if self._in_cell:
            attr_str = "".join(
                f' {name}="{value}"' if value is not None else f" {name}"
                for name, value in attrs
            )
            self._cell_parts.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            cell_html = "".join(self._cell_parts).strip()
            if self._current_row is None:
                self._current_row = []
            self._current_row.append(cell_html)
            self._in_cell = False
            return
        if self._in_cell:
            self._cell_parts.append(f"</{tag}>")
            return
        if tag == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)
