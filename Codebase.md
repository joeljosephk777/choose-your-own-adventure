# Codebase Notes — Cave of Time (CSS 382)

## Project Overview

This project takes a scanned PDF of *Choose Your Own Adventure: The Cave of Time* and turns it into a fully interactive web application. There are two main layers:

1. **Data pipeline** — Python scripts that OCR the PDF, extract page text, parse story graph edges, and generate JSON for the web app.
2. **Web application** — A Flask-served three-page app: an interactive reader, a live authoring tool with graph visualization, and a journey graph viewer.

---

## Project Architecture

```
choose-your-own-adventure/
├── app.py                        ← Flask backend (API + static serving)
├── requirements.txt
├── todo.md                       ← Task tracking
├── brainstorm.md                 ← Feature ideas
├── samples/
│   └── the-cave-of-time.pdf      ← Source scanned PDF (input)
├── scripts/                      ← Data pipeline scripts
│   ├── reextract_cot_ocr_split.py
│   ├── build_story_graph.py
│   ├── build_pages_json.py       ← Main pipeline entry point for web app
│   ├── write_all_stories.py
│   └── render_story_graph_svg.py
├── output/                       ← All generated outputs
│   ├── cot-pages-ocr-v2/         ← Extracted page text files (canonical)
│   ├── cot-story-graph.mmd       ← Mermaid graph
│   ├── cot-story-graph.svg       ← Static SVG render
│   └── cot-stories/              ← 45 bounded story paths
├── web/                          ← All frontend files (served by Flask)
│   ├── index.html                ← Interactive reader
│   ├── graph.html                ← Journey graph viewer
│   ├── author.html               ← Authoring tool + live graph
│   ├── pages.json                ← Canonical page data (served as API source of truth)
│   └── story_beginnings.txt      ← List of story-beginning page numbers
└── session-logs/
    └── AI-session-logs.json      ← Full chat history across all sessions
```

---

## Data Pipeline (Python Scripts)

### 1. OCR Extraction — `reextract_cot_ocr_split.py`

The PDF is a two-page spread scan. Each PDF page contains two story pages side by side. This script:
- Splits each PDF page image into left and right halves
- Runs OCR (via pytesseract) on each half independently
- Maps PDF page numbers to story page numbers (PDF page 8 = story pages 2 & 3)
- Saves extracted text to `output/cot-pages-ocr-v2/NN-CoT.txt`

**Critical mapping:**
- Story begins on story page 2, which is on the left half of PDF page 8
- Formula: PDF page N → story pages `(N-8)*2+2` (left) and `(N-8)*2+3` (right)

```bash
python3 scripts/reextract_cot_ocr_split.py \
  --pdf samples/the-cave-of-time.pdf \
  --pdf-start-page 8 --pdf-end-page 66 \
  --story-start-page 2 \
  --output-dir output/cot-pages-ocr-v2
```

### 2. Story Graph — `build_story_graph.py`

Parses the extracted text files and builds a Mermaid-format directed graph:
- Reads "turn to page X" / "go to page X" patterns in page text
- Adds sequential continuation edges when a page continues to the next page without an explicit choice
- Output: `output/cot-story-graph.mmd`

```bash
python3 scripts/build_story_graph.py \
  --pages-dir output/cot-pages-ocr-v2 \
  --output output/cot-story-graph.mmd
```

### 3. Web Page JSON — `build_pages_json.py`

The main pipeline entry point for the web app. Converts extracted text files into a structured JSON format that all three web pages consume:
- Parses page text and choice destinations from `NN-CoT.txt` files
- Falls back to graph edges if no explicit choices are found in text
- Supports `--story-starts` flag for marking beginning pages
- Output: `web/pages.json`

```bash
python3 scripts/build_pages_json.py \
  --pages-dir output/cot-pages-ocr-v2 \
  --graph output/cot-story-graph.mmd \
  --output web/pages.json \
  --story-starts 2,22,56,90,97,100,117,119
```

### 4. Story Writer — `write_all_stories.py`

Traverses the graph and writes every possible bounded story path as a text file:
- Starts from story page 2
- Stops at terminal pages (no outgoing choices), on cycles, or after 20 decision points
- Generates 45 complete story variants in `output/cot-stories/`

### 5. SVG Renderer — `render_story_graph_svg.py`

Renders the Mermaid graph to a static SVG without external tools:
- Layered Sugiyama-style layout with iterative barycenter ordering
- Terminal pages colored red, main trunk from page 2 colored blue

---

## Web Application

The web app is served by Flask (`app.py`). All three pages load from `web/pages.json` as their data source.

### Data Format — `web/pages.json`

