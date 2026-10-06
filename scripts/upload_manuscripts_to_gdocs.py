#!/usr/bin/env python3
"""Upload manuscript/chNN.md into GRSI chapter Google Docs (replace body).

Packt: manuscripts must already follow inline-URL-once rules.
Auth: kenhuangus gws profile.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GWS = Path(r"C:\Users\kenhu\AppData\Roaming\npm\node_modules\@googleworkspace\cli\bin\gws.exe")
os.environ["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(Path.home() / ".config/gws-profiles/kenhuangus")
os.environ["GOOGLE_WORKSPACE_CLI_ACCOUNT"] = "kenhuangus@gmail.com"


def gws(*args: str) -> dict:
    r = subprocess.run([str(GWS), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout or f"rc={r.returncode}")
    return json.loads(r.stdout or "{}")


def replace_body(doc_id: str, text: str) -> None:
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": doc_id}))
    end = doc["body"]["content"][-1]["endIndex"]
    reqs = []
    if end > 2:
        reqs.append({"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end - 1}}})
    # Docs API rejects some control chars; normalize
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Cap very large inserts: Docs API has request size limits; chunk if needed
    chunk = 40000
    if len(text) <= chunk:
        reqs.append({"insertText": {"location": {"index": 1}, "text": text}})
        gws(
            "docs",
            "documents",
            "batchUpdate",
            "--params",
            json.dumps({"documentId": doc_id}),
            "--json",
            json.dumps({"requests": reqs}),
        )
        return
    # First clear, then insert chunks from the end backward so indices stay stable... 
    # Simpler: clear once, then append chunks sequentially at growing end.
    gws(
        "docs",
        "documents",
        "batchUpdate",
        "--params",
        json.dumps({"documentId": doc_id}),
        "--json",
        json.dumps({"requests": reqs}),
    )
    idx = 1
    for i in range(0, len(text), chunk):
        part = text[i : i + chunk]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ch", type=int, nargs="*", help="Chapter numbers (default: all existing md)")
    args = ap.parse_args()
    ids = json.loads((ROOT / "docs" / "GDOC_IDS.json").read_text(encoding="utf-8"))
    chapters = {int(k): v for k, v in ids["chapters"].items()}
    wanted = args.ch or sorted(chapters)
    for n in wanted:
        md = ROOT / "manuscript" / f"ch{n:02d}.md"
        if not md.exists():
            print(f"SKIP ch{n}: missing {md}")
            continue
        text = md.read_text(encoding="utf-8")
        # Strip markdown heading markers lightly for Docs readability
        # Keep as-is; authors can style later. Prefixed note:
        header = (
            f"Chapter {n} manuscript draft (from manuscript/ch{n:02d}.md).\n"
            "Packt: inline URLs only; no References section; each URL once.\n\n"
        )
        print(f"Uploading ch{n} ({len(text)} chars) -> {chapters[n]}")
        replace_body(chapters[n], header + text)
        print(f"OK ch{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
