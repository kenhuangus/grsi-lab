#!/usr/bin/env python3
"""Publish manuscript/chNN.md into GRSI Google Doc with Packt template styling.

Local manuscript/ is staging only — never push to GitHub.
Template: docs/PACKT_FORMAT.md (from LLM DP Ch8 Doc 1VkUK66uM_...).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GWS = Path(r"C:\Users\kenhu\AppData\Roaming\npm\node_modules\@googleworkspace\cli\bin\gws.exe")
os.environ["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(Path.home() / ".config/gws-profiles/kenhuangus")
os.environ["GOOGLE_WORKSPACE_CLI_ACCOUNT"] = "kenhuangus@gmail.com"

BODY_FG = {"color": {"rgbColor": {"red": 0.06666667, "green": 0.09411765, "blue": 0.15294118}}}
H_FG = {"color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}}
H3_FG = {"color": {"rgbColor": {"red": 0.18039216, "green": 0.45882353, "blue": 0.7137255}}}
CODE_SHADE = {"backgroundColor": {"color": {"rgbColor": {"red": 0.95686275, "green": 0.9647059, "blue": 0.98039216}}}}
CODE_BORDER = {
    "color": {"color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}},
    "dashStyle": "SOLID",
    "padding": {"magnitude": 6, "unit": "PT"},
    "width": {"magnitude": 2.25, "unit": "PT"},
}


def gws(*args: str) -> dict:
    r = subprocess.run([str(GWS), *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or b"").decode("utf-8", "replace"))
    if not r.stdout:
        return {}
    return json.loads(r.stdout.decode("utf-8"))


def clear_body(doc_id: str) -> None:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    end = doc["body"]["content"][-1]["endIndex"]
    if end <= 2:
        return
    gws(
        "docs",
        "documents",
        "batchUpdate",
        "--params",
        json.dumps({"documentId": doc_id}),
        "--json",
        json.dumps(
            {
                "requests": [
                    {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}}
                ]
            }
        ),
    )


def parse_md(text: str, chapter_num: int, chapter_title: str) -> list[dict]:
    """Return list of {kind, text} blocks: opener_num, opener_title, h1, h2, h3, body, code."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Drop leading # Chapter line if present — we rebuild opener
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
        if para:
            for p in re.split(r"\n\s*\n", para):
                p = p.strip()
                if p:
                    # unwrap markdown emphasis lightly
                    p = re.sub(r"\*\*(.+?)\*\*", r"\1", p)
                    p = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", p)
                    blocks.append({"kind": "body", "text": p})

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
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            flush_body()
            level = len(m.group(1))
            title = m.group(2).strip()
            kind = {1: "h1", 2: "h2", 3: "h3"}[level]
            # Map markdown # section -> Packt HEADING_1, ## -> H2, ### -> H3
            # Our manuscripts use ## for main sections → treat ## as h1, ### as h2
            if level == 1:
                kind = "h1"
            elif level == 2:
                kind = "h1"
            else:
                kind = "h2"
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


