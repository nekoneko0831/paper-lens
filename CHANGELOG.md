# Changelog

## v1.4.0 (2026-05-04)

### Fixes
- Replaced the old Web UI Claude bridge with a long-lived `claude -p --input-format stream-json` subprocess. Follow-up messages now stay in one session instead of respawning per turn.
- Added a small MCP back-channel for structured user questions. Browser question cards now truly block the Claude turn until the user answers, avoiding the `AskUserQuestion` auto-skip behavior in headless stream-json mode.
- Fixed paper titles containing `:` in the frontend session key parser.
- Hardened Markdown rendering: long URLs/paths wrap inside chat bubbles, single-dollar text no longer triggers noisy KaTeX parsing, and invalid math no longer stalls the page.
- Sanitized restored browser session history so stale or malformed tool/question events cannot white-screen the UI after refresh.
- Fixed React 19 lint blockers in the Web UI and updated backend tests for the new turn lifecycle.

### Notes
- The backend still requires a logged-in Claude Code CLI and must still be run as the normal user, not with `sudo`.
- `paper-lens-web/.env.local.example` is now explicitly tracked; copy it to `.env.local` for direct browser-to-backend SSE calls.

## v1.3.1 (2026-04-26)

### Bug fixes
- **Backend session reaper killed mid-turn sessions.** `SESSION_TTL_SECONDS` was 600s, and the `last_active` timestamp only got refreshed by HTTP endpoints (`start-session`, `/api/stream`, `/api/answer`) and the initial CLI WebSocket connect — *not* by individual CLI WS frames flowing through. So in long deep-learn turns where Claude was actively producing output (or parked on AskUserQuestion waiting for user input) the cleanup task could reap the session mid-flight. The user's next `POST /api/answer/{sid}` then 404'd with no obvious cause.
  - Fix: cleanup now skips any session whose `_cli_ws is not None` — i.e. while the CLI subprocess is still attached to its WebSocket, the session is treated as live regardless of the timestamp.
  - Defense-in-depth: bump default TTL from 600s → 1800s (30 min) so genuine idle sessions still get garbage-collected, but normal multi-step turns and AskUserQuestion think-time fit comfortably inside the window.

## v1.3.0 (2026-04-25)

### New Features
- **Web UI shipped** — FastAPI backend (`paper-lens-backend/`, port 8765) + Next.js frontend (`paper-lens-web/`, port 3000) are now part of the open-source repo. The CLI skill remains independently usable; the Web UI is opt-in.
- **Phase -1 environment probe** — On every load the skill probes whether the Web UI is running and prints a one-line hint (no auto-launch, no auto-open). Falls back to pure CLI mode if the Web UI is absent.

### Improvements
- README: dedicated "Web UI" section with install + run instructions and a clear `sudo` warning.
- Top-level `.gitignore` now covers Node/Next.js artifacts (`node_modules/`, `.next/`, `*.tsbuildinfo`, etc.) so the repo stays clean for monorepo contributors.
- `paper-lens-web/.env.local.example` added so users know which env var to set without leaking the maintainer's local config.

### Notes
- The backend spawns a Claude Code subprocess. It inherits the invoking shell's credentials, so the operator must have already completed `claude` `/login`. Do not start the backend with `sudo`.

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
