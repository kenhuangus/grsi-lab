"""
Update Product Information (PI) Google Doc for:
Governed Recursive Self-Improvement: Bounded Self-Evolution of Agent Harnesses

Document ID: 1M29Em3yqS7fO-f3qxKZvEEYW7bQuab21UDeXPO-wa-E
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_chapter_to_gdoc import gws, gws_batch

DOC_ID = "1M29Em3yqS7fO-f3qxKZvEEYW7bQuab21UDeXPO-wa-E"

SECTIONS = [
    {
        "header": "Title (50 chars with spaces)",
        "content": "Governed Recursive Self-Improvement",
    },
    {
        "header": "Subtitle (100 chars with spaces)",
        "content": "Architect safe autonomous AI agents with bounded self-evolution and sandboxed verification",
    },
    {
        "header": "PacktPub Meta Description / Hook (230 chars with spaces)",
        "content": "Build production-ready autonomous agent systems that safely evolve prompts, code, and weights under strict cryptographic ledgers and automated rollback gates.",
    },
    {
        "header": "Key Features (3 bullet points, each max 100 chars; 4th standard point included)",
        "bullets": [
            "Implement tamper-proof cryptographic ledgers and HMAC tokens to verify every agent mutation",
            "Prevent catastrophic forgetting with automated threshold gates across adapters and memory stores",
            "Deploy isolated container sandboxes that block unauthorized network egress and file tampering",
            "Purchase of the print or Kindle book includes a free PDF eBook",
        ],
    },
    {
        "header": "Short Description (250 chars with spaces)",
        "content": "Autonomous agents that modify their own code risk catastrophic misalignment without rigorous controls. This guide delivers verified architectural patterns, sandbox isolation, and cryptographic governance to build secure self-improving AI systems.",
    },
    {
        "header": "Long Description (1350 chars with spaces)",
        "paragraphs": [
            "Autonomous AI agents that modify their own prompts, tools, or weights can rapidly degrade, overfit, or bypass safety constraints without strict boundaries. Governed Recursive Self-Improvement solves this challenge by establishing an engineering discipline for bounded self-evolution. Rather than relying on unconstrained loops, you will construct a hardened architecture where every mutation is proposed, isolated, evaluated against held-out benchmarks, and verified before deployment.",
            "Written by Ken Huang, Adjunct Professor at the University of San Francisco and creator of the CSA MAESTRO framework, this book provides five production-ready lab implementations. You will build schema-enforced proposal engines, anti-forgetting gates for LoRA adapters, AST-level harness hot-reloading with per-module rollback, and bubblewrap container sandboxes with default-deny network egress. You will also implement append-only cryptographic evaluation ledgers and HMAC-signed promotion tokens.",
            "By the end of this book, you will possess the architectural frameworks and code to build autonomous agent harnesses that reliably self-improve while maintaining complete operational safety, auditability, and human oversight.",
        ],
    },
    {
        "header": "What you will learn (6-8 bullet points, max 70 chars each)",
        "bullets": [
            "Enforce file boundaries using JSON Schema ownership manifests",
            "Build proposal engines that validate code diffs before execution",
            "Block model forgetting using LoRA adapter threshold evaluation gates",
            "Quarantine unverified experience data using token budget controls",
            "Hot-reload agent skills with AST validation and per-module rollbacks",
            "Isolate agent workers in Linux sandboxes with strict network jails",
            "Record tamper-evident evaluation decisions using SHA-256 hash chains",
            "Require HMAC tokens before promoting mutated agents to production",
        ],
    },
    {
        "header": "Audience (600 characters with spaces)",
        "content": "This book is for AI engineers, machine learning systems architects, agentic workflow developers, and security practitioners who want to build autonomous systems that self-improve safely. Engineering leaders deploying autonomous coding or research agents in production environments will also find this guide essential for governance. Readers should have intermediate Python proficiency and familiarity with large language model APIs, modern agent frameworks, and fundamental software testing concepts.",
    },
    {
        "header": "Approach (400 chars with spaces)",
        "content": "This book uses a contract-driven engineering curriculum centered on five runnable lab implementations. You learn by defining immutable schema contracts, configuring isolated execution sandboxes, running automated failure injection drills, and verifying cryptographic audit trails. Each chapter pairs architectural taxonomy with deterministic test suites that validate system behavior.",
    },
    {
        "header": "Author Bio (750 chars with spaces)",
        "content": "Ken Huang is an internationally recognized expert in artificial intelligence and cybersecurity. He is an Adjunct Professor at the University of San Francisco and co-chair of the Cloud Security Alliance (CSA) AI Safety Working Group, where he created the MAESTRO threat-modeling framework for agentic systems. Ken has authored multiple acclaimed books on AI engineering and distributed systems. He regularly advises Fortune 500 enterprises, government agencies, and research institutes on AI safety governance and autonomous agent security. He also serves as a keynote speaker and conference chair across global technology summits.",
    },
]

def build_document_text_and_styles():
    """Build full plain text and calculate ranges for headers and content."""
    full_text = "Product Information — Governed Recursive Self-Improvement\n\n"
    styles = [] # list of (start, end, style_dict)

    # Document Title style
    styles.append({
        "start": 1,
        "end": len(full_text),
        "type": "DOC_TITLE"
    })

    current_idx = 1 + len(full_text)

    for section in SECTIONS:
        hdr = section["header"] + "\n\n"
        hdr_start = current_idx
        hdr_end = current_idx + len(hdr)
        full_text += hdr
        styles.append({
            "start": hdr_start,
            "end": hdr_end,
            "type": "SECTION_HEADER"
        })
        current_idx = hdr_end

        if "content" in section:
            body = section["content"] + "\n\n"
            body_start = current_idx
            body_end = current_idx + len(body)
            full_text += body
            styles.append({
                "start": body_start,
                "end": body_end,
                "type": "BODY_TEXT"
            })
            current_idx = body_end
        elif "paragraphs" in section:
            for p in section["paragraphs"]:
                p_text = p + "\n\n"
                p_start = current_idx
                p_end = current_idx + len(p_text)
                full_text += p_text
                styles.append({
                    "start": p_start,
                    "end": p_end,
                    "type": "BODY_TEXT"
                })
                current_idx = p_end
        elif "bullets" in section:
            for b in section["bullets"]:
                b_text = "• " + b + "\n"
                b_start = current_idx
                b_end = current_idx + len(b_text)
                full_text += b_text
                styles.append({
                    "start": b_start,
                    "end": b_end,
                    "type": "BULLET_TEXT"
                })
                current_idx = b_end
            full_text += "\n"
            current_idx += 1

    return full_text, styles

def main():
    print(f"Fetching current document {DOC_ID}...")
    doc = gws("docs", "documents", "get", "--params", json.dumps({"documentId": DOC_ID}))
    body_content = doc.get("body", {}).get("content", [])
    end_idx = body_content[-1]["endIndex"] if body_content else 1

    if end_idx > 2:
        print(f"Clearing old content (range 1 to {end_idx - 1})...")
        gws_batch(DOC_ID, [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_idx - 1}}}])

    full_text, styles = build_document_text_and_styles()
    print(f"Inserting new PI text ({len(full_text)} chars)...")
    gws_batch(DOC_ID, [{"insertText": {"location": {"index": 1}, "text": full_text}}])

    # Now apply formatting:
    print("Applying typography and styling...")
    format_requests = []

    # Default styling for whole document (Crimson Pro 10.5pt, line spacing 115)
    doc_after = gws("docs", "documents", "get", "--params", json.dumps({"documentId": DOC_ID}))
    doc_end = doc_after.get("body", {}).get("content", [])[-1]["endIndex"]

    format_requests.append({
        "updateTextStyle": {
            "range": {"startIndex": 1, "endIndex": doc_end - 1},
            "textStyle": {
                "weightedFontFamily": {"fontFamily": "Crimson Pro", "weight": 400},
                "fontSize": {"magnitude": 10.5, "unit": "PT"},
                "foregroundColor": {"color": {"rgbColor": {"red": 0.067, "green": 0.094, "blue": 0.153}}},
            },
            "fields": "weightedFontFamily,fontSize,foregroundColor",
        }
    })

    # Paragraph style for entire document
    format_requests.append({
        "updateParagraphStyle": {
            "range": {"startIndex": 1, "endIndex": doc_end - 1},
            "paragraphStyle": {
                "lineSpacing": 115,
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "lineSpacing,spaceBelow",
        }
    })

    # Style individual elements
    for s in styles:
        s_type = s["type"]
        st = s["start"]
        en = min(s["end"], doc_end - 1)
        if st >= en:
            continue

        if s_type == "DOC_TITLE":
            format_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": st, "endIndex": en},
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
                        "fontSize": {"magnitude": 20, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.122, "green": 0.306, "blue": 0.475}}},
                    },
                    "fields": "weightedFontFamily,fontSize,foregroundColor",
                }
            })
            format_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": st, "endIndex": en},
                    "paragraphStyle": {
                        "spaceAbove": {"magnitude": 12, "unit": "PT"},
                        "spaceBelow": {"magnitude": 16, "unit": "PT"},
                    },
                    "fields": "spaceAbove,spaceBelow",
                }
            })
        elif s_type == "SECTION_HEADER":
            format_requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": st, "endIndex": en},
                    "textStyle": {
                        "weightedFontFamily": {"fontFamily": "Jost", "weight": 700},
                        "fontSize": {"magnitude": 13, "unit": "PT"},
                        "foregroundColor": {"color": {"rgbColor": {"red": 0.122, "green": 0.306, "blue": 0.475}}},
                    },
                    "fields": "weightedFontFamily,fontSize,foregroundColor",
                }
            })
            format_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": st, "endIndex": en},
                    "paragraphStyle": {
                        "spaceAbove": {"magnitude": 14, "unit": "PT"},
                        "spaceBelow": {"magnitude": 4, "unit": "PT"},
                    },
                    "fields": "spaceAbove,spaceBelow",
                }
            })

    # Batch execute styling in chunks
    chunk_size = 15
    for i in range(0, len(format_requests), chunk_size):
        gws_batch(DOC_ID, format_requests[i:i + chunk_size])

    print("Successfully updated PI document!")

if __name__ == "__main__":
    main()
