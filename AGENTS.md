# AGENTS.md

本文件是仓库协作路由器，不是唯一规则源。持久规则必须落到
`docs/specs/`，本文件只保留入口、硬约束和收尾命令。

## Repository Map

- CLI: `src/winstyles/main.py`
- Core orchestration: `src/winstyles/core/engine.py`
- Scanners/apply adapters: `src/winstyles/plugins/`
- System adapters: `src/winstyles/infra/`
- Local Web GUI: `start_web_ui.py` + `frontend/`
- Architecture background: `docs/ARCHITECTURE.md`
- Canonical contracts: `docs/specs/`
- Incident log: `docs/PITFALLS.md`
- Decisions: `docs/adr/`

## Spec-Anchored Rules

- Durable cross-module behavior MUST be documented in `docs/specs/` before the
  change is considered complete. Summaries in README/docs may link to specs but
  must not restate normative clauses.
- Import safety changes MUST preserve `docs/specs/import-safety.md`.
- Web API changes MUST preserve `docs/specs/web-api.md`.
- Release and quality-gate changes MUST preserve `docs/specs/quality-gates.md`.
- New incidents MUST add a `docs/PITFALLS.md` entry and a regression test when
  the failure mode is reproducible.

## Documentation Sync Rules

- Version changes in `pyproject.toml` MUST update `CHANGELOG.md`.
- New user-visible features or behavior changes MUST update `README.md` and, if
  they affect durable contracts, the relevant `docs/specs/` file.
- CLI changes MUST update README usage examples and `docs/design.md` if the
  technical reference changes.
- Dependency changes MUST update `pyproject.toml` and `CHANGELOG.md`.
- Repository URL or badge changes MUST update `pyproject.toml` `project.urls`
  and README links.

## Task Tracking

- Use bd for backlog and follow-up work.
- On this Windows checkout, the canonical bd command is currently the WSL
  binary:

  ```bash
  cd /mnt/d/Dev/WinstyleS
  /home/cheems/dev/Beads/bd list --ignore-schema-skew
  ```

- Windows `bd` may fail on the embedded schema; do not hand-edit `.beads`.
- `bd sync` is not available in the current bd binaries. Use `bd vc status` to
  check database version-control state until the T0 bd workflow task is resolved.

## Quality Gates

Use a Windows-owned uv environment. Do not reuse the checked-in `.venv` from WSL
or Linux tooling.

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".uv-verify"
uv run --python 3.12 --extra dev python scripts\release_check.py
Remove-Item Env:UV_PROJECT_ENVIRONMENT
```

The full release check runs black, ruff, mypy, pytest, `winstyles --version`,
and `winstyles scan -f json`.

## CI Failure Order

Handle the first failing gate in order:

1. `black`
2. `ruff`
3. `mypy`
4. `pytest`

If zero tests are collected, add minimum regression coverage. For Windows
console encoding errors, avoid emoji in CLI output or force UTF-8 explicitly.

## Landing the Plane

Work is not complete until local changes are committed and pushed, unless the
user explicitly asked for an uncommitted investigation.

1. File bd issues for remaining work.
2. Run quality gates when code changed.
3. Update bd issue status when the active issue is finished.
4. Run:

   ```bash
   git pull --rebase
   # bd sync is unavailable in current bd; use canonical bd vc status instead.
   git push
   git status
   ```

5. Report any untracked pre-existing files separately.
