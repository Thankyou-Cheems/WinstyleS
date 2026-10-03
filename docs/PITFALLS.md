# PITFALLS

## 2026-10-03: Import tests must isolate audit output

The administrator-denial regression used real `Path.home()` for its audit log.
It failed under the workspace sandbox and could leave artifacts in a developer's
profile. Patch home to the test's temporary directory, as enforced by
`test_import_aborts_admin_required_items_without_admin_on_windows`.

## 2026-07-05: Shared environment broke Windows uv verification

`uv run --python 3.12 --extra dev ...` failed while trying to remove `.venv/lib64`
with access denied. The environment was created by non-Windows tooling. Use a
Windows-owned environment; setup is in [CONTRIBUTING](../CONTRIBUTING.md).