```json
{
  "meta": {
    "start_page": 2,
    "total_pages": 111,
    "page_numbers": [2, 3, 4, ...]
  },
  "pages": {
    "2": {
      "page": 2,
      "text": "You've hiked through Snake Canyon...",
      "choices": [
        { "label": "Turn to page 5", "page": 5 },
        { "label": "Turn to page 13", "page": 13 }
      ],
      "is_terminal": false,
      "is_story_beginning": true
    }
  }
}
```

**Terminal detection is structural:** a page is terminal when `choices.length === 0`, not when the `is_terminal` flag is set. The flag is stored but the UI always recalculates from choices.

### Story Beginnings — `web/story_beginnings.txt`

A plain text file with one page number per line. Lists all pages the author has marked as story entry points. The reader start menu is built exclusively from this file.

Current beginning pages: `2, 22, 56, 90, 97, 100, 117, 119`

---

### Page 1 — Interactive Reader (`web/index.html`)

**Purpose:** Let a reader navigate the story interactively.

**How it works:**
1. On load, fetches `pages.json` and merges with author's localStorage draft (author-marked dirty pages override baseline for those specific pages only — see `dirtyPageSet` below)
2. Fetches `story_beginnings.txt` to populate the start menu
3. Shows a start menu with all beginning pages — reader picks one to begin
4. Each page displays text + clickable choice buttons
5. Navigating updates `history[]` array and syncs path to localStorage for the graph to read
6. At a terminal page (no choices): shows "You have reached an ending" with two action buttons:
   - **View Journey Graph** — opens `graph.html` with the reader's path pre-highlighted
   - **Read Full Story** — opens a full-page overlay showing all visited pages concatenated in reading order with page count and path metadata

**Key data flows:**
- `PAGES` object: merged baseline + dirty author pages
- `history[]`: ordered array of visited page numbers
- `START_PAGES`: Set of page numbers from `story_beginnings.txt`
- `localStorage['readerPath']`: written on every navigation, read by `graph.html`

---

### Page 2 — Journey Graph Viewer (`web/graph.html`)

**Purpose:** Visualize the story graph and highlight the reader's path.

**How it works:**
1. Fetches `/graph` API endpoint to get nodes and edges
2. Renders an interactive Cytoscape.js graph
3. If `localStorage['readerPath']` is set (written by reader), highlights the reader's traversed path in purple
4. Listens for `storage` events to sync in real time when the reader navigates in another tab
5. Clicking a node shows page text and choices in the side panel

**Mode:** Author View scaffold — layer-by-layer expansion starting from root pages. Clicking a node reveals its children. Selected path is green, unselected nodes are gray.

**Removed:** Full Graph tab was removed. Only journey/author view remains.

---

### Page 3 — Author Tool (`web/author.html`)

**Purpose:** Create, edit, and manage story pages with a live graph visualization.

**How it works:**

**Loading and draft management:**
- On load, fetches `pages.json` as the baseline
- Merges with localStorage draft using `dirtyPageSet`:
  - `dirtyPageSet` = Set of page keys the author has explicitly saved this session
  - For each page in localStorage: if it's in `dirtyPageSet` OR doesn't exist in baseline → use localStorage version
  - Otherwise, baseline (pages.json) wins
  - This prevents stale localStorage from overriding new pages.json changes

**Editing workflow:**
1. Left panel: filtered list of all pages (by status: written, unfinished, terminal, shared, missing)
2. Click a page in the list or on the graph → loads into the editor panel
3. Editor fields: page number, text, choices (page + label pairs), "Mark as story beginning", "Mark as terminal ending" checkboxes
4. Save: PUT to `/pages/<n>`, adds key to `dirtyPageSet`, re-renders graph
5. Delete: DELETE to `/pages/<n>`, removes key from `dirtyPageSet`
6. Ctrl+S / Cmd+S: keyboard shortcut triggers save
7. "Add new page" card: creates a blank page entry, focuses editor

**Live graph (Cytoscape.js):**
- Renders after every save/delete
- Node colors are computed by `pageStatus()`:
  - **Green** (`node.written`): page exists, has choices, all targets exist
  - **Amber** (`node.unfinished`): page has at least one choice pointing to a missing target
  - **Gray/slate** (`node.terminal`): structural terminal (choices.length === 0), single path ending
  - **Purple** (`node.shared`): structural terminal AND referenced by 2+ other pages (shared ending)
  - **Red** (`node.orphan`): has broken links
- Edge colors: purple for edges that point to shared-ending nodes
- **Important:** Cytoscape.js does NOT support CSS custom properties (`var(--xxx)`). All colors in `graphStyle()` must be literal hex values.

**Persistence (two modes):**
- `persistDraft()`: saves current draft + `dirtyPageSet` to localStorage (auto after every edit)
- Save to file: uses browser File System Access API (`showSaveFilePicker`) to write JSON directly to disk

