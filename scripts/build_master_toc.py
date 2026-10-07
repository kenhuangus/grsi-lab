#!/usr/bin/env python3
"""Rebuild GRSI master TOC Google Doc with clickable links to all chapters."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gws_env import configure_gws_env  # noqa: E402

GWS = configure_gws_env()

BODY_FG = {"color": {"rgbColor": {"red": 0.06666667, "green": 0.09411765, "blue": 0.15294118}}}
H_FG = {"color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}}


def gws(*args: str) -> dict:
    r = subprocess.run([str(GWS), *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or b"").decode("utf-8", "replace"))
    if not r.stdout:
        return {}
    return json.loads(r.stdout.decode("utf-8"))


def gws_batch(doc_id: str, requests: list[dict]) -> dict:
    return gws(
        "docs",
        "documents",
        "batchUpdate",
        "--params",
        json.dumps({"documentId": doc_id}),
        "--json",
        json.dumps({"requests": requests}, ensure_ascii=False),
    )


def clear_body(doc_id: str) -> None:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    end = doc["body"]["content"][-1]["endIndex"]
    if end <= 2:
        return
    gws_batch(doc_id, [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}}])


def chapter_title_short(full: str) -> str:
    return re.sub(r"^GRSI Ch\d+\s*[—\-]\s*", "", full).strip()


def build_segments(manifest: dict, gdoc: dict) -> list[dict]:
    """Each segment: text (with trailing newline), kind, url optional."""
    segs: list[dict] = []
    segs.append({"text": "Governed Recursive Self-Improvement\n", "kind": "title"})
    segs.append({"text": f"{manifest['subtitle']}\n", "kind": "subtitle"})
    segs.append({"text": f"Author: {manifest['author']}\nPublisher: {manifest['publisher']}\n\n", "kind": "body"})
    segs.append({"text": "Master table of contents\n", "kind": "h1"})
    segs.append(
        {
            "text": "Use this document as the master index. Open any chapter from the links below. "
            "Chapter manuscripts live in Google Docs only; companion code is on GitHub.\n\n",
            "kind": "body",
        }
    )

    segs.append({"text": "Project links\n", "kind": "h2"})
    proposal_url = (
        f"https://docs.google.com/document/d/{manifest['proposal_doc_id']}/edit"
    )
    github_url = f"https://github.com/{manifest['github_repo']}"
    segs.append(
        {
            "text": "Packt proposal (locked outline)\n",
            "kind": "link_line",
            "url": proposal_url,
        }
    )
    segs.append(
        {
            "text": "GitHub companion lab (code only — not chapter prose)\n",
            "kind": "link_line",
            "url": github_url,
        }
    )
    segs.append({"text": "\n", "kind": "body"})

    titles = gdoc.get("titles") or {}
    links = gdoc.get("webViewLinks") or {}

    for part in manifest["parts"]:
        segs.append({"text": f"Part {part['id']}: {part['title']}\n", "kind": "h2"})
        for ch_num in part["chapters"]:
            ch_key = str(ch_num)
            ch_entry = next(c for c in manifest["chapters"] if c["number"] == ch_num)
            short = chapter_title_short(titles.get(ch_key, ch_entry["title"]))
            url = links.get(ch_key) or (
                f"https://docs.google.com/document/d/{gdoc['chapters'][ch_key]}/edit"
            )
            line = f"Chapter {ch_num}: {short}\n"
            segs.append({"text": line, "kind": "link_line", "url": url})
            segs.append(
                {
                    "text": f"  Page budget (target): {ch_entry['page_budget']} pages\n",
                    "kind": "body",
                }
            )
        segs.append({"text": "\n", "kind": "body"})

    segs.append({"text": "Editorial rules (all chapters)\n", "kind": "h2"})
    segs.append(
        {
            "text": "Inline hyperlinked URLs only; no end-of-chapter References section. "
            "Each distinct URL appears once per chapter. Numbers grounded in VERIFIED_FACTS.\n",
            "kind": "body",
        }
    )
    segs.append(
        {
            "text": f"Last rebuilt from {ROOT.name} manifest and GDOC_IDS.json.\n",
            "kind": "body",
        }
    )
    return segs


def apply_content(doc_id: str, segments: list[dict]) -> None:
    full = "".join(s["text"] for s in segments)
    clear_body(doc_id)
    time.sleep(0.3)

    idx = 1
    chunk = 8000
    for i in range(0, len(full), chunk):
        part = full[i : i + chunk]
        gws_batch(doc_id, [{"insertText": {"location": {"index": idx}, "text": part}}])
        idx += len(part)
        time.sleep(0.25)

    # Style + links by walking segments from index 1
    pos = 1
    link_reqs: list[dict] = []
    para_reqs: list[dict] = []
    for seg in segments:
        text = seg["text"]
        start = pos
        end = pos + len(text)
        kind = seg["kind"]
        # paragraph styling (exclude trailing newline-only from text style where empty)
        text_end = end - 1 if text.endswith("\n") else end
        if kind == "title" and text.strip():
            para_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": end},
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                            "spaceBelow": {"magnitude": 6, "unit": "PT"},
                        },
                        "fields": "namedStyleType,spaceBelow",
                    }
                }
            )
            if text_end > start:
                link_reqs.append(
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
        elif kind == "subtitle" and text.strip():
            if text_end > start:
                link_reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start, "endIndex": text_end},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Jost", "weight": 400},
                                "fontSize": {"magnitude": 14, "unit": "PT"},
                                "foregroundColor": BODY_FG,
                            },
                            "fields": "weightedFontFamily,fontSize,foregroundColor",
                        }
                    }
                )
        elif kind == "h1" and text.strip():
            para_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": end},
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            )
            if text_end > start:
                link_reqs.append(
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
        elif kind == "h2" and text.strip():
            para_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": end},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                }
            )
            if text_end > start:
                link_reqs.append(
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
        elif kind == "link_line" and seg.get("url"):
            if text_end > start:
                link_reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start, "endIndex": text_end},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 400},
                                "fontSize": {"magnitude": 11, "unit": "PT"},
                                "foregroundColor": BODY_FG,
                                "link": {"url": seg["url"]},
                            },
                            "fields": "weightedFontFamily,fontSize,foregroundColor,link",
                        }
                    }
                )
        elif kind == "body" and text.strip():
            para_reqs.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": end},
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                            "lineSpacing": 115,
                        },
                        "fields": "namedStyleType,lineSpacing",
                    }
                }
            )
            if text_end > start:
                link_reqs.append(
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": start, "endIndex": text_end},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 400},
                                "fontSize": {"magnitude": 10.5, "unit": "PT"},
                                "foregroundColor": BODY_FG,
                            },
                            "fields": "weightedFontFamily,fontSize,foregroundColor",
                        }
                    }
                )
        pos = end

    for i in range(0, len(para_reqs), 15):
        gws_batch(doc_id, para_reqs[i : i + 15])
        time.sleep(0.3)
    for i in range(0, len(link_reqs), 15):
        gws_batch(doc_id, link_reqs[i : i + 15])
        time.sleep(0.3)


def rename_doc(doc_id: str, name: str) -> None:
    gws(
        "drive",
        "files",
        "update",
        "--params",
        json.dumps({"fileId": doc_id}),
        "--json",
        json.dumps({"name": name}),
    )


def main() -> int:
    manifest = json.loads((ROOT / "BOOK_MANIFEST.json").read_text(encoding="utf-8"))
    gdoc = json.loads((ROOT / "docs" / "GDOC_IDS.json").read_text(encoding="utf-8"))
    toc_id = manifest.get("toc_doc_id") or gdoc["toc"]
    segments = build_segments(manifest, gdoc)
    apply_content(toc_id, segments)
    rename_doc(toc_id, "GRSI — Master TOC (Chapters 1–10)")
    url = gdoc["webViewLinks"].get("toc") or f"https://docs.google.com/document/d/{toc_id}/edit"
    print("Master TOC rebuilt:", toc_id)
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
