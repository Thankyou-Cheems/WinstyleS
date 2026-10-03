# WinstyleS Architecture

Status: descriptive

WinstyleS is a Windows personalization scanner, exporter, importer, and local
Web GUI. This document describes extension points; import and API compatibility
live in [behavior](behavior.md).

## Runtime Surfaces

- `winstyles` CLI is implemented in `src/winstyles/main.py` with Typer.
- The default GUI entry starts the local Web UI through `start_web_ui.py`.
- `src/winstyles/gui/app.py` is a legacy/fallback CustomTkinter surface and is
  not the primary feature surface.

## Layer Map

- Domain models: `src/winstyles/domain/models.py` and
  `src/winstyles/domain/types.py`
- Core orchestration: `src/winstyles/core/engine.py`
- Report/update helpers: `src/winstyles/core/report.py` and
  `src/winstyles/core/update_checker.py`
- Infrastructure adapters: `src/winstyles/infra/`
- Scanner/apply plugins: `src/winstyles/plugins/`
- Web API and static frontend: `start_web_ui.py`, `frontend/index.html`,
  `frontend/main.js`, `frontend/style.css`, and `frontend/import-plan.js`

## Data Flow

1. CLI or Web API builds a `StyleEngine`.
2. `StyleEngine` loads scanner plugins and default values.
3. Scan results are represented as `ScanResult` with `ScannedItem` entries.
4. Export writes `manifest.json`, `scan.json`, and optional assets.
5. Import loads a package, optionally produces dry-run risk data, then applies
   writable items through the matching plugin.
6. Reports render scan data as Markdown or HTML.

## Scanner Categories

The current plugin categories are:

- `fonts`
- `terminal`
- `theme`
- `wallpaper`
- `cursor`
- `vscode`

There is no browser scanner. User-facing help and docs must not advertise a
`browser` category unless a scanner is added.

## Import Safety Boundary

Import is the highest-risk workflow because it writes registry values, user
configuration files, and relocated assets. Its durable contract is
[behavior](behavior.md#packages-and-import).

## Web API Boundary

The Web GUI talks to the local Python service through a small command-oriented
API. Its durable response envelope and status payload contract are in
[behavior](behavior.md#local-web-api-and-review).

## Quality Boundary

Verification commands and environment setup live in [CONTRIBUTING](../CONTRIBUTING.md).
