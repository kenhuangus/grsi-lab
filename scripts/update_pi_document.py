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

# Packt Brand Orange (#EB5928 / RGB 235, 89, 40)
PACKT_ORANGE_FG = {
    "color": {"rgbColor": {"red": 0.92156863, "green": 0.34901961, "blue": 0.15686275}}
}

SECTIONS = [
    {
        "header": "Title (50 chars with spaces)",
        "content": "Governed Recursive Self-Improvement",
    },
    {
        "header": "Subtitle (100 chars with spaces)",
        "content": "Design secure, governed, and verified recursive self-improvement for AI agents and models",
    },
    {
        "header": "PacktPub Meta Description / Hook (230 chars with spaces)",
        "content": "Implement secure, governed, and verified recursive self-improvement to build AI agents that evolve algorithms, prompts, memory, and model weights under sandboxed execution and cryptographic promotion gates.",
    },
    {
        "header": "Key Features (3 bullet points, each max 100 chars; 4th standard point included)",
        "bullets": [
            "Evolve algorithms, prompts, and code using evolutionary search and reflective optimization loops",
            "Adapt model weights and curate episodic memory while preventing catastrophic forgetting",
            "Enforce secure, governed, and verified RSI with container sandboxes and cryptographic ledgers",
            "Purchase of the print or Kindle book includes a free PDF eBook",
        ],
    },
    {
        "header": "Short Description (250 chars with spaces)",
        "content": "Build secure, governed, and verified recursive self-improvement (RSI) for AI agents. This guide delivers verified architectures to evolve prompts, code, memory, and model weights under sandbox isolation and cryptographic production controls.",
    },
    {
        "header": "Long Description (1350 chars with spaces)",
        "paragraphs": [
            "Recursive self-improvement (RSI) allows AI agents to optimize their prompts, code, memory, and model weights over time. Without explicit boundaries, runtime modifications introduce failure modes such as reward hacking, catastrophic forgetting, and behavioral drift. Governed Recursive Self-Improvement delivers an engineering framework for secure, governed, and verified RSI. You will construct architectures where candidate mutations across prompts, algorithms, weights, and orchestration are proposed, isolated in sandboxes, empirically evaluated, and verified before promotion.",
            "Written by Ken Huang, Adjunct Professor at the University of San Francisco and creator of the CSA MAESTRO framework, this book features five runnable lab implementations. You will build evolutionary algorithm search, LoRA model adaptation with anti-forgetting gates, token-efficient memory curation, and AST-level harness hot-reloading. To ensure secure and governed RSI, you will deploy isolated container sandboxes, cryptographic evaluation ledgers, and HMAC-signed promotion tokens.",
            "By the end of this book, you will have the architecture and code to build AI agents with secure, governed, and verified recursive self-improvement across algorithms, models, and orchestration.",
        ],
    },
    {
        "header": "What you will learn (6-8 bullet points, max 70 chars each)",
        "bullets": [
            "Build evolutionary code search engines that mutate algorithm logic",
            "Define JSON Schema contracts to bound mutable agent code and prompts",
            "Optimize prompts using reflective critique and genetic compile loops",
            "Adapt LoRA model weights while preventing catastrophic forgetting",
            "Curate episodic agent memory using token ROI and budget controls",
            "Hot-reload multi-agent harnesses with AST validation and rollback",
            "Isolate and verify RSI experiments in sandboxes with SHA-256 ledgers",
            "Enforce secure, governed promotion gates using HMAC validation tokens",
        ],
    },
    {
        "header": "Audience (600 characters with spaces)",
        "content": "This book is for AI engineers, machine learning systems architects, agentic workflow developers, and technical leaders who build secure, governed, and verified RSI systems for AI agents. Software engineers designing adaptive LLM pipelines, prompt compilation workflows, or model fine-tuning harnesses will find concrete architectures. Readers should have intermediate Python proficiency and familiarity with large language model APIs, modern agent frameworks, and software testing concepts.",
    },
    {
        "header": "Approach (400 chars with spaces)",
        "content": "This book uses a contract-driven engineering curriculum centered on five runnable lab implementations. You learn by defining immutable schema contracts, building evolutionary proposal loops, fine-tuning model adapters, and isolating execution in container sandboxes. Each chapter pairs architectural taxonomy with deterministic test suites to implement secure, governed, and verified RSI.",
    },
    {
        "header": "Author Bio (750 chars with spaces)",
        "content": "Ken Huang is an Adjunct Professor at the University of San Francisco and co-chair of the Cloud Security Alliance (CSA) AI Safety Working Group, where he created the MAESTRO threat-modeling framework for agentic systems. He has authored books on AI engineering and distributed systems, and advises enterprises, government agencies, and research institutes on AI safety governance, secure agent systems, and governed RSI architectures. He also speaks and chairs sessions at technology conferences.",
    },
]

def build_document_text_and_styles():
    """Build full plain text and calculate ranges for headers and content."""
    full_text = "Product Information — Governed Recursive Self-Improvement\n\n"
    styles = []  # list of (start, end, style_dict)

    # Document Title style
    doc_title_text = "Product Information — Governed Recursive Self-Improvement\n"
    styles.append({
        "start": 1,
        "end": 1 + len(doc_title_text),
        "type": "DOC_TITLE"
    })

    current_idx = 1 + len(full_text)

    for i, section in enumerate(SECTIONS):
        is_last_section = (i == len(SECTIONS) - 1)
        hdr = section["header"] + "\n"
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
            body = section["content"] + ("\n" if is_last_section else "\n\n")
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
            num_p = len(section["paragraphs"])
            for p_idx, p in enumerate(section["paragraphs"]):
                is_last_p = (p_idx == num_p - 1)
                p_text = p + ("\n" if (is_last_section and is_last_p) else "\n\n")
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
            if not is_last_section:
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
                "spaceBelow": {"magnitude": 2, "unit": "PT"},
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
                        "foregroundColor": PACKT_ORANGE_FG,
                    },
                    "fields": "weightedFontFamily,fontSize,foregroundColor",
                }
            })
            format_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": st, "endIndex": en},
                    "paragraphStyle": {
                        "spaceAbove": {"magnitude": 6, "unit": "PT"},
                        "spaceBelow": {"magnitude": 4, "unit": "PT"},
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
                        "foregroundColor": PACKT_ORANGE_FG,
                    },
                    "fields": "weightedFontFamily,fontSize,foregroundColor",
                }
            })
            format_requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": st, "endIndex": en},
                    "paragraphStyle": {
                        "spaceAbove": {"magnitude": 8, "unit": "PT"},
                        "spaceBelow": {"magnitude": 2, "unit": "PT"},
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
