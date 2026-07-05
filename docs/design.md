# WinstyleS Technical Reference

This document is a compact developer reference. Durable contracts live in
`docs/specs/`; architecture background lives in `docs/ARCHITECTURE.md`.

## GUI Strategy

- Default GUI: local Web server plus browser frontend.
- Fallback GUI: legacy CustomTkinter surface.
- The Web server is local-only and binds to loopback.

See `docs/specs/web-api.md` for the Web API contract.

## CLI Summary

```bash
winstyles scan
winstyles scan -c fonts -c terminal -f json
winstyles export ./my-style.zip
winstyles export ./my-style.zip --include-font-files
winstyles import ./my-style.zip --dry-run
winstyles import ./my-style.zip --skip-restore-point
winstyles report --no-check-updates
winstyles diff ./old.zip ./new.zip -f json
winstyles inspect ./my-style.zip -f json
```

Machine-readable `json` and `yaml` output should be parseable stdout without
human banners. Table output may include human-oriented progress text.

## Scanner Categories

Current categories are:

- `fonts`
- `terminal`
- `theme`
- `wallpaper`
- `cursor`
- `vscode`

There is no `browser` scanner.

## Contract Index

- Import safety: `docs/specs/import-safety.md`
- Web API: `docs/specs/web-api.md`
- CLI output: `docs/specs/cli-output.md`
- Quality gates: `docs/specs/quality-gates.md`

## Release Governance

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".uv-verify"
uv run --python 3.12 --extra dev python scripts\release_check.py
```

The full release check runs black, ruff, mypy, pytest, `winstyles --version`,
and `winstyles scan -f json`.
