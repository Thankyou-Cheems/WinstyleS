# Web API Spec

Status: Accepted
Owner: maintainers
Prefix: `WEB-`

## Scope

This spec governs the local Web API implemented by `start_web_ui.py` and
consumed by `frontend/main.js`. It covers response envelopes, status payloads,
command dispatch, file upload import, and frontend error handling expectations.

## Non-goals

- This spec does not define a remote or multi-user API.
- This spec does not require native file-picker support in browser mode.
- This spec does not require Web GUI parity with the legacy CustomTkinter GUI.

## Normative Clauses

- `WEB-01`: Every Web API success response MUST use the envelope
  `{ok:true,data,error:null,code:"ok",message}`.
- `WEB-02`: Every Web API error response MUST use the envelope
  `{ok:false,data,error,code,message}` and preserve structured core error data
  when available.
- `WEB-03`: The local Web server MUST bind to loopback only.
- `WEB-04`: `/api/status` and the `status` command MUST return `status`,
  `mode`, `frontend_dir`, `src_dir`, `version`, `os`, and `is_admin`.
- `WEB-05`: Browser path browsing commands MUST fail or no-op visibly; they
  MUST NOT fabricate a local path.
- `WEB-06`: File upload import MUST decode `fileBase64` into a temporary zip and
  remove that temporary file after command handling.
- `WEB-07`: Frontend command invocation MUST unwrap the envelope and surface
  `code` and `message` for failed responses.

## Contract Coverage

- `tests/unit/test_start_web_ui_mapping.py` enforces `WEB-01`, `WEB-02`,
  `WEB-04`, `WEB-06`, and `WEB-07`.
- `tests/contracts/test_web_api_contract.py` enforces `WEB-01`, `WEB-02`, and
  `WEB-03`, `WEB-04`.
- `tests/contracts/test_spec_traceability.py` enforces spec/test traceability.
