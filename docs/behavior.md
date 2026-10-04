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

The browser uses `review_import`, `apply_reviewed_import`, and `recover_import`.
Review compares package values with current settings, and canonicalizes write
destinations and metadata from the local scanner. Start with zero selected items.
Category/risk/search filters change visibility; selection persists independently.
Apply requires explicit unique eligible IDs and the review digest. Read the zip
into an immutable snapshot, recheck the package/current digest, then recheck each
setting immediately before writing. Source changes invalidate browser review too.

Reviewed imports accept schema 1.0.0 zip packages (legacy scan-only packages have
that implicit schema), up to 32 MiB compressed / 128 MiB expanded. Reject ambiguous
member names or category/key identities. Missing local settings, readonly items,
scripts/system APIs, wallpaper/cursor resource paths, and non-config dependencies
are ineligible. Whole config attachments are not copied; adapters modify only
selected settings. Legacy CLI/import_config keeps its existing whole-package path.

Save selected before/after values and pending/attempting/applied state before
plugin writes. On failure, try restoring touched items in reverse order, preserving
untouched selections and foreign changes; an unreadable current value requires
explicit recovery retry rather than a blind overwrite. Report a journal path and
SHA-256 receipt even when rollback needs retry. Explicit recovery verifies the receipt, current destination/value,
administrator rights, and drift before each write. A foreign current value stops
recovery. Receipts detect file changes; they are not an authorization credential.
Recovery records may contain sensitive configuration: keep them local.

This is a small settings journal, not a filesystem transaction or OS lock. Another
process can still change a value in the gap between checking and writing; power
loss/disk failure can prevent a final receipt being returned. The browser keeps
only the latest receipt in memory; cross-session recovery management is future work.

API requests require the process's HttpOnly/SameSite=Strict session cookie, exact
loopback Host, JSON content type, and same Origin when provided. The trusted index
issues the cookie. Reject malformed object payloads and requests over 48 MiB. This
blocks ordinary cross-site requests and DNS rebinding; it does not isolate another
local process, another service on the same loopback host, or a compromised UI.
External API clients must open the index and retain the cookie first; envelopes
remain unchanged. All responses disable caching. No remote-account auth is added.

Render package text as text or escape it, including raw JSON. Keep the original
error code/message visible. Read-only preview and an empty plan are valid states.

Verify with `tests/unit/test_start_web_ui_mapping.py`, `test_web_import_preview.py`,
`test_reviewed_import.py`, `test_web_request_safety.py`,
`tests/contracts/test_web_api_contract.py`, and
`node --test tests/frontend/import-plan.test.cjs`.

## CLI and verification

JSON/YAML stdout is parseable data without human banners; HTML reports escape
scan values and filter unsafe links. Quality checks fail on formatting, lint,
type, or test failures; results do not prove elevated apply safety.
Build depends on the reusable CI matrix, and release depends on build; a failed
quality job prevents either downstream job from running.

Verify with `tests/unit/test_cli_package_output.py`, `test_cli_report.py`,
`tests/contracts/test_quality_gates_contract.py`, and the checks in CONTRIBUTING.
