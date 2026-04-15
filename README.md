# choose-your-own-adventure

## Build Story Graph

Run:

```bash
python3 scripts/build_story_graph.py \
	--pages-dir output/cot-pages-ocr-v2 \
	--output output/cot-story-graph.mmd
```

Generated output:

- `output/cot-story-graph.mmd`: Mermaid graph of branching story transitions from the corrected OCR v2 page set

## Generate All Story Variants

Run:

```bash
python3 scripts/write_all_stories.py
```

Generated outputs:

- `output/cot-stories/story-0001.txt` (and additional numbered files): one complete path per file
- `output/cot-stories/manifest.json`: index of generated story files and page paths

## Run the Web App

Start the Flask backend from the project root, then open the app in your browser.

```bash
python -m pip install -r requirements.txt
python app.py
```

Open:

- `http://127.0.0.1:5000/` for the reader
- `http://127.0.0.1:5000/graph.html` for the story graph
- `http://127.0.0.1:5000/author.html` for the authoring tool

API endpoints:

- `GET /pages` lists page numbers
- `GET /pages/<n>` returns one page
- `POST /pages` creates a page
- `PUT /pages/<n>` updates a page
- `DELETE /pages/<n>` removes a page and unlinks references
- `GET /graph` returns graph nodes and edges
- `POST /graph/rebuild` writes `output/cot-story-graph.mmd`

The authoring tool keeps a browser draft, can export updated JSON, and can save to a chosen file path when the browser file picker is available.

Optional flags:

```bash
python3 scripts/write_all_stories.py \
	--graph output/cot-story-graph.mmd \
	--pages-dir output/cot-pages-ocr-v2 \
	--output-dir output/cot-stories \
	--start-page 2 \
	--max-decisions 20
```

## Re-Extract From Spread-Scanned PDF

The book scan is a two-page spread layout. The story starts on the left side of PDF page 8:

- PDF page 8 -> story pages 2 and 3
- PDF page 9 -> story pages 4 and 5

Run:

```bash
python3 scripts/reextract_cot_ocr_split.py \
	--pdf samples/the-cave-of-time.pdf \
	--pdf-start-page 8 \
	--pdf-end-page 66 \
	--story-start-page 2 \
	--output-dir output/cot-pages-ocr-v2
```

Generated output:

- `output/cot-pages-ocr-v2/*.txt`: OCR re-extraction using left/right half-page splitting