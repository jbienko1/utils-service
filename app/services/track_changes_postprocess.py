from __future__ import annotations

import copy
import re
from datetime import datetime
from typing import Any

_INSERTION_CLASSES = frozenset({"insertion", "paragraph-insertion"})
_DELETION_CLASSES = frozenset({"deletion", "paragraph-deletion"})


def transform_track_changes_ast(ast: dict[str, Any]) -> dict[str, Any]:
    """Normalizuje track-changes=all z Pandoc: wstawienia bez otoczki, usunięcia jako Strikeout, komentarze jako CodeBlock."""
    out = copy.deepcopy(ast)
    out["blocks"] = _transform_blocks(out.get("blocks") or [])
    return out


def _transform_blocks(blocks: list[Any]) -> list[Any]:
    result: list[Any] = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if isinstance(block, dict) and block.get("t") == "Para":
            start = _find_comment_start_in_block(block)
            if start is not None and not _block_contains_comment_end(block, start["comment_id"]):
                chunk, i = _collect_comment_span(blocks, i, start)
                result.extend(chunk)
                continue
        if isinstance(block, dict):
            result.extend(_transform_single_block(block))
        else:
            result.append(block)
        i += 1
    return result


def _transform_single_block(block: dict[str, Any]) -> list[Any]:
    t = block.get("t")
    if t == "Para":
        return _transform_para(block)
    if t in ("Header", "Plain"):
        c = block.get("c")
        if isinstance(c, list) and len(c) >= 2 and isinstance(c[-1], list):
            new_block = copy.deepcopy(block)
            new_block["c"] = list(c)
            new_block["c"][-1] = _process_inlines(new_block["c"][-1])
            return [new_block]
        return [block]
    if t == "BlockQuote":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list):
            new_block["c"] = _transform_blocks(c)
        return [new_block]
    if t == "BulletList":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list):
            new_block["c"] = [_transform_blocks(item) for item in c if isinstance(item, list)]
        return [new_block]
    if t == "OrderedList":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list) and len(c) >= 2 and isinstance(c[1], list):
            new_block["c"] = list(c)
            new_block["c"][1] = [_transform_blocks(item) for item in c[1] if isinstance(item, list)]
        return [new_block]
    if t == "Table":
        new_block = copy.deepcopy(block)
        c = new_block.get("c")
        if isinstance(c, list) and len(c) >= 4 and isinstance(c[3], list):
            new_c = list(c)
            new_c[3] = [
                [_transform_blocks(cell) if isinstance(cell, list) else cell for cell in row]
                if isinstance(row, list)
                else row
                for row in c[3]
            ]
            new_block["c"] = new_c
        return [new_block]
    return [block]


def _transform_para(para: dict[str, Any]) -> list[Any]:
    inlines = para.get("c")
    if not isinstance(inlines, list):
        return [para]
    segments = _split_inlines_on_comments(inlines)
    out: list[Any] = []
    for prefix, highlighted, comment in segments:
        combined = _process_inlines(prefix + (highlighted or []))
        if combined:
            out.append({"t": "Para", "c": combined})
        if comment is not None:
            out.append(_comment_code_block(comment))
    return out or [{"t": "Para", "c": []}]


def _split_inlines_on_comments(
    inlines: list[Any],
) -> list[tuple[list[Any], list[Any] | None, dict[str, Any] | None]]:
    segments: list[tuple[list[Any], list[Any] | None, dict[str, Any] | None]] = []
    current: list[Any] = []
    i = 0
    while i < len(inlines):
        inline = inlines[i]
        start = _parse_comment_start(inline)
        if start is not None:
            highlighted: list[Any] = []
            i += 1
            while i < len(inlines):
                end_id = _parse_comment_end(inlines[i])
                if end_id is not None and end_id == start["comment_id"]:
                    i += 1
                    break
                highlighted.append(inlines[i])
                i += 1
            segments.append((current, highlighted, start))
            current = []
            continue
        current.append(inline)
        i += 1
    segments.append((current, None, None))
    return segments


def _collect_comment_span(
    blocks: list[Any],
    start_index: int,
    start_info: dict[str, Any],
) -> tuple[list[Any], int]:
    """Obsługa komentarzy rozciągających się na wiele akapitów."""
    comment_id = start_info["comment_id"]
    prefix_inlines: list[Any] = []
    highlighted_inlines: list[Any] = []
    suffix_blocks: list[Any] = []
    found_start = False
    end_block_index = start_index
    i = start_index
    while i < len(blocks):
        block = blocks[i]
        if not isinstance(block, dict) or block.get("t") != "Para":
            if found_start:
                highlighted_inlines.append({"t": "SoftBreak"})
            suffix_blocks.append(block)
            i += 1
            continue
        inlines = block.get("c") or []
        j = 0
        while j < len(inlines):
            inline = inlines[j]
            if not found_start:
                cs = _parse_comment_start(inline)
                if cs is not None and cs["comment_id"] == comment_id:
                    start_info = cs
                    found_start = True
                    j += 1
                    continue
                prefix_inlines.append(inline)
                j += 1
                continue
            end_id = _parse_comment_end(inline)
            if end_id is not None and end_id == comment_id:
                rest = inlines[j + 1 :]
                if rest:
                    suffix_blocks.insert(0, {"t": "Para", "c": rest})
                out: list[Any] = []
                body = _process_inlines(prefix_inlines) + _process_inlines(highlighted_inlines)
                if body:
                    out.append({"t": "Para", "c": body})
                out.append(_comment_code_block(start_info))
                out.extend(_transform_blocks(suffix_blocks))
                return out, end_block_index + 1
            highlighted_inlines.append(inline)
            j += 1
        if found_start:
            highlighted_inlines.append({"t": "SoftBreak"})
        end_block_index = i
        i += 1
    return _transform_single_block(blocks[start_index]), start_index + 1


