#!/usr/bin/env python3
"""Sync Packt named styles from template Doc onto all GRSI chapter Docs."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gws_env import configure_gws_env  # noqa: E402

GWS = configure_gws_env()
TEMPLATE = "1VkUK66uM_JZnEs25q-CtGerdrsco16bMG3a9xdpXO7g"

# Explicit Packt values (from template) — do not invent
PACKT = {
    "NORMAL_TEXT": {
        "textStyle": {
            "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 400},
            "fontSize": {"magnitude": 10.5, "unit": "PT"},
            "bold": False,
            "foregroundColor": {
                "color": {"rgbColor": {"red": 0.06666667, "green": 0.09411765, "blue": 0.15294118}}
            },
        },
        "paragraphStyle": {
            "namedStyleType": "NORMAL_TEXT",
            "lineSpacing": 115,
            "spaceBelow": {"magnitude": 10, "unit": "PT"},
            "alignment": "START",
        },
    },
    "HEADING_1": {
        "textStyle": {
            "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
            "fontSize": {"magnitude": 16, "unit": "PT"},
            "bold": True,
            "foregroundColor": {
                "color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}
            },
        },
        "paragraphStyle": {
            "namedStyleType": "HEADING_1",
            "spaceAbove": {"magnitude": 24, "unit": "PT"},
        },
    },
    "HEADING_2": {
        "textStyle": {
            "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
            "fontSize": {"magnitude": 14, "unit": "PT"},
            "bold": True,
            "foregroundColor": {
                "color": {"rgbColor": {"red": 0.12156863, "green": 0.30588236, "blue": 0.4745098}}
            },
        },
        "paragraphStyle": {
            "namedStyleType": "HEADING_2",
            "spaceAbove": {"magnitude": 10, "unit": "PT"},
        },
    },
    "HEADING_3": {
        "textStyle": {
            "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
            "fontSize": {"magnitude": 12, "unit": "PT"},
            "bold": True,
            "foregroundColor": {
                "color": {"rgbColor": {"red": 0.18039216, "green": 0.45882353, "blue": 0.7137255}}
            },
        },
        "paragraphStyle": {
            "namedStyleType": "HEADING_3",
            "spaceAbove": {"magnitude": 10, "unit": "PT"},
        },
    },
}


def gws(*args: str) -> dict:
    r = subprocess.run([str(GWS), *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or b"").decode("utf-8", "replace"))
    return json.loads(r.stdout.decode("utf-8"))


def sync_doc(doc_id: str) -> None:
    reqs = []
    for named, spec in PACKT.items():
        # paragraphStyle for named styles must NOT nest namedStyleType
        ps = {k: v for k, v in spec["paragraphStyle"].items() if k != "namedStyleType"}
        reqs.append(
            {
                "updateNamedStyle": {
                    "namedStyle": {
                        "namedStyleType": named,
                        "textStyle": spec["textStyle"],
                        "paragraphStyle": ps,
                    },
                    "fields": "textStyle,paragraphStyle",
                }
            }
        )
    # Page margins match template
    reqs.append(
        {
            "updateDocumentStyle": {
                "documentStyle": {
                    "marginTop": {"magnitude": 72, "unit": "PT"},
                    "marginBottom": {"magnitude": 72, "unit": "PT"},
                    "marginLeft": {"magnitude": 72, "unit": "PT"},
                    "marginRight": {"magnitude": 72, "unit": "PT"},
                },
                "fields": "marginTop,marginBottom,marginLeft,marginRight",
            }
        }
    )
    gws(
        "docs",
        "documents",
        "batchUpdate",
        "--params",
        json.dumps({"documentId": doc_id}),
        "--json",
        json.dumps({"requests": reqs}),
    )


def main() -> int:
    ids = json.loads((ROOT / "docs" / "GDOC_IDS.json").read_text(encoding="utf-8"))
    targets = [ids["toc"], *ids["chapters"].values()]
    for doc_id in targets:
        print("sync", doc_id)
        try:
            sync_doc(doc_id)
            print("  OK")
        except Exception as e:
            print("  FAIL", e)
            return 1
    print("Synced Packt named styles from template", TEMPLATE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
