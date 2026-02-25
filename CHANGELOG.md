# Changelog

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