def _find_comment_start_in_block(block: Any) -> dict[str, Any] | None:
    if not isinstance(block, dict) or block.get("t") != "Para":
        return None
    for inline in block.get("c") or []:
        cs = _parse_comment_start(inline)
        if cs is not None:
            return cs
    return None


def _block_contains_comment_end(block: Any, comment_id: str) -> bool:
    if not isinstance(block, dict) or block.get("t") != "Para":
        return False
    for inline in block.get("c") or []:
        end_id = _parse_comment_end(inline)
        if end_id == comment_id:
            return True
    return False


def _parse_comment_start(inline: Any) -> dict[str, Any] | None:
    if not isinstance(inline, dict) or inline.get("t") != "Span":
        return None
    attrs, content = inline.get("c") or [[], []]
    classes = attrs[1] if isinstance(attrs, list) and len(attrs) > 1 else []
    if "comment-start" not in classes:
        return None
    keyvals = attrs[2] if isinstance(attrs, list) and len(attrs) > 2 else []
    meta = {k: v for k, v in keyvals if isinstance(k, str)}
    return {
        "comment_id": meta.get("id", ""),
        "author": meta.get("author", ""),
        "date": meta.get("date", ""),
        "body_inlines": content if isinstance(content, list) else [],
    }


def _parse_comment_end(inline: Any) -> str | None:
    if not isinstance(inline, dict) or inline.get("t") != "Span":
        return None
    attrs = inline.get("c") or [[], []]
    classes = attrs[1] if isinstance(attrs, list) and len(attrs) > 1 else []
    if "comment-end" not in classes:
        return None
    keyvals = attrs[2] if isinstance(attrs, list) and len(attrs) > 2 else []
    meta = {k: v for k, v in keyvals if isinstance(k, str)}
    return meta.get("id", "")


def _process_inlines(inlines: list[Any]) -> list[Any]:
    out: list[Any] = []
    for inline in inlines:
        out.extend(_process_inline(inline))
    return out


def _process_inline(inline: Any) -> list[Any]:
    if not isinstance(inline, dict):
        return [inline]
    t = inline.get("t")
    if t == "Span":
        attrs, content = inline.get("c") or [[], []]
        classes = set(attrs[1] if isinstance(attrs, list) and len(attrs) > 1 else [])
        children = content if isinstance(content, list) else []
        if classes & _INSERTION_CLASSES:
            return _process_inlines(children)
        if classes & _DELETION_CLASSES:
            inner = _process_inlines(children)
            return [{"t": "Strikeout", "c": inner}] if inner else []
        if "comment-start" in classes or "comment-end" in classes:
            return []
        inner = _process_inlines(children)
        if not inner:
            return []
        return [{"t": "Span", "c": [attrs, inner]}]
    if t == "Strikeout":
        c = inline.get("c")
        if isinstance(c, list):
            return [{"t": "Strikeout", "c": _process_inlines(c)}]
    if t in ("Strong", "Emph", "Underline", "SmallCaps"):
        c = inline.get("c")
        if isinstance(c, list):
            return [{**inline, "c": _process_inlines(c)}]
    if t == "Quoted":
        c = inline.get("c")
        if isinstance(c, list) and len(c) >= 2:
            return [{**inline, "c": [c[0], _process_inlines(c[1])]}]
    return [inline]


def _comment_code_block(comment: dict[str, Any]) -> dict[str, Any]:
    author = comment.get("author") or "Nieznany"
    date_str = _format_comment_date(comment.get("date") or "")
    body = _inlines_to_text(comment.get("body_inlines") or []).strip()
    text = f"*{author} ({date_str}):*\n{body}" if body else f"*{author} ({date_str}):*"
    return {"t": "CodeBlock", "c": [["", [], []], text]}


def _format_comment_date(raw: str) -> str:
    if not raw:
        return "?"
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
        return m.group(1) if m else raw


def _inlines_to_text(inlines: list[Any]) -> str:
    parts: list[str] = []
    for inline in inlines:
        if not isinstance(inline, dict):
            continue
        t = inline.get("t")
        if t == "Str":
            parts.append(str(inline.get("c", "")))
        elif t == "Space":
            parts.append(" ")
        elif t in ("SoftBreak", "LineBreak"):
            parts.append("\n")
        elif t in ("Strong", "Emph", "Strikeout", "Underline", "Span"):
            c = inline.get("c")
            if isinstance(c, list):
                if t == "Span" and len(c) > 1:
                    parts.append(_inlines_to_text(c[1]))
                elif t in ("Strong", "Emph", "Strikeout", "Underline") and c:
                    parts.append(_inlines_to_text(c[0]))
    return "".join(parts)


def meta_title(ast: dict[str, Any]) -> str | None:
    title = (ast.get("meta") or {}).get("title")
    if not isinstance(title, dict):
        return None
    if title.get("t") == "MetaInlines":
        text = _inlines_to_text(title.get("c") or []).strip()
        return text or None
    return None
