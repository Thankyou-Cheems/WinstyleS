# Behavior worth preserving

Read this when changing packages, import, output, or the local Web API.
The tests below exercise the behavior; documentation identifiers are not a gate.

## Packages and import

Packages contain `manifest.json`, `scan.json`, and optional `assets/<category>/`.
Reject zip members with absolute, drive-qualified, rooted, or traversal paths
before extraction. Preserve original files when JSONC parsing fails.

Preview reads the plan without writing registry/config values, copying assets,
creating an asset directory, or writing import logs. Browser upload preview may
create a temporary zip, which the handler removes even on failure.

Apply skips `metadata.readonly=true` items. Check required administrator rights,
the restore point (unless explicitly skipped), and pre-import backup before
plugin writes; abort when a prerequisite fails. Relocate packaged assets during
apply only. Write an audit log for actual import attempts and report log failures.

The backup and restore point do not make all plugin writes atomic. Recovery needs
review; the tool does not promise complete automatic rollback. Credentials,
account tokens, extension installation, and cloud synchronization are outside
the current profile workflow.

Verify with `tests/unit/test_engine_import_routing.py`,
`test_import_asset_resolution.py`, `test_terminal_apply.py`, `test_vscode_apply.py`,
and `test_report_security.py`.

## Local Web API and review

Bind to `127.0.0.1`. Success envelopes are
`{ok:true,data,error:null,code:"ok",message}`; errors retain
`{ok:false,data,error,code,message}` and core error details. Status includes
`status`, `mode`, `frontend_dir`, `src_dir`, `version`, `os`, and `is_admin`.
Browser path browsing fails visibly instead of inventing a path.

`import_config` with JSON boolean `dryRun:true` returns a structured engine summary
in development and bundled modes. It includes `dry_run_plan`, `would_apply`,
`would_skip`, `admin_required`, and `risk_summary`; each plan entry contains
category/key, action/operation, source target, risk, administrator requirement,
and reasons. Source paths are recorded package paths, not a guarantee of the
final destination. Apply retains its existing response behavior.

The browser requires a successful preview of the current source before running
import. Changing the path or upload invalidates the review. This is a user
interface guard, not server authentication or a cryptographically bound approval:
a local path may change on disk after preview. Category/risk/search filters
affect display only; import still handles the entire package.

Render package text as text or escape it, including raw JSON. Keep the original
error code/message visible. Read-only preview and an empty plan are valid states.

Verify with `tests/unit/test_start_web_ui_mapping.py`, `test_web_import_preview.py`,
`tests/contracts/test_web_api_contract.py`, and
`node --test tests/frontend/import-plan.test.cjs`.

## CLI and verification

JSON/YAML stdout is parseable data without human banners; HTML reports escape
scan values and filter unsafe links. Quality checks fail on formatting, lint,
type, or test failures; results do not prove elevated apply safety.

Verify with `tests/unit/test_cli_package_output.py`, `test_cli_report.py`,
`tests/contracts/test_quality_gates_contract.py`, and the checks in CONTRIBUTING.
