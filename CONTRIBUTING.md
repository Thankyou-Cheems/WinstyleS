# Development

Python 3.11+ and Windows are the target runtime. The Web frontend uses plain
HTML/CSS/JavaScript; Node's built-in test runner verifies presentation logic.

Create an environment in your checkout; use a different environment for WSL:

```powershell
python -m venv .venv-windows
.venv-windows\Scripts\python -m pip install -e ".[dev]"
```

Run checks using that environment's Python, in order:

```powershell
python -m black --check src tests start_web_ui.py
python -m ruff check src tests start_web_ui.py
python -m mypy src/winstyles
python -m pytest tests
node --test tests/frontend/import-plan.test.cjs
python -m winstyles --version
```

An optional read-only smoke scan is `python -m winstyles scan -f json`.
`scripts/release_check.py` remains the uv-based release check, including that scan.
Unit tests exercise writes against mock adapters and temp directories. A green
test run does not validate real elevated Windows apply.

When editing a scanner, test through the engine with synthetic settings. When
editing the browser UI, check loading, errors, empty results, keyboard access,
long paths, light/dark mode, and narrow windows. Use mocked API responses for
write workflows; runtime payloads are described in [behavior](docs/behavior.md).

Keep changes on a branch and report verification gaps with the deliverable.
Update the user-facing README when behavior changes. Store consequential choices
with their reasons, rather than maintaining duplicate completion tables.

Legacy backlog records remain in `.beads/`; their historical Phase labels are
not the current product plan. Old documentation is recoverable at `ce70fef`.
