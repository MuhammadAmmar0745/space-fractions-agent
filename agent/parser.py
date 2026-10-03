"""
parser.py
---------
Ye module do input files parhta hai:
  1. Architecture_Documentation.md  -> requirements, components, tech stack, API contracts, schema
  2. Architecture_View.md           -> PlantUML diagrams (use-case, class, sequence, etc.)

Aur inhe ek structured JSON mein convert karta hai, jo humara "Code Agent"
ke liye asaan / machine-readable input hoga (jaisa task ne suggest kiya hai).

Ye simple regex/markdown-section based parser hai - koi heavy NLP nahi,
kyunke input file ka format consistent (headings + code blocks) hai.
"""

import re
import json
from pathlib import Path


def _extract_code_blocks(text: str):
    """Har fenced code block (```lang ... ```) ko (language, content) tuple ke tor par nikalta hai."""
    pattern = r"```(\w*)\n(.*?)```"
    return [(lang or "text", content.strip()) for lang, content in re.findall(pattern, text, re.DOTALL)]


def _split_by_headings(text: str, level=1):
    """Markdown ko '# Heading' (level 1) ya '## Heading' (level 2) ke hisaab se sections mein todta hai."""
    marker = "#" * level
    pattern = rf"(?m)^{marker} (.+)$"
    parts = re.split(pattern, text)
    # parts[0] = heading se pehle ka text, phir (heading, body) pairs
    sections = {}
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections[heading] = body.strip()
    return sections


def parse_architecture_documentation(md_text: str) -> dict:
    """Architecture_Documentation.md ko structured dict mein parse karta hai."""
    sections = _split_by_headings(md_text, level=1)
    result = {
        "raw_sections": list(sections.keys()),
        "executive_summary": None,
        "architectural_style": None,
        "components": [],
        "api_contracts": {"openapi": None, "internal_proto": None},
        "data_schemas": [],
        "deployment": {"kubernetes_yaml": None},
        "traceability_matrix_csv": None,
    }

    # A. Executive Summary
    exec_summary = sections.get("A. Executive Summary", "")
    result["executive_summary"] = exec_summary.split("\n")[0] if exec_summary else None
    style_match = re.search(r"Chosen architectural style:\s*(.+)", exec_summary)
    if style_match:
        result["architectural_style"] = style_match.group(1).strip()

    # C. Architecture Overview -> component list (bullet points "* Name: description")
    overview = sections.get("C. Architecture Overview", "")
    for m in re.finditer(r"\*\s*(\w+):\s*(.+)", overview):
        result["components"].append({"name": m.group(1), "responsibility": m.group(2).strip()})

    # D. Detailed Technical Design -> code blocks contain openapi / proto / sql
    detailed = sections.get("D. Detailed Technical Design", "")
    for lang, content in _extract_code_blocks(detailed):
        if lang in ("yml", "yaml") and "openapi" in content:
            result["api_contracts"]["openapi"] = content
        elif lang == "proto":
            result["api_contracts"]["internal_proto"] = content
        elif lang == "sql":
            result["data_schemas"].append(content)

    # E. Operations & Deployment -> k8s yaml
    ops = sections.get("E. Operations & Deployment", "")
    for lang, content in _extract_code_blocks(ops):
        if lang in ("yml", "yaml"):
            result["deployment"]["kubernetes_yaml"] = content

    # L. Deliverables -> traceability CSV
    deliverables = sections.get("L. Deliverables", "")
    for lang, content in _extract_code_blocks(deliverables):
        if lang == "csv":
            result["traceability_matrix_csv"] = content

    return result


def parse_architecture_view(md_text: str) -> dict:
    """Architecture_View.md se saare PlantUML diagrams nikalta hai, view (Scenario/Logic/...) ke hisaab se group karke."""
    views = _split_by_headings(md_text, level=2)
    result = {}
    for view_name, body in views.items():
        diagrams = []
        for lang, content in _extract_code_blocks(body):
            if lang == "plantuml":
                name_match = re.search(r"@startuml\s+(\w+)", content)
                diagrams.append({
                    "name": name_match.group(1) if name_match else "Unnamed",
                    "plantuml": content,
                })
        result[view_name] = diagrams
    return result


def build_agent_input_json(doc_md_path: str, view_md_path: str, out_json_path: str) -> dict:
    """Dono files parse kar ke ek combined JSON file save karta hai. Yehi Code Agent ka input hoga."""
    doc_text = Path(doc_md_path).read_text(encoding="utf-8")
    view_text = Path(view_md_path).read_text(encoding="utf-8")

    combined = {
        "architecture_documentation": parse_architecture_documentation(doc_text),
        "architecture_views": parse_architecture_view(view_text),
    }

    Path(out_json_path).write_text(json.dumps(combined, indent=2), encoding="utf-8")
    return combined


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Parse architecture docs into a single JSON input for the Code Agent.")
    ap.add_argument("--doc", default="Architecture_Documentation.md")
    ap.add_argument("--view", default="Architecture_View.md")
    ap.add_argument("--out", default="agent_input.json")
    args = ap.parse_args()

    data = build_agent_input_json(args.doc, args.view, args.out)
    print(f"[parser] Saved structured input -> {args.out}")
    print(f"[parser] Components found: {[c['name'] for c in data['architecture_documentation']['components']]}")
    print(f"[parser] Views found: {list(data['architecture_views'].keys())}")
