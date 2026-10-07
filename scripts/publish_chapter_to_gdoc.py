#!/usr/bin/env python3
"""Publish manuscript/chNN.md into GRSI Google Doc with Packt styling.

Inserts:
  - Real Google Docs tables (not markdown pipes)
  - PNG figures from manuscript SVG refs (lead-in already in prose; caption under image)
  - Parenthetical https:// URLs as Docs hyperlinks

Local manuscript/ is staging only — never push to GitHub.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gws_env import configure_gws_env  # noqa: E402

GWS = configure_gws_env()

BODY_FG = {"color": {"rgbColor": {"red": 0.06666667, "green": 0.09411765, "blue": 0.15294118}}}
H_FG = {"color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}}
H3_FG = {"color": {"rgbColor": {"red": 0.18039216, "green": 0.45882353, "blue": 0.7137255}}}
CODE_SHADE = {
    "backgroundColor": {
        "color": {"rgbColor": {"red": 0.95686275, "green": 0.9647059, "blue": 0.98039216}}
    }
}
CODE_BORDER = {
    "color": {"color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}},
    "dashStyle": "SOLID",
    "padding": {"magnitude": 6, "unit": "PT"},
    "width": {"magnitude": 2.25, "unit": "PT"},
}

FIG_WIDTH_PT = 468.0  # ~6.5" within US Letter margins


def gws(*args: str) -> dict:
    r = subprocess.run([str(GWS), *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or b"").decode("utf-8", "replace"))
    if not r.stdout:
        return {}
    return json.loads(r.stdout.decode("utf-8"))


def gws_batch(doc_id: str, requests: list[dict], retries: int = 8) -> dict:
    last_err = ""
    for attempt in range(retries):
        try:
            return gws(
                "docs",
                "documents",
                "batchUpdate",
                "--params",
                json.dumps({"documentId": doc_id}),
                "--json",
                json.dumps({"requests": requests}, ensure_ascii=False),
            )
        except RuntimeError as e:
            last_err = str(e)
            if "Quota exceeded" not in last_err and "RATE_LIMIT" not in last_err:
                raise
            wait = min(90, 8 * (2**attempt))
            print(f"  quota wait {wait}s (attempt {attempt+1})", flush=True)
            time.sleep(wait)
    raise RuntimeError(last_err)


def clear_body(doc_id: str) -> None:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    end = doc["body"]["content"][-1]["endIndex"]
    if end <= 2:
        return
    gws_batch(doc_id, [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}}])


def doc_end_index(doc_id: str) -> int:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    return doc["body"]["content"][-1]["endIndex"]


def strip_md_light(p: str) -> str:
    p = re.sub(r"\*\*(.+?)\*\*", r"\1", p)
    p = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", p)
    p = re.sub(r"`([^`]+)`", r"\1", p)
    return p


def parse_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [strip_md_light(c.strip()) for c in line.split("|")]


def is_table_sep(line: str) -> bool:
    s = line.strip().replace(" ", "")
    return bool(re.match(r"^\|?:?-{3,}:?(\|:?-{3,}:?)*\|?$", s))


def resolve_figure_png(md_path: str, chapter: int) -> Path | None:
    """Map ../figures/chNN/fig.svg -> local PNG (preferred) or SVG."""
    raw = md_path.strip()
    # normalize
    raw = raw.replace("\\", "/")
    if raw.startswith("../"):
        cand = (ROOT / "manuscript" / raw).resolve()
    elif raw.startswith("figures/"):
        cand = (ROOT / raw).resolve()
    else:
        cand = Path(raw)
        if not cand.is_absolute():
            cand = (ROOT / raw).resolve()
    png = cand.with_suffix(".png")
    if png.exists():
        return png
    if cand.exists() and cand.suffix.lower() == ".png":
        return cand
    # try chapter figures dir by stem
    stem = cand.stem
    alt = ROOT / "figures" / f"ch{chapter:02d}" / f"{stem}.png"
    if alt.exists():
        return alt
    return None


def parse_md(text: str, chapter_num: int, chapter_title: str) -> list[dict]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if lines and re.match(r"^#\s+Chapter\s+\d+", lines[0], re.I):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]

    blocks: list[dict] = [
        {"kind": "opener_num", "text": str(chapter_num)},
        {"kind": "opener_title", "text": chapter_title},
    ]
    i = 0
    in_code = False
    code_buf: list[str] = []
    body_buf: list[str] = []

    def flush_body() -> None:
        nonlocal body_buf
        para = "\n".join(body_buf).strip()
        body_buf = []
        if not para:
            return
        for p in re.split(r"\n\s*\n", para):
            p = p.strip()
            if not p:
                continue
            p = strip_md_light(p)
            # skip lone image lines accidentally buffered
            if re.match(r"^!\[", p):
                continue
            kind = "caption" if re.match(r"^(Figure|Table)\s+\d+\.\d+:", p) else "body"
            blocks.append({"kind": kind, "text": p})

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            if in_code:
                blocks.append({"kind": "code", "text": "\n".join(code_buf)})
                code_buf = []
                in_code = False
            else:
                flush_body()
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # Markdown table
        if "|" in line and line.strip().startswith("|"):
            flush_body()
            rows: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
                if is_table_sep(lines[i]):
                    i += 1
                    continue
                rows.append(parse_table_row(lines[i]))
                i += 1
            if rows:
                # normalize column count
                cols = max(len(r) for r in rows)
                rows = [r + [""] * (cols - len(r)) for r in rows]
                # skip blank lines before Table N.M caption
                while i < len(lines) and not lines[i].strip():
                    i += 1
                caption = ""
                if i < len(lines) and re.match(r"^Table\s+\d+\.\d+:", lines[i].strip()):
                    caption = strip_md_light(lines[i].strip())
                    i += 1
                blocks.append({"kind": "table", "rows": rows, "caption": caption})
            continue

        # Figure image
        m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line.strip())
        if m_img:
            flush_body()
            alt = m_img.group(1).strip()
            path = m_img.group(2).strip()
            caption = ""
            # allow blank line between image and Figure N.M caption
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and re.match(r"^Figure\s+\d+\.\d+:", lines[j].strip()):
                caption = strip_md_light(lines[j].strip())
                i = j + 1
            else:
                i += 1
                if not caption and alt:
                    caption = strip_md_light(
                        alt if alt.lower().startswith("figure") else f"Figure: {alt}"
                    )
            png = resolve_figure_png(path, chapter_num)
            blocks.append(
                {
                    "kind": "figure",
                    "path": str(png) if png else path,
                    "png": png,
                    "caption": caption,
                    "alt": alt,
                }
            )
            continue

        # Packt Docs styles only distinguish H1 (##) vs H2 (###+).
        # Accept ####+ so raw hash markers never leak into body text.
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_body()
            level = len(m.group(1))
            title = m.group(2).strip()
            kind = "h1" if level <= 2 else "h2"
            blocks.append({"kind": kind, "text": title})
            i += 1
            continue
        if line.strip() == "---":
            i += 1
            continue
        body_buf.append(line)
        i += 1

    flush_body()
    if in_code and code_buf:
        blocks.append({"kind": "code", "text": "\n".join(code_buf)})
    return blocks


def style_paragraph(
    doc_id: str, start: int, end: int, kind: str, text: str
) -> None:
    if end <= start + 1:
        return
    para_end = end
    text_end = end - 1 if text.endswith("\n") else end
    reqs: list[dict] = []

    def text_style(family: str, size: float, bold: bool, fg: dict, italic: bool = False) -> dict:
        fields = "weightedFontFamily,fontSize,bold,foregroundColor"
        style = {
            "weightedFontFamily": {"fontFamily": family, "weight": 700 if bold else 400},
            "fontSize": {"magnitude": size, "unit": "PT"},
            "bold": bold,
            "foregroundColor": fg,
        }
        if italic:
            style["italic"] = True
            fields += ",italic"
        return {
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": text_end},
                "textStyle": style,
                "fields": fields,
            }
        }

    if kind == "opener_num":
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": para_end},
                    "paragraphStyle": {"namedStyleType": "NORMAL_TEXT", "spaceBelow": {"unit": "PT"}},
                    "fields": "namedStyleType,spaceBelow",
                }
            }
        )
        if text_end > start:
            reqs.append(text_style("Jost", 84, False, BODY_FG))
    elif kind == "opener_title":
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": para_end},
                    "paragraphStyle": {
                        "namedStyleType": "NORMAL_TEXT",
                        "spaceBelow": {"magnitude": 15, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceBelow",
                }
            }
        )
        if text_end > start:
            reqs.append(text_style("Jost", 28, False, BODY_FG))
    elif kind == "h1":
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": para_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_1"},
                    "fields": "namedStyleType",
                }
            }
        )
        if text_end > start:
            reqs.append(text_style("Jost", 16, True, H_FG))
    elif kind == "h2":
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": para_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType",
                }
            }
        )
        if text_end > start:
            reqs.append(text_style("Jost", 14, True, H_FG))
    elif kind in ("body", "caption"):
        para_style = {
            "namedStyleType": "NORMAL_TEXT",
            "lineSpacing": 115,
            "spaceBelow": {"magnitude": 10, "unit": "PT"},
        }
        fields = "namedStyleType,lineSpacing,spaceBelow"
        if kind == "caption":
            para_style["alignment"] = "CENTER"
            fields += ",alignment"
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": para_end},
                    "paragraphStyle": para_style,
                    "fields": fields,
                }
            }
        )
        if text_end > start:
            italic = kind == "caption"
            reqs.append(text_style("Crimson Pro", 10.5 if not italic else 10, False, BODY_FG, italic=italic))
    elif kind == "code":
        reqs.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": para_end},
                    "paragraphStyle": {
                        "namedStyleType": "NORMAL_TEXT",
                        "indentStart": {"magnitude": 10, "unit": "PT"},
                        "indentFirstLine": {"magnitude": 10, "unit": "PT"},
                        "spaceAbove": {"unit": "PT"},
                        "spaceBelow": {"unit": "PT"},
                        "shading": CODE_SHADE,
                        "borderLeft": CODE_BORDER,
                    },
                    "fields": "namedStyleType,indentStart,indentFirstLine,spaceAbove,spaceBelow,shading,borderLeft",
                }
            }
        )
        if text_end > start:
            reqs.append(text_style("Consolas", 9, False, BODY_FG))

    if reqs:
        gws_batch(doc_id, reqs)
        time.sleep(0.35)


def insert_text_block(doc_id: str, kind: str, text: str) -> None:
    chunk = text if text.endswith("\n") else text + "\n"
    idx = doc_end_index(doc_id) - 1
    gws_batch(doc_id, [{"insertText": {"location": {"index": idx}, "text": chunk}}])
    time.sleep(0.25)
    style_paragraph(doc_id, idx, idx + len(chunk), kind, chunk)


def prepare_docs_png(png: Path, max_width: int = 1600) -> Path:
    """Downscale publication 10x PNGs for Docs inline insert (size limit)."""
    from PIL import Image

    out = ROOT / "figures" / "_docs_cache" / f"{png.stem}_docs.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_mtime >= png.stat().st_mtime:
        return out
    im = Image.open(png)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    w, h = im.size
    if w > max_width:
        nh = int(h * (max_width / w))
        im = im.resize((max_width, nh), Image.Resampling.LANCZOS)
    # flatten on white if RGBA
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        im = bg
    im.save(out, format="PNG", optimize=True)
    return out


def upload_png_public(png: Path) -> str:
    """Upload PNG to Drive, share as reader, return a Docs-usable URI."""
    docs_png = prepare_docs_png(png)
    name = f"grsi-fig-{docs_png.stem}-{uuid.uuid4().hex[:8]}.png"
    meta = gws(
        "drive",
        "files",
        "create",
        "--params",
        json.dumps({"uploadType": "multipart"}),
        "--json",
        json.dumps({"name": name, "mimeType": "image/png"}),
        "--upload",
        str(docs_png),
        "--upload-content-type",
        "image/png",
    )
    file_id = meta["id"]
    gws(
        "drive",
        "permissions",
        "create",
        "--params",
        json.dumps({"fileId": file_id}),
        "--json",
        json.dumps({"role": "reader", "type": "anyone"}),
    )
    time.sleep(0.4)
    return f"https://drive.google.com/uc?export=view&id={file_id}"


def insert_figure(doc_id: str, block: dict) -> None:
    png: Path | None = block.get("png")
    caption = block.get("caption") or ""
    if png is None or not Path(png).exists():
        # fallback note so lead-in is not orphaned
        note = f"[Figure image missing: {block.get('path')}]\n"
        insert_text_block(doc_id, "body", note)
        if caption:
            insert_text_block(doc_id, "caption", caption)
        return

    uri = upload_png_public(Path(png))
    idx = doc_end_index(doc_id) - 1
    # spacer newline then image
    gws_batch(doc_id, [{"insertText": {"location": {"index": idx}, "text": "\n"}}])
    time.sleep(0.2)
    idx = doc_end_index(doc_id) - 1
    gws_batch(
        doc_id,
        [
            {
                "insertInlineImage": {
                    "location": {"index": idx},
                    "uri": uri,
                    "objectSize": {
                        "width": {"magnitude": FIG_WIDTH_PT, "unit": "PT"},
                    },
                }
            }
        ],
    )
    time.sleep(0.6)
    # newline after image so caption is its own paragraph
    idx = doc_end_index(doc_id) - 1
    gws_batch(doc_id, [{"insertText": {"location": {"index": idx}, "text": "\n"}}])
    time.sleep(0.2)
    if caption:
        insert_text_block(doc_id, "caption", caption)


def insert_table(doc_id: str, block: dict) -> None:
    rows: list[list[str]] = block["rows"]
    caption = block.get("caption") or ""
    n_rows = len(rows)
    n_cols = len(rows[0]) if rows else 0
    if n_rows == 0 or n_cols == 0:
        return

    idx = doc_end_index(doc_id) - 1
    gws_batch(
        doc_id,
        [{"insertTable": {"rows": n_rows, "columns": n_cols, "location": {"index": idx}}}],
    )
    time.sleep(0.6)

    # Refetch and fill cells (first paragraph in each cell)
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    table = None
    for el in doc["body"]["content"]:
        if "table" in el:
            table = el
    if table is None:
        # fallback: last table-ish — walk all
        tables = [el for el in doc["body"]["content"] if "table" in el]
        table = tables[-1] if tables else None
    if table is None:
        raise RuntimeError("insertTable succeeded but table not found in document")

    fill_reqs: list[dict] = []
    style_reqs: list[dict] = []
    for r_i, row in enumerate(table["table"]["tableRows"]):
        for c_i, cell in enumerate(row["tableCells"]):
            # content[0] is paragraph; insert at startIndex of first text element
            para = cell["content"][0]
            # empty cell has paragraph with one newline textRun
            start = para["startIndex"]
            text = rows[r_i][c_i] if r_i < len(rows) and c_i < len(rows[r_i]) else ""
            if text:
                fill_reqs.append({"insertText": {"location": {"index": start}, "text": text}})
            # header row bold
            if r_i == 0 and text:
                end = start + len(text)
                style_reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start, "endIndex": end},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 700},
                                "fontSize": {"magnitude": 10, "unit": "PT"},
                                "bold": True,
                                "foregroundColor": BODY_FG,
                            },
                            "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                        }
                    }
                )
            elif text:
                end = start + len(text)
                style_reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start, "endIndex": end},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 400},
                                "fontSize": {"magnitude": 10, "unit": "PT"},
                                "foregroundColor": BODY_FG,
                            },
                            "fields": "weightedFontFamily,fontSize,foregroundColor",
                        }
                    }
                )

    # Insert into cells from bottom-right to top-left so indices stay valid
    # Actually inserting at start of each empty cell: if we go top-left to bottom-right,
    # later cell indices shift. So reverse order.
    for req in reversed(fill_reqs):
        gws_batch(doc_id, [req])
        time.sleep(0.2)

    # Restyle after fill — refetch indices
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    tables = [el for el in doc["body"]["content"] if "table" in el]
    table = tables[-1]
    style_reqs = []
    for r_i, row in enumerate(table["table"]["tableRows"]):
        for c_i, cell in enumerate(row["tableCells"]):
            for pel in cell.get("content", []):
                p = pel.get("paragraph")
                if not p:
                    continue
                for e in p.get("elements", []):
                    tr = e.get("textRun")
                    if not tr or not (tr.get("content") or "").strip():
                        continue
                    start = e["startIndex"]
                    end = e["endIndex"]
                    # trim trailing newline from style range
                    content = tr["content"]
                    if content.endswith("\n"):
                        end = end - 1
                    if end <= start:
                        continue
                    bold = r_i == 0
                    style_reqs.append(
                        {
                            "updateTextStyle": {
                                "range": {"startIndex": start, "endIndex": end},
                                "textStyle": {
                                    "weightedFontFamily": {
                                        "fontFamily": "Crimson Pro",
                                        "weight": 700 if bold else 400,
                                    },
                                    "fontSize": {"magnitude": 10, "unit": "PT"},
                                    "bold": bold,
                                    "foregroundColor": BODY_FG,
                                },
                                "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                            }
                        }
                    )
    for i in range(0, len(style_reqs), 10):
        gws_batch(doc_id, style_reqs[i : i + 10])
        time.sleep(0.4)

    if caption:
        insert_text_block(doc_id, "caption", caption)


def linkify_urls(doc_id: str) -> int:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    reqs = []
    for el in doc["body"]["content"]:
        p = el.get("paragraph")
        if not p:
            continue
        for e in p.get("elements", []):
            tr = e.get("textRun")
            if not tr:
                continue
            content = tr.get("content") or ""
            style = tr.get("textStyle") or {}
            if style.get("link"):
                continue
            for m in re.finditer(r"https://[^\s\)\]\>\"']+", content):
                url = m.group(0).rstrip(".,;:)")
                abs_start = e["startIndex"] + m.start()
                abs_end = e["startIndex"] + m.start() + len(url)
                reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": abs_start, "endIndex": abs_end},
                            "textStyle": {"link": {"url": url}},
                            "fields": "link",
                        }
                    }
                )
    if not reqs:
        return 0
    for i in range(0, len(reqs), 15):
        gws_batch(doc_id, reqs[i : i + 15])
        time.sleep(0.5)
    return len(reqs)


def extract_plain_map(doc: dict) -> str:
    """Concatenate body text runs in order (for placeholder search)."""
    parts: list[str] = []
    for el in doc["body"]["content"]:
        p = el.get("paragraph")
        if not p:
            continue
        for e in p.get("elements", []):
            tr = e.get("textRun")
            if tr and tr.get("content"):
                parts.append(tr["content"])
    return "".join(parts)


def find_placeholder(doc_id: str, token: str) -> int | None:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    for el in doc["body"]["content"]:
        p = el.get("paragraph")
        if not p:
            continue
        for e in p.get("elements", []):
            tr = e.get("textRun")
            if not tr:
                continue
            content = tr.get("content") or ""
            at = content.find(token)
            if at >= 0:
                return e["startIndex"] + at
    return None


def build_document_stream(blocks: list[dict]) -> tuple[str, list[tuple[str, int, int, str]], list[dict]]:
    """Return full text, style spans, and media jobs (figure/table) with placeholders."""
    parts: list[str] = []
    spans: list[tuple[str, int, int, str]] = []
    media: list[dict] = []

    def add(kind: str, text: str) -> None:
        chunk = text if text.endswith("\n") else text + "\n"
        start = 1 + sum(len(p) for p in parts)
        parts.append(chunk)
        end = 1 + sum(len(p) for p in parts)
        spans.append((kind, start, end, chunk))

    fig_i = 0
    tab_i = 0
    for b in blocks:
        kind = b["kind"]
        if kind == "figure":
            token = f"⟦FIG{fig_i}⟧"
            add("body", token)
            media.append({"type": "figure", "token": token, "block": b})
            if b.get("caption"):
                add("caption", b["caption"])
            fig_i += 1
        elif kind == "table":
            token = f"⟦TAB{tab_i}⟧"
            add("body", token)
            media.append({"type": "table", "token": token, "block": b})
            # caption embedded in table insert; do not duplicate unless missing later
            tab_i += 1
        elif kind == "code":
            for cl in (b["text"].split("\n") if b["text"] else [""]):
                add("code", cl)
        else:
            add(kind, b["text"])

    return "".join(parts), spans, media


def style_spans(doc_id: str, spans: list[tuple[str, int, int, str]]) -> None:
    """Apply Packt styles in batched requests (quota-friendly)."""
    reqs: list[dict] = []
    for kind, start, end, chunk in spans:
        if end <= start + 1:
            continue
        para_end = end
        text_end = end - 1 if chunk.endswith("\n") else end

        def ts(family: str, size: float, bold: bool, fg: dict, italic: bool = False) -> dict:
            fields = "weightedFontFamily,fontSize,bold,foregroundColor"
            style = {
                "weightedFontFamily": {"fontFamily": family, "weight": 700 if bold else 400},
                "fontSize": {"magnitude": size, "unit": "PT"},
                "bold": bold,
                "foregroundColor": fg,
            }
            if italic:
                style["italic"] = True
                fields += ",italic"
            return {
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": max(start + 1, text_end)},
                    "textStyle": style,
                    "fields": fields,
                }
            }

        if kind == "opener_num":
            reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT", "spaceBelow": {"unit": "PT"}},
                        "fields": "namedStyleType,spaceBelow",
                    }
                }
            )
            if text_end > start:
                reqs.append(ts("Jost", 84, False, BODY_FG))
        elif kind == "opener_title":
            reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                            "spaceBelow": {"magnitude": 15, "unit": "PT"},
                        },
                        "fields": "namedStyleType,spaceBelow",
                    }
                }
            )
            if text_end > start:
                reqs.append(ts("Jost", 28, False, BODY_FG))
        elif kind == "h1":
            reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            )
            if text_end > start:
                reqs.append(ts("Jost", 16, True, H_FG))
        elif kind == "h2":
            reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                }
            )
            if text_end > start:
                reqs.append(ts("Jost", 14, True, H_FG))
        elif kind in ("body", "caption"):
            para_style = {
                "namedStyleType": "NORMAL_TEXT",
                "lineSpacing": 115,
                "spaceBelow": {"magnitude": 10, "unit": "PT"},
            }
            fields = "namedStyleType,lineSpacing,spaceBelow"
            if kind == "caption":
                para_style["alignment"] = "CENTER"
                fields += ",alignment"
            reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": para_style,
                        "fields": fields,
                    }
                }
            )
            if text_end > start:
                reqs.append(ts("Crimson Pro", 10 if kind == "caption" else 10.5, False, BODY_FG, italic=(kind == "caption")))
        elif kind == "code":
            reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                            "indentStart": {"magnitude": 10, "unit": "PT"},
                            "indentFirstLine": {"magnitude": 10, "unit": "PT"},
                            "spaceAbove": {"unit": "PT"},
                            "spaceBelow": {"unit": "PT"},
                            "shading": CODE_SHADE,
                            "borderLeft": CODE_BORDER,
                        },
                        "fields": "namedStyleType,indentStart,indentFirstLine,spaceAbove,spaceBelow,shading,borderLeft",
                    }
                }
            )
            if text_end > start:
                reqs.append(ts("Consolas", 9, False, BODY_FG))

    for i in range(0, len(reqs), 8):
        gws_batch(doc_id, reqs[i : i + 8])
        time.sleep(1.2)


def replace_media_placeholders(doc_id: str, media: list[dict]) -> None:
    """Replace ⟦FIG⟧ / ⟦TAB⟧ tokens from last to first with real images/tables."""
    for job in reversed(media):
        token = job["token"]
        idx = find_placeholder(doc_id, token)
        if idx is None:
            print(f"  missing placeholder {token}", flush=True)
            continue
        # delete token (+ following newline if present in same run — delete exact token)
        gws_batch(
            doc_id,
            [{"deleteContentRange": {"range": {"startIndex": idx, "endIndex": idx + len(token)}}}],
        )
        time.sleep(0.5)
        if job["type"] == "figure":
            insert_figure_at(doc_id, idx, job["block"])
        else:
            insert_table_at(doc_id, idx, job["block"])
        time.sleep(1.5)


def insert_figure_at(doc_id: str, idx: int, block: dict) -> None:
    png: Path | None = block.get("png")
    if png is None or not Path(png).exists():
        gws_batch(
            doc_id,
            [
                {
                    "insertText": {
                        "location": {"index": idx},
                        "text": f"[Figure image missing: {block.get('path')}]\n",
                    }
                }
            ],
        )
        return
    last_err = ""
    for attempt in range(4):
        try:
            uri = upload_png_public(Path(png))
            time.sleep(0.8 + attempt)
            gws_batch(
                doc_id,
                [
                    {
                        "insertInlineImage": {
                            "location": {"index": idx},
                            "uri": uri,
                            "objectSize": {"width": {"magnitude": FIG_WIDTH_PT, "unit": "PT"}},
                        }
                    }
                ],
            )
            time.sleep(0.4)
            gws_batch(doc_id, [{"insertText": {"location": {"index": idx + 1}, "text": "\n"}}])
            return
        except RuntimeError as e:
            last_err = str(e)
            if "retrieving the image" not in last_err and "image should be publicly" not in last_err:
                raise
            wait = 5 * (attempt + 1)
            print(f"  image insert retry in {wait}s (attempt {attempt+1})", flush=True)
            time.sleep(wait)
    raise RuntimeError(last_err)

def insert_table_at(doc_id: str, idx: int, block: dict) -> None:
    rows: list[list[str]] = block["rows"]
    caption = block.get("caption") or ""
    n_rows = len(rows)
    n_cols = len(rows[0]) if rows else 0
    if not n_rows or not n_cols:
        return
    gws_batch(
        doc_id,
        [{"insertTable": {"rows": n_rows, "columns": n_cols, "location": {"index": idx}}}],
    )
    time.sleep(0.8)
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    tables = [el for el in doc["body"]["content"] if "table" in el]
    # choose table whose startIndex is closest to idx
    table = min(tables, key=lambda el: abs(el.get("startIndex", 0) - idx))

    fill_reqs: list[dict] = []
    for r_i, row in enumerate(table["table"]["tableRows"]):
        for c_i, cell in enumerate(row["tableCells"]):
            para = cell["content"][0]
            start = para["startIndex"]
            text = rows[r_i][c_i] if r_i < len(rows) and c_i < len(rows[r_i]) else ""
            if text:
                fill_reqs.append({"insertText": {"location": {"index": start}, "text": text}})
    for req in reversed(fill_reqs):
        gws_batch(doc_id, [req])
        time.sleep(0.25)

    # style cells
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    tables = [el for el in doc["body"]["content"] if "table" in el]
    table = min(tables, key=lambda el: abs(el.get("startIndex", 0) - idx))
    style_reqs: list[dict] = []
    for r_i, row in enumerate(table["table"]["tableRows"]):
        for cell in row["tableCells"]:
            for pel in cell.get("content", []):
                p = pel.get("paragraph")
                if not p:
                    continue
                for e in p.get("elements", []):
                    tr = e.get("textRun")
                    if not tr or not (tr.get("content") or "").strip("\n"):
                        continue
                    start = e["startIndex"]
                    end = e["endIndex"]
                    if (tr.get("content") or "").endswith("\n"):
                        end -= 1
                    if end <= start:
                        continue
                    bold = r_i == 0
                    style_reqs.append(
                        {
                            "updateTextStyle": {
                                "range": {"startIndex": start, "endIndex": end},
                                "textStyle": {
                                    "weightedFontFamily": {
                                        "fontFamily": "Crimson Pro",
                                        "weight": 700 if bold else 400,
                                    },
                                    "fontSize": {"magnitude": 10, "unit": "PT"},
                                    "bold": bold,
                                    "foregroundColor": BODY_FG,
                                },
                                "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                            }
                        }
                    )
    for i in range(0, len(style_reqs), 8):
        gws_batch(doc_id, style_reqs[i : i + 8])
        time.sleep(0.8)

    if caption:
        # insert caption after table: table endIndex
        end_idx = table["endIndex"]
        chunk = caption if caption.endswith("\n") else caption + "\n"
        gws_batch(doc_id, [{"insertText": {"location": {"index": end_idx}, "text": chunk}}])
        time.sleep(0.4)
        style_paragraph(doc_id, end_idx, end_idx + len(chunk), "caption", chunk)


def publish(chapter: int) -> None:
    ids = json.loads((ROOT / "docs" / "GDOC_IDS.json").read_text(encoding="utf-8"))
    doc_id = ids["chapters"][str(chapter)]
    title = ids.get("titles", {}).get(str(chapter), f"Chapter {chapter}")
    opener = re.sub(r"^GRSI Ch\d+\s*[—\-]\s*", "", title).strip()
    md_path = ROOT / "manuscript" / f"ch{chapter:02d}.md"
    if not md_path.exists():
        raise FileNotFoundError(md_path)
    md = md_path.read_text(encoding="utf-8")
    blocks = parse_md(md, chapter, opener)
    full, spans, media = build_document_stream(blocks)

    n_tab = sum(1 for m in media if m["type"] == "table")
    n_fig = sum(1 for m in media if m["type"] == "figure")
    n_fig_ok = sum(1 for m in media if m["type"] == "figure" and m["block"].get("png"))
    print(
        f"ch{chapter}: {len(full)} chars, {len(spans)} spans, {n_tab} tables, {n_fig} figures ({n_fig_ok} png) -> {doc_id}",
        flush=True,
    )

    clear_body(doc_id)
    time.sleep(1.0)

    chunk = 5000
    idx = 1
    for i in range(0, len(full), chunk):
        part = full[i : i + chunk]
        gws_batch(doc_id, [{"insertText": {"location": {"index": idx}, "text": part}}])
        idx += len(part)
        time.sleep(0.8)

    print(f"ch{chapter}: text inserted; styling…", flush=True)
    style_spans(doc_id, spans)
    print(f"ch{chapter}: replacing {len(media)} media placeholders…", flush=True)
    replace_media_placeholders(doc_id, media)
    n_links = linkify_urls(doc_id)
    print(f"ch{chapter}: done — {n_tab} tables, {n_fig_ok}/{n_fig} figures, {n_links} links", flush=True)
    time.sleep(15.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ch", type=int, nargs="+", required=True)
    args = ap.parse_args()
    for n in args.ch:
        publish(n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