**Story beginnings sync:**
- When a page is saved with "Mark as story beginning" checked (`is_start: true`), the Flask server's `_sync_story_beginnings()` writes updated `story_beginnings.txt`
- Reader automatically reflects the change on next load

**Removed:** "New page" button from the left filter panel (the "Add new page" card in the editor is the correct entry point).

---

## Flask Backend (`app.py`)

Serves the static web app and provides a REST API over `web/pages.json`.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves `web/index.html` |
| GET | `/pages` | List all page numbers |
| GET | `/pages/<n>` | Get a single page |
| POST | `/pages` | Create a new page |
| PUT | `/pages/<n>` | Create or update a page |
| DELETE | `/pages/<n>` | Delete a page (also removes dangling choices) |
| GET | `/graph` | Get full graph JSON (nodes + edges) |
| POST | `/graph/rebuild` | Rebuild `output/cot-story-graph.mmd` from current pages |
| GET | `/story_beginnings.txt` | Serve beginning pages list |

### No-Cache Policy

All HTML, JS, JSON, CSS, and TXT responses are served with:
```
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
```
This prevents browsers from serving stale versions of any web asset.

### Story Beginnings Sync

`_sync_story_beginnings(payload)` is called after every write operation. It scans `pages` for entries with `is_story_beginning: true` (or `is_start: true`), sorts them, and writes the sorted page numbers to both `web/story_beginnings.txt` and the root `story_beginnings.txt`.

---

## Shared Endings

A **shared ending** is a terminal page (no outgoing choices) that is referenced by two or more different pages. These represent convergence points where multiple story branches arrive at the same conclusion.

In the current dataset, pages **31** and **45** are shared endings:
- Page 31: reached from both page 20's "witness the end of the world" branch and another branch
- Page 45: reached from both page 49's philosopher path and another path

These are highlighted in purple in the author tool graph.

---

## dirtyPageSet Pattern

**Problem:** The author tool stores its work in localStorage. If `pages.json` is updated (e.g., new story data added), a naive merge would overwrite those new pages with stale localStorage values.

**Solution:** `dirtyPageSet` tracks which pages the author has explicitly saved during their session.

- On save: `dirtyPageSet.add(pageKey)`
- On delete: `dirtyPageSet.delete(pageKey)`
- On reset: `dirtyPageSet = new Set()`
- On `persistDraft()`: saved as `dirtyPages: [...dirtyPageSet]` in localStorage
- On `loadBaseline()`: for each localStorage page — use it only if it's in `dirtyPageSet` or doesn't exist in baseline

This ensures: the author's edits are preserved, but unedited pages always reflect the current `pages.json`.

---

## Story Beginnings Flow

```
Author checks "Mark as story beginning" in author.html
          ↓
PUT /pages/<n> with is_start: true
          ↓
app.py _sync_story_beginnings() writes web/story_beginnings.txt
          ↓
Reader fetches /story_beginnings.txt on load
          ↓
Start menu shows only those page numbers
```

---

## Known Constraints and Gotchas

1. **Cytoscape.js + CSS variables:** Cytoscape does not process CSS custom properties. All color values in `graphStyle()` must be literal hex strings.
2. **Terminal detection:** Always computed as `page.choices.length === 0`. Do not rely on the `is_terminal` flag for UI logic.
3. **PDF page ≠ story page:** See the PDF mapping section above. Always use story page numbers in graph/data logic.
4. **OCR quality:** The v2 extraction is improved but not perfect. Some pages still have minor OCR noise. Page 6 was manually corrected ("tun to page 22" → "turn to page 22").
5. **localStorage persistence:** The draft only survives as long as the browser's localStorage is intact. The canonical data lives in `web/pages.json` (committed to git).
6. **is_start vs is_story_beginning:** The web app internally uses `is_start`. Legacy localStorage may contain `is_story_beginning`. `normalizePage()` reads both with `page?.is_start ?? page?.['is_story_beginning']`.

---

## How to Run

### Start the web app

```bash
pip install -r requirements.txt
python3 app.py
# Open http://127.0.0.1:5000
```

### Regenerate pages.json from source text

```bash
python3 scripts/build_pages_json.py \
  --pages-dir output/cot-pages-ocr-v2 \
  --graph output/cot-story-graph.mmd \
  --output web/pages.json \
  --story-starts 2,22,56,90,97,100,117,119
```

### Regenerate story graph and SVG

```bash
python3 scripts/build_story_graph.py \
  --pages-dir output/cot-pages-ocr-v2 \
  --output output/cot-story-graph.mmd

python3 scripts/render_story_graph_svg.py \
  --graph output/cot-story-graph.mmd \
  --output output/cot-story-graph.svg
```

---

## Session Log

Full interaction history across all sessions is in `session-logs/AI-session-logs.json`. Each session entry includes all requests, responses, and files changed.
