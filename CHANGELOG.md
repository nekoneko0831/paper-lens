# Changelog

## v1.2.0 (2026-04-17)

### New Features
- **Batch Search**: Search papers by topic via WebSearch — outputs a ranked table with links, then offers to download selected papers
- **Batch Download**: Paste multiple arXiv URLs/IDs to download in batch — with 3-layer dedup (input / local / arXiv ID)
- **Style selection enforcement**: Present mode now requires `/frontend-slides` to ask user for visual style preference (no more silent defaults)

### Improvements
- Deep Learn mode: "analogy-first" → "analogy-precise" — fewer stacked metaphors, sharper terminology tables (4-column format)
- Present mode: explicit figure fallback path when `images/` directory is empty
- PDF export: cross-platform `open` command, LaTeX auto-resize, temp file cleanup
- Figure extraction: cross-type dedup (vector regions suppress overlapping embedded images)
- Mode router: auto-detect batch search/download intent from user input (no manual mode selection needed)

## v1.1.0 (2026-02-26)

12 fixes covering scripts, instructions, and README. See git log for details.

## v1.0.0 (2026-02-26)

Initial open-source release.

### Features
- Three-mode paper reading: Speed Read, Deep Learn, Present
- Smart figure extraction from PDF (vector + bitmap) via PyMuPDF
  - Rectangle merging for split figures
  - Caption detection for cross-column figure expansion
  - Manifest.json output for programmatic access
- Incremental note-saving in Deep Learn mode (边学边存)
- Interactive term/formula selection via AskUserQuestion
- Dual-layer formula output (ASCII in terminal, LaTeX in saved file)
- "Big Whitepaper" (大白话) style explanations for non-specialists
- Figure-to-slide mapping with semantic renaming
- Base64 image embedding for self-contained HTML presentations

### Tested With
- SWE-Compass (arXiv 2511.05459v3): Speed Read + Deep Learn + Present
- τ²-Bench (UC Berkeley 2025): Deep Learn + Present
