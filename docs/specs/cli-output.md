# CLI Output Spec

Status: Accepted
Owner: maintainers
Prefix: `CLI-`

## Scope

This spec governs machine-readable stdout for public CLI commands in
`src/winstyles/main.py`, especially `scan`, `diff`, `inspect`, and `report`.

## Non-goals

- This spec does not define the full JSON schema for every command payload.
- This spec does not ban human-oriented banners in table output.
- This spec does not require stderr to be machine-readable.

## Normative Clauses

- `CLI-01`: Commands invoked with `--format json` and no `--output` MUST print
  only JSON payload bytes to stdout.
- `CLI-02`: Commands invoked with `--format yaml` and no `--output` MUST print
  only YAML payload bytes to stdout.
- `CLI-03`: Human-readable progress banners MUST be limited to table output or
  file-output confirmations.
- `CLI-04`: `winstyles report` without `--output` MUST print report content as
  plain Markdown or HTML, not a JSON-encoded string, except when
  `WINSTYLES_WEB_MODE=1`.

## Contract Coverage

- `tests/unit/test_cli_package_output.py` enforces `CLI-01` and `CLI-03` for
  `diff` and `inspect`.
- `tests/unit/test_cli_report.py` enforces `CLI-04`.
- `tests/contracts/test_spec_traceability.py` enforces spec/test traceability.
