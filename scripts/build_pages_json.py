#!/usr/bin/env python3
"""Build pages.json for the web reader from OCR page files and story graph."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PAGE_FILE_RE = re.compile(r"^(\d+)-CoT\.txt$")
EDGE_RE = re.compile(r"\bP(\d+)\s*-->\s*P(\d+)\b")

# Match choice blocks like:
#   If you decide to start back home,
#   tum to page 4.
CHOICE_BLOCK_RE = re.compile(
    r"(If\s+[^\n]{3,120}?)[,.]?\s*\n\s*(?:tum|turn|go|return|follow|take)\s+to\s+page\s+(\d+)",
    re.IGNORECASE,
)

# Fallback: bare "turn to page N" with no preceding If-line
BARE_TURN_RE = re.compile(
    r"(?:tum|turn|go)\s+to\s+page\s+(\d+)",
    re.IGNORECASE,
)

TERMINAL_PHRASES = re.compile(r"\bthe\s+end\b", re.IGNORECASE)

OCR_FIXES = {
    "tum": "turn",
    "Tum": "Turn",
    "poge": "page",
}


def fix_ocr(text: str) -> str:
    for bad, good in OCR_FIXES.items():
        text = text.replace(bad, good)
    return text


def parse_graph_edges(graph_path: Path) -> Dict[int, List[int]]:
    edges: Dict[int, List[int]] = {}
    for line in graph_path.read_text(encoding="utf-8").splitlines():
        m = EDGE_RE.search(line)
        if m:
            src, dst = int(m.group(1)), int(m.group(2))
            edges.setdefault(src, [])
            if dst not in edges[src]:
                edges[src].append(dst)
    return edges


def extract_choices(text: str, graph_targets: List[int]) -> List[dict]:
    """Extract labelled choices from page text. Fall back to graph edges."""
    choices: List[dict] = []
    seen_pages: List[int] = []

    for m in CHOICE_BLOCK_RE.finditer(text):
        label = m.group(1).strip().rstrip(",.")
        # Clean up hyphenated line-breaks in label
        label = re.sub(r"-\s*\n\s*", "", label)
        label = re.sub(r"\s+", " ", label).strip()
        page = int(m.group(2))
        if page not in seen_pages:
            choices.append({"label": label, "page": page})
            seen_pages.append(page)

    # If we found labelled choices, we're done.
    if choices:
        return choices

    # Fallback: bare "turn to page N" mentions
    for m in BARE_TURN_RE.finditer(text):
        page = int(m.group(1))
        if page not in seen_pages:
            choices.append({"label": f"Turn to page {page}", "page": page})
            seen_pages.append(page)

    if choices:
        return choices

    # Last resort: use graph edges (sequential continuation pages)
    for page in graph_targets:
        if page not in seen_pages:
            choices.append({"label": f"Continue to page {page}", "page": page})
            seen_pages.append(page)

    return choices


def clean_text(raw: str, page_num: int) -> str:
    """Remove page header line and OCR artifacts."""
    lines = raw.splitlines()
    # Strip leading "Page N" header
    cleaned = []
    skip_next_blank = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and re.fullmatch(r"Page\s+\d+", stripped):
            skip_next_blank = True
            continue
        if skip_next_blank and stripped == "":
            skip_next_blank = False
            continue
        skip_next_blank = False
        cleaned.append(line)

    text = "\n".join(cleaned).strip()
    text = fix_ocr(text)
    return text


def build_pages(pages_dir: Path, graph_path: Optional[Path]) -> Dict[str, dict]:
    graph_edges: Dict[int, List[int]] = {}
    if graph_path and graph_path.exists():
        graph_edges = parse_graph_edges(graph_path)

    pages: Dict[str, dict] = {}

    for path in sorted(pages_dir.glob("*-CoT.txt")):
        m = PAGE_FILE_RE.match(path.name)
        if not m:
            continue
        page_num = int(m.group(1))
        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = clean_text(raw, page_num)

        graph_targets = graph_edges.get(page_num, [])
        choices = extract_choices(text, graph_targets)
        is_terminal = bool(TERMINAL_PHRASES.search(text)) or (not choices and not graph_targets)

        pages[str(page_num)] = {
            "page": page_num,
            "text": text,
            "choices": choices,
            "is_terminal": is_terminal,
        }

    return pages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build pages.json for the web reader.")
    parser.add_argument("--pages-dir", type=Path, default=Path("output/cot-pages-ocr-v2"))
    parser.add_argument("--graph", type=Path, default=Path("output/cot-story-graph.mmd"))
    parser.add_argument("--output", type=Path, default=Path("web/pages.json"))
    parser.add_argument("--start-page", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.pages_dir.exists():
        raise FileNotFoundError(f"Pages directory not found: {args.pages_dir}")

    pages = build_pages(args.pages_dir, args.graph)

    meta = {
        "start_page": args.start_page,
        "total_pages": len(pages),
        "page_numbers": sorted(int(k) for k in pages),
    }

    output = {"meta": meta, "pages": pages}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    terminal_count = sum(1 for p in pages.values() if p["is_terminal"])
    print(f"Pages processed: {len(pages)}")
    print(f"Terminal pages:  {terminal_count}")
    print(f"Output:          {args.output}")


if __name__ == "__main__":
    main()
