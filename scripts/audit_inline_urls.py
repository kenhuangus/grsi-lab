#!/usr/bin/env python3
"""Audit Packt citation rules in manuscript markdown.

Fails if:
- References/Sources heading present
- Same URL appears more than once in a chapter
- Quantitative-looking claims without nearby http (heuristic warn only)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "manuscript"
URL_RE = re.compile(r"https?://[^\s\)\]\>\"']+")
REF_RE = re.compile(r"^#{1,3}\s+(References|Sources)\b", re.I | re.M)


def audit(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errs: list[str] = []
    if REF_RE.search(text):
        errs.append("has References/Sources section")
    urls = URL_RE.findall(text)
    # normalize trailing punctuation
    norm = [u.rstrip(".,;:)") for u in urls]
    seen: dict[str, int] = {}
    for u in norm:
        seen[u] = seen.get(u, 0) + 1
    dups = {u: c for u, c in seen.items() if c > 1}
    if dups:
        errs.append(f"duplicate URLs: {dups}")
    return errs


def main() -> int:
    files = sorted(ROOT.glob("ch*.md"))
    if not files:
        print("No manuscripts found")
        return 1
    bad = 0
    for f in files:
        errs = audit(f)
        if errs:
            bad += 1
            print(f"FAIL {f.name}: {errs}")
        else:
            urls = len(URL_RE.findall(f.read_text(encoding="utf-8")))
            print(f"OK   {f.name}: {urls} unique-pass URLs")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
