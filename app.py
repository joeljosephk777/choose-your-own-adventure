#!/usr/bin/env python3
"""Flask backend for the Cave of Time web app.

Serves the static reader/graph/author pages and exposes CRUD endpoints for
page data plus a graph rebuild route for the current story draft.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
OUTPUT_DIR = ROOT / "output"
PAGES_JSON_PATH = WEB_DIR / "pages.json"
GRAPH_PATH = OUTPUT_DIR / "cot-story-graph.mmd"
BEGINNINGS_PATH = ROOT / "story_beginnings.txt"
WEB_BEGINNINGS_PATH = WEB_DIR / "story_beginnings.txt"


app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # disable static file caching


@app.after_request
def no_cache(response):
    if request.path.endswith((".html", ".js", ".json", ".css", ".txt")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


def _numeric_keys(mapping: dict) -> list[int]:
    numbers = []
    for key in mapping:
        try:
            numbers.append(int(key))
        except (TypeError, ValueError):
            continue
    return sorted(numbers)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {"meta": {"start_page": 2, "total_pages": 0, "page_numbers": []}, "pages": {}}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON in {path}")
    return data


def _normalize_choice(choice: dict) -> dict | None:
    if not isinstance(choice, dict):
        return None
    try:
        page = int(choice.get("page"))
    except (TypeError, ValueError):
        return None
    if page <= 0:
        return None
    label = str(choice.get("label", "")).strip() or f"Turn to page {page}"
    return {"label": label, "page": page}


def _normalize_page(page_num: int, page: dict) -> dict:
    raw_choices = page.get("choices", []) if isinstance(page, dict) else []
    choices = []
    for choice in raw_choices:
        normalized = _normalize_choice(choice)
        if normalized is not None and normalized["page"] not in [c["page"] for c in choices]:
            choices.append(normalized)

    terminal = page.get("is_terminal")
    if terminal is None:
        terminal = len(choices) == 0

    return {
        "page": page_num,
        "text": str(page.get("text", "")).strip(),
        "choices": choices,
        "is_terminal": bool(terminal),
        "is_story_beginning": bool(page.get("is_story_beginning", False)),
    }


def _normalize_payload(data: dict) -> dict:
    pages_in = data.get("pages", {}) if isinstance(data, dict) else {}
    normalized_pages = {}

    for key in sorted(pages_in, key=lambda value: int(value) if str(value).isdigit() else 10**9):
        try:
            page_num = int(key)
        except (TypeError, ValueError):
            continue
        if page_num <= 0:
            continue
        normalized_pages[str(page_num)] = _normalize_page(page_num, pages_in[key])

    meta_in = data.get("meta", {}) if isinstance(data, dict) else {}
    try:
        start_page = int(meta_in.get("start_page", 2))
    except (TypeError, ValueError):
        start_page = 2

    return {
        "meta": {
            "start_page": start_page,
            "total_pages": len(normalized_pages),
            "page_numbers": _numeric_keys(normalized_pages),
        },
        "pages": normalized_pages,
    }


def _save_payload(payload: dict) -> dict:
    normalized = _normalize_payload(payload)
    PAGES_JSON_PATH.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
    _sync_story_beginnings(normalized)
    return normalized


def _sync_story_beginnings(payload: dict) -> None:
    beginning_pages = sorted(
        page["page"]
        for page in payload.get("pages", {}).values()
        if page.get("is_story_beginning")
    )
    content = "\n".join(str(page_num) for page_num in beginning_pages)
    BEGINNINGS_PATH.write_text(content, encoding="utf-8")
    WEB_BEGINNINGS_PATH.write_text(content, encoding="utf-8")


def _page_numbers(payload: dict) -> list[int]:
    return _numeric_keys(payload.get("pages", {}))


def _build_graph_data(payload: dict) -> dict:
    pages = payload.get("pages", {})
    nodes = {}
    edges = []

    for key in sorted(pages, key=lambda value: int(value) if str(value).isdigit() else 10**9):
        page = pages[key]
        page_num = int(key)
        nodes[page_num] = {
            "id": page_num,
            "label": str(page_num),
            "page": page_num,
            "is_terminal": bool(page.get("is_terminal", False)),
            "is_story_beginning": bool(page.get("is_story_beginning", False)),
            "missing": False,
        }

    for key in sorted(pages, key=lambda value: int(value) if str(value).isdigit() else 10**9):
        page = pages[key]
        src = int(key)
        for choice in page.get("choices", []):
            dst = int(choice["page"])
            if dst not in nodes:
                nodes[dst] = {
                    "id": dst,
                    "label": str(dst),
                    "page": dst,
                    "is_terminal": False,
                    "is_story_beginning": False,
                    "missing": True,
                }
            edges.append(
                {
                    "source": src,
                    "target": dst,
                    "label": choice["label"],
                    "target_exists": str(dst) in pages,
                }
            )

    return {
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": edges,
    }


def _build_mermaid_graph(payload: dict) -> str:
    graph = _build_graph_data(payload)
    lines = ["graph TD"]

    for node in graph["nodes"]:
        lines.append(f'  P{node["id"]}["{node["label"]}"]')

    for edge in graph["edges"]:
        lines.append(f'  P{edge["source"]} --> P{edge["target"]}')

    return "\n".join(lines) + "\n"


def _rebuild_graph_file(payload: dict) -> dict:
    graph_text = _build_mermaid_graph(payload)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_PATH.write_text(graph_text, encoding="utf-8")
    graph = _build_graph_data(payload)
    return {
        "graph_path": str(GRAPH_PATH.relative_to(ROOT)),
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
    }


def _get_payload() -> dict:
    return _normalize_payload(_read_json(PAGES_JSON_PATH))


def _store_page(page_num: int, page: dict, allow_create: bool = True) -> tuple[dict, bool]:
    payload = _get_payload()
    pages = payload["pages"]
    key = str(page_num)
    existed = key in pages
    if not existed and not allow_create:
        abort(404, description=f"Page {page_num} not found")

    pages[key] = _normalize_page(page_num, page)
    payload["meta"]["page_numbers"] = _page_numbers(payload)
    payload["meta"]["total_pages"] = len(pages)
    _save_payload(payload)
    return payload, existed


@app.get("/")
def root() -> str:
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/story_beginnings.txt")
def story_beginnings() -> object:
    if WEB_BEGINNINGS_PATH.exists():
        return send_file(WEB_BEGINNINGS_PATH, mimetype="text/plain")
    if BEGINNINGS_PATH.exists():
        return send_file(BEGINNINGS_PATH, mimetype="text/plain")
    abort(404)


@app.get("/pages")
def list_pages() -> object:
    payload = _get_payload()
    return jsonify({"pages": _page_numbers(payload), "total": len(payload["pages"])})


@app.get("/pages/<int:page_num>")
def get_page(page_num: int) -> object:
    payload = _get_payload()
    page = payload["pages"].get(str(page_num))
    if not page:
        abort(404, description=f"Page {page_num} not found")
    return jsonify(page)


@app.post("/pages")
def create_page() -> object:
    body = request.get_json(silent=True) or {}
    try:
        page_num = int(body.get("page"))
    except (TypeError, ValueError):
        abort(400, description="Request body must include a numeric page field")

    payload = _get_payload()
    if str(page_num) in payload["pages"]:
        abort(409, description=f"Page {page_num} already exists")

    payload["pages"][str(page_num)] = _normalize_page(page_num, body)
    payload["meta"]["page_numbers"] = _page_numbers(payload)
    payload["meta"]["total_pages"] = len(payload["pages"])
    _save_payload(payload)
    return jsonify(payload["pages"][str(page_num)]), 201


@app.put("/pages/<int:page_num>")
def update_page(page_num: int) -> object:
    body = request.get_json(silent=True) or {}
    body["page"] = page_num
    payload, existed = _store_page(page_num, body, allow_create=True)
    return jsonify(payload["pages"][str(page_num)]), 200 if existed else 201


@app.delete("/pages/<int:page_num>")
def delete_page(page_num: int) -> object:
    payload = _get_payload()
    key = str(page_num)
    if key not in payload["pages"]:
        abort(404, description=f"Page {page_num} not found")

    del payload["pages"][key]
    for page in payload["pages"].values():
        page["choices"] = [choice for choice in page.get("choices", []) if int(choice["page"]) != page_num]
    payload["meta"]["page_numbers"] = _page_numbers(payload)
    payload["meta"]["total_pages"] = len(payload["pages"])
    _save_payload(payload)
    return jsonify({"deleted": page_num})


@app.get("/graph")
def get_graph() -> object:
    payload = _get_payload()
    graph = _build_graph_data(payload)
    return jsonify(
        {
            "meta": payload["meta"],
            "nodes": graph["nodes"],
            "edges": graph["edges"],
        }
    )


@app.post("/graph/rebuild")
def rebuild_graph() -> object:
    payload = _get_payload()
    summary = _rebuild_graph_file(payload)
    summary["status"] = "rebuilt"
    return jsonify(summary)


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "bad_request", "message": getattr(error, "description", "Bad request")}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "not_found", "message": getattr(error, "description", "Not found")}), 404


@app.errorhandler(409)
def conflict(error):
    return jsonify({"error": "conflict", "message": getattr(error, "description", "Conflict")}), 409


def main() -> None:
    if not WEB_DIR.exists():
        raise FileNotFoundError(f"Web directory not found: {WEB_DIR}")

    payload = _get_payload()
    _sync_story_beginnings(payload)

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") not in {"0", "false", "False"}

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()