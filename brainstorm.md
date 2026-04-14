# Brainstorm

## Core Concept
A web-based platform for writing AND reading "Choose Your Own Adventure" style stories.
Two modes: Author Mode (create/edit stories) and Reader Mode (play through stories).

---

## Reader Experience Ideas

### Navigation
- Click choices at the bottom of each page to advance
- Breadcrumb trail showing the path taken so far (e.g. Page 2 → 3 → 5 → 16)
- Back button to undo the last choice
- "Restart" button to go back to page 1
- Bookmark / save progress in browser localStorage so you can return later
- Show how many pages are in this story path (e.g. "Step 4 of ~9")

### Presentation
- Animated page transitions (fade or slide)
- Typewriter effect for text appearing on screen
- Show an illustration or image placeholder per page (authors could upload images)
- Dark mode / light mode toggle
- Font size controls for accessibility
- Audio narration support (authors upload MP3 per page)
- Show a mini-map of the graph in the corner while reading, highlighting current position

### Engagement
- Track which endings the reader has reached ("You've found 3 of 28 endings")
- Show a % completion of all possible paths explored
- Achievement badges for reaching certain endings
- Share your path/ending on social media
- "Hint" button that subtly suggests which choice leads somewhere new

---

## Authoring Tool Ideas

### Writing Interface
- Rich text editor (bold, italic, paragraphs) per page segment
- Auto-detect "turn to page X" phrases and convert them to clickable links in preview
- Side-by-side: write on the left, preview on the right
- Drag and drop to reorder pages
- Autosave as you type
- Version history per page (undo changes, see diffs)

### Graph Management
- Live-updating graph as you add/link pages
- Click any node in the graph to jump to that page's editor
- Color coding in the authoring graph:
  - Green = fully written and linked
  - Yellow = written but has unlinked choices
  - Red = referenced by another page but not yet written (orphan target)
  - Gray = terminal ending page
- Drag nodes in the graph to rearrange layout
- Zoom and pan the graph
- Filter graph to show only unfinished branches

### Story Structure Tools
- "Dead end detector" — highlights pages that lead nowhere unintentionally
- "Convergence detector" — shows which pages are reached from many different paths
- "Longest path" view — highlights the longest possible story
- "Shortest path" view — highlights the quickest way to an ending
- Word count per page and per story path
- Export full story as a single PDF or printable HTML
- Import an existing CYOA PDF (using the OCR pipeline already built)

### Collaboration
- Multi-author support: assign different branches to different writers
- Comments/notes on each page (visible only to authors)
- "Lock" a page so other authors can't edit it
- Change history with author attribution

---

## Technical Architecture Ideas

### Frontend Options
- Plain HTML + CSS + JavaScript (simplest, no build step)
- React (component-based, good for the graph viewer and editor)
- Vue.js (lighter than React, good for beginners)
- Svelte (very lightweight output)

### Backend Options
- Python Flask (already using Python for scripts, natural fit)
- Python FastAPI (modern, auto-generates API docs)
- Node.js + Express (if going full JavaScript stack)
- No backend at all — store everything as static JSON files served by GitHub Pages

### Data Storage Options
- Plain JSON files on disk (simplest, no database needed)
- SQLite (lightweight database, good for single-user)
- PostgreSQL (if multi-user collaboration is needed)
- Browser localStorage only (fully offline, no server)
- GitHub as storage (commit story pages as files, use GitHub API)

### Graph Rendering Options
- Keep the existing custom SVG renderer (already works)
- D3.js (powerful, interactive, lots of examples online)
- Cytoscape.js (built specifically for graph/network visualization, easy pan/zoom/click)
- Mermaid.js (render the existing .mmd files directly in browser)
- vis.js (interactive network graphs)

---

## Stretch / Fun Ideas

- **AI-assisted writing**: given the current page text, suggest 2-3 possible next pages
- **Procedural story generation**: auto-generate placeholder pages to fill unfinished branches
- **Story analytics dashboard**: which paths are most popular with readers? Which endings are never reached?
- **Multiplayer reading**: two readers on the same story, each making choices for alternate pages
- **Time travel mechanic**: let the reader "rewind" to any previous choice point
- **Comparison view**: show two different story paths side by side
- **Story templates**: start a new story from a pre-built graph skeleton (e.g. "3-act structure", "mystery", "adventure")
- **Export to Twine**: export the story in Twine format for use in other tools
- **Mobile app**: package the reader as a PWA (Progressive Web App) for offline reading on phones
- **Print mode**: format the story like the original CYOA books (scrambled page order, physical page references)

---

## Author Mode — Scaffold / Layer-by-Layer Reveal (added 2026-04-14)

The story graph in author mode should work like a scaffold that expands as you explore:
- Start on page 2 — only page 2 is visible
- Click page 2 → page 3 is revealed
- Click page 3 → pages 4 and 5 are revealed (the branch point)
- Click page 4 → pages 8 and 10 are revealed
- Continue expanding the tree as you author the story

This mirrors how a real author thinks: you write one page, then decide where it can go next, then write those options. The graph grows as the story grows. Nodes that are "available" (revealed but not yet expanded) are shown in amber/yellow. Nodes that have been expanded are shown in green.

## Immediate Next Steps (pick one to start)
1. **Build the reader** — HTML + JS, load pages from JSON, navigate by clicking choices ✅ Done
2. **Build the graph viewer** — interactive Cytoscape.js graph with Full Graph + Author scaffold mode ✅ Done
3. **Build the backend API** — Flask server, serve pages as JSON, support add/edit/delete
4. **Build the authoring tool** — text editor per page, connect to backend API, live graph update
