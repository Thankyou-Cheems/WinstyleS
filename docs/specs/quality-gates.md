# Quality Gates Spec

Status: Accepted
Owner: maintainers
Prefix: `QG-`

## Scope

This spec governs local release checks, CI quality gates, and environment
selection for contributors and coding agents.

## Non-goals

- This spec does not define packaging release approval.
- This spec does not claim unit tests validate real elevated Windows behavior.
- This spec does not require WSL to own the Python virtual environment.

## Normative Clauses

- `QG-01`: The full local release check MUST run black, ruff, mypy, pytest,
  `winstyles --version`, and `winstyles scan -f json` in that order.
- `QG-02`: Windows and WSL/Linux tooling MUST NOT share one `.venv` for this
  repository.
- `QG-03`: Local verification from Windows SHOULD set `UV_PROJECT_ENVIRONMENT`
  to a Windows-owned path such as `.uv-verify`.
- `QG-04`: CI MUST treat black, ruff, mypy, and pytest failures as hard
  failures.
- `QG-05`: Green CI MUST NOT be represented as proof of real elevated Windows
  apply behavior; human smoke testing is required for that boundary.

## Contract Coverage

- `tests/contracts/test_quality_gates_contract.py` enforces `QG-01`.
- `.github/workflows/ci.yml` enforces `QG-04`.
- `tests/contracts/test_spec_traceability.py` enforces spec/test traceability.