def build_insert_requests(blocks: list[dict]) -> tuple[str, list[dict]]:
    """Build full text + style update requests with indices after insert at 1."""
    parts: list[str] = []
    spans: list[tuple[str, int, int, str]] = []  # kind, start, end, text

    def add(kind: str, text: str) -> None:
        # Docs needs newline at end of each paragraph
        chunk = text if text.endswith("\n") else text + "\n"
        start = 1 + sum(len(p) for p in parts)
        parts.append(chunk)
        end = 1 + sum(len(p) for p in parts)
        spans.append((kind, start, end, chunk))

    for b in blocks:
        kind = b["kind"]
        t = b["text"]
        if kind == "code":
            # one paragraph per code line for shading borders (Packt template pattern)
            code_lines = t.split("\n") if t else [""]
            for li, cl in enumerate(code_lines):
                add("code", cl)
        else:
            add(kind, t)

    full = "".join(parts)
    style_reqs: list[dict] = []
    for kind, start, end, chunk in spans:
        # paragraph is [start, end) including trailing \n; style range excludes final newline often
        # Docs: endIndex exclusive; for updateParagraphStyle use startIndex of para through endIndex-1 content
        if end <= start + 1:
            continue
        para_end = end  # includes newline
        text_end = end - 1 if chunk.endswith("\n") else end

        if kind == "opener_num":
            style_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "NORMAL_TEXT", "spaceBelow": {"unit": "PT"}},
                        "fields": "namedStyleType,spaceBelow",
                    }
                }
            )
            style_reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": text_end},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Jost", "weight": 400},
                            "fontSize": {"magnitude": 84, "unit": "PT"},
                            "foregroundColor": BODY_FG,
                        },
                        "fields": "weightedFontFamily,fontSize,foregroundColor",
                    }
                }
            )
        elif kind == "opener_title":
            style_reqs.append(
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
            style_reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": text_end},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Jost", "weight": 400},
                            "fontSize": {"magnitude": 28, "unit": "PT"},
                            "foregroundColor": BODY_FG,
                        },
                        "fields": "weightedFontFamily,fontSize,foregroundColor",
                    }
                }
            )
        elif kind == "h1":
            style_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            )
            style_reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": text_end},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
                            "fontSize": {"magnitude": 16, "unit": "PT"},
                            "bold": True,
                            "foregroundColor": H_FG,
                        },
                        "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                    }
                }
            )
        elif kind == "h2":
            style_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                }
            )
            style_reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": text_end},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
                            "fontSize": {"magnitude": 14, "unit": "PT"},
                            "bold": True,
                            "foregroundColor": H_FG,
                        },
                        "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                    }
                }
            )
        elif kind == "h3":
            style_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {"namedStyleType": "HEADING_3"},
                        "fields": "namedStyleType",
                    }
                }
            )
            style_reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": text_end},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
                            "fontSize": {"magnitude": 12, "unit": "PT"},
                            "bold": True,
                            "foregroundColor": H3_FG,
                        },
                        "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                    }
                }
            )
        elif kind == "body":
            style_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": para_end},
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                            "lineSpacing": 115,
                            "spaceBelow": {"magnitude": 10, "unit": "PT"},
                        },
                        "fields": "namedStyleType,lineSpacing,spaceBelow",
                    }
                }
            )
            style_reqs.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start, "endIndex": text_end},
                        "textStyle": {
                            "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 400},
                            "fontSize": {"magnitude": 10.5, "unit": "PT"},
                            "bold": False,
                            "foregroundColor": BODY_FG,
                        },
                        "fields": "weightedFontFamily,fontSize,bold,foregroundColor",
                    }
                }
            )
        elif kind == "code":
            style_reqs.append(
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
                style_reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start, "endIndex": text_end},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Consolas", "weight": 400},
                                "fontSize": {"magnitude": 9, "unit": "PT"},
                                "foregroundColor": BODY_FG,
                            },
                            "fields": "weightedFontFamily,fontSize,foregroundColor",
                        }
                    }
                )
    return full, style_reqs


def linkify_urls(doc_id: str) -> int:
    """Make each https URL a hyperlink (first occurrence already unique in manuscript)."""
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
    # batch in chunks of 50
    for i in range(0, len(reqs), 50):
        gws(
            "docs",
            "documents",
            "batchUpdate",
            "--params",
            json.dumps({"documentId": doc_id}),
            "--json",
            json.dumps({"requests": reqs[i : i + 50]}),
        )
        time.sleep(0.3)
    return len(reqs)


def publish(chapter: int) -> None:
    ids = json.loads((ROOT / "docs" / "GDOC_IDS.json").read_text(encoding="utf-8"))
    doc_id = ids["chapters"][str(chapter)]
    title = ids.get("titles", {}).get(str(chapter), f"Chapter {chapter}")
    # Strip "GRSI Ch0N — " prefix for opener title
    opener = re.sub(r"^GRSI Ch\d+\s*[—\-]\s*", "", title).strip()
    md_path = ROOT / "manuscript" / f"ch{chapter:02d}.md"
    if not md_path.exists():
        raise FileNotFoundError(md_path)
    md = md_path.read_text(encoding="utf-8")
    blocks = parse_md(md, chapter, opener)
    full, style_reqs = build_insert_requests(blocks)
    print(f"ch{chapter}: {len(full)} chars, {len(blocks)} blocks, {len(style_reqs)} style ops -> {doc_id}")

    clear_body(doc_id)
    time.sleep(0.4)

    # Insert text (chunk if huge)
    chunk = 35000
    idx = 1
    for i in range(0, len(full), chunk):
        part = full[i : i + chunk]
        gws(
            "docs",
            "documents",
            "batchUpdate",
            "--params",
            json.dumps({"documentId": doc_id}),
            "--json",
            json.dumps({"requests": [{"insertText": {"location": {"index": idx}, "text": part}}]}),
        )
        idx += len(part)
        time.sleep(0.4)

    # Style in batches
    for i in range(0, len(style_reqs), 40):
        batch = style_reqs[i : i + 40]
        gws(
            "docs",
            "documents",
            "batchUpdate",
            "--params",
            json.dumps({"documentId": doc_id}),
            "--json",
            json.dumps({"requests": batch}),
        )
        time.sleep(0.5)

    n_links = linkify_urls(doc_id)
    print(f"ch{chapter}: styled OK, {n_links} hyperlinks")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ch", type=int, nargs="+", required=True)
    args = ap.parse_args()
    for n in args.ch:
        publish(n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
