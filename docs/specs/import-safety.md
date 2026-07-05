# Import Safety Spec

Status: Accepted
Owner: maintainers
Prefix: `IMP-`

## Scope

This spec governs `StyleEngine.import_package()`, CLI `winstyles import`, Web
API `import_config`, package extraction, dry-run planning, pre-apply checks,
asset relocation, plugin dispatch, and import audit artifacts.

## Non-goals

- This spec does not require installing fonts, VS Code extensions, Oh My Posh,
  or lockscreen/Spotlight settings.
- This spec does not define Windows System Restore internals.
- This spec does not promise atomic rollback of every plugin write.

## Normative Clauses

- `IMP-01`: Dry-run import MUST NOT write registry values, write config files,
  create imported asset directories, or copy package assets.
- `IMP-02`: Zip import MUST reject absolute paths, drive-qualified paths, root
  paths, and `..` traversal before extracting any member.
- `IMP-03`: Default apply import MUST abort before plugin writes when restore
  point creation fails, unless the caller explicitly disables restore-point
  creation.
- `IMP-04`: Apply import MUST abort before plugin writes when writable package
  items require administrator privileges and the current Windows process is not
  elevated.
- `IMP-05`: Apply import MUST create a pre-import backup package before plugin
  writes; backup failure MUST abort the import.
- `IMP-06`: Every import attempt MUST write an `import_log.json` audit artifact
  unless writing the log itself fails, in which case the summary MUST report
  `import_log_error`.
- `IMP-07`: Items marked `metadata.readonly=true` MUST be skipped by apply and
  reported as skipped in dry-run plans and audit data.
- `IMP-08`: Package assets MUST be relocated only during apply, and only from
  package `assets/<category>/` into `~/.winstyles/imported_assets/<scan_id>/`.

## Contract Coverage

- `tests/unit/test_engine_import_routing.py` enforces `IMP-01`, `IMP-02`,
  `IMP-03`, `IMP-04`, `IMP-05`, `IMP-06`, and `IMP-07`.
- `tests/unit/test_import_asset_resolution.py` enforces `IMP-08`.
- `tests/contracts/test_spec_traceability.py` enforces spec/test traceability.
