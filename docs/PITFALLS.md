# PITFALLS

Newest entries first. Each incident should map to a spec clause and a
regression pin when the failure mode can be reproduced.

### 2026-07-05 - Shared `.venv` broke Windows uv verification

Symptom: `uv run --python 3.12 --extra dev ...` failed while trying to remove
`.venv\lib64` with Windows access denied.

Root cause: The repository contained a non-Windows virtual environment layout;
Windows uv tried to reconcile it as the project environment.

Spec: `docs/specs/quality-gates.md` `QG-02`, `QG-03`

Pin: `tests/contracts/test_quality_gates_contract.py`
