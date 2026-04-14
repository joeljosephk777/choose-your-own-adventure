# Project TODO

## Phase 1: Reader (Static HTML)
- [x] Create a basic HTML page that loads a story page by number
- [x] Display page text content to the reader
- [x] Parse and display choices at the bottom of each page ("turn to page X")
- [x] Make choices clickable — navigate to the chosen page
- [x] Add a "start over" button back to page 2
- [x] Style the reader (readable font, clean layout)
- [x] Test all 45 story paths navigate correctly to their endings

## Phase 2: Story Graph Viewer
- [x] Embed interactive graph in a webpage (web/graph.html using Cytoscape.js)
- [x] Make nodes clickable — clicking shows page text + choices in side panel
- [x] Highlight the main trunk from page 2 (blue)
- [x] Color-code terminal/ending nodes (red) and regular nodes (gray)
- [x] Add a legend for both Full Graph and Author View modes
- [x] Full Graph mode — all 111 nodes, zoom/pan, fit controls
- [x] Author View (scaffold) mode — layer-by-layer reveal starting from page 2
- [x] "Read from here" button — opens index.html at the selected page
- [x] Link from reader (index.html) to graph (graph.html)
- [x] index.html supports ?page=N URL param so graph can open reader at any page
- [ ] Highlight the path taken as the reader progresses (reader ↔ graph sync)
- [ ] Show unfinished branches (author-mode nodes with no choices yet written)

## Phase 3: Authoring Tool
- [ ] Upload a new story segment (text file or text area input)
- [ ] Assign it a page number
- [ ] Define outgoing choices (link this page to one or more other pages)
- [ ] Save the new segment to the pages directory
- [ ] Regenerate the story graph after adding a new segment
- [ ] Display the updated graph with the new node highlighted
- [ ] Show which branches are unfinished (leaf nodes that are not marked as endings)
- [ ] Show which endings are shared by multiple paths (converging branches)
- [ ] Allow editing existing story segments
- [ ] Allow deleting a story segment and unlinking it from the graph

## Phase 4: Web Server / Backend
- [ ] Set up a simple backend (Python Flask or similar) to serve pages data as JSON
- [ ] API endpoint: GET `/pages` — list all page numbers
- [ ] API endpoint: GET `/pages/<n>` — return text and choices for page n
- [ ] API endpoint: POST `/pages` — upload a new story segment
- [ ] API endpoint: PUT `/pages/<n>` — edit an existing segment
- [ ] API endpoint: DELETE `/pages/<n>` — remove a segment
- [ ] API endpoint: GET `/graph` — return graph data (nodes + edges)
- [ ] API endpoint: POST `/graph/rebuild` — rebuild graph from current pages

## Phase 5: Project Hygiene
- [ ] Update session-logs/AI-session-logs.json after each work session
- [ ] Keep Codebase.md up to date as new files are added
- [ ] Write a short section in README.md for how to run the web app
- [ ] Test the full pipeline: extract → graph → stories → web reader → authoring tool

## Completed
- [x] OCR-extract 111 story pages from the Cave of Time PDF
- [x] Build story graph (58 nodes, Mermaid format)
- [x] Generate all 45 story paths with cycle detection
- [x] Render story graph as SVG (color-coded: blue trunk, red endings, gray regular)
- [x] Create Codebase.md project state guide
- [x] Set up session-logs/ folder with combined AI session log
- [x] Phase 1: Static HTML reader (web/index.html + web/pages.json)
- [x] Phase 2: Interactive graph viewer (web/graph.html) — Full Graph + Author scaffold mode
