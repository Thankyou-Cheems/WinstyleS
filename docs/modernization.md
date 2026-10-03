# Modernization decisions — 2026-10-03

## Goal and inherited work

Make a local personalization profile manager: inspect what is customized, review
what a portable package would write, and eventually choose individual changes,
compare saved profiles with a new scan, and recover from a reviewed backup.

The verified source is `Thankyou-Cheems/WinstyleS`, local baseline `ce70fef` on main.
The original checkout has an untracked `.review/` directory; leave it untouched.
The baseline already has six scanner categories, asset export, CLI diff/inspect,
JSONC handling, administrator/restore/backup checks, and itemized dry-run plans.
Historical Tauri/acrylic commits date to January 2026, while the current supported
UI is a plain browser frontend backed by Python. Reuse that seam first.

No earlier modern redesign session was recovered: personal-context lookup was
unavailable. Local Git history is the design evidence. A read-only remote check confirmed
main at `ce70fefd7758bbb0ac73d4eba22a84ef6684dd66`; it is the only remote branch.
The old Phase A–E database mostly records closed work, so it is not a new roadmap.

## First slice

Make the existing empty import-preview card useful. Both browser runtime modes
now return the engine's structured preview. The card shows totals, operation,
source target, risks, administrator flags, and skip reasons. Search/category/risk
filters help review long plans. Source changes invalidate browser review;
starting import requires a successful preview. Apply remains a separate action.

Package-controlled strings are escaped, and raw JSON remains inspectable. The
package's recorded path is labeled as such because asset relocation and adapters
may choose a different destination. Preview is not a target-machine compatibility
check. This first slice did not yet provide selective import.

Scope: frontend import markup/styles/module, API preview dispatch, regression
coverage, and the documents describing this workflow. The engine, package format,
apply adapters, account handling, and runtime stack remain reusable.

## Useful integrations

| Integration | Local profile value | Current scope and next boundary |
|---|---|---|
| Windows appearance | Theme/colors, wallpaper/cursor resources, fonts | Existing scanners. Separate writable settings from inventory/Spotlight metadata and check asset portability. |
| Windows Terminal | Fonts, color schemes and selected preferences | Existing JSONC adapter. Stable/preview/unpackaged locations differ; machine paths and dynamic profiles need review. |
| PowerShell / Oh My Posh | Prompt appearance and selected local profile configuration | Existing scanning. Script profiles may contain secrets and executable commands; future profiles should make export opt-in and never execute scripts during inspection. |
| VS Code | Reviewed appearance settings and exported profiles | Existing appearance adapter. Built-in Sync already handles broader editor data; [exported profiles](https://code.visualstudio.com/docs/configure/profiles#share-profiles) can be a later explicit input. Avoid account tokens and automatic extension installation. |
| PowerToys | Keyboard Manager mappings and FancyZones layouts | New integration candidate. Start with explicitly supplied backup/settings fixtures and read-only inspection; schema/version and monitor-specific layout compatibility need validation before write-back. |

## Second slice

The Web workflow now compares package targets with the current scanner output,
shows actual local destinations, and sends explicit selected identities. The
engine enforces eligibility and the package/current review digest, uses an immutable
package snapshot, and checks drift before writing. No new runtime or provider is
needed. Settings with unavailable old values or resource/script dependencies stay
visible with reasons but cannot be selected.

A local journal records only selected before/after values; failure triggers reverse
restoration of touched settings. The response contains a recovery receipt, and the
UI offers explicit recovery of its latest import. Recovery stops on conflicting
current values. A real Terminal adapter test changes one setting in a temporary
file and restores it while retaining unselected preferences. No live user apply
was used to verify this work. See [behavior](behavior.md) for concurrency and
cross-session limitations.

The local API now requires a temporary index-issued session and validates Host,
Origin and JSON requests. Build and release wait for the reusable CI matrix.
These address the two baseline risks observed in review; neither proves elevated
Windows apply. PowerToys read-only fixture inspection is the next provider candidate
after users review this bounded workflow. Independent drift monitoring remains future work.

## Alternatives and official evidence

UniGetUI manages discovery, updates and package lists/bundles. Keep app installation
there; borrow the clear list/detail/operation-review interaction, not its code or
brand. Its current official site is [Devolutions](https://devolutions.net/unigetui/).
The [previous maintainer page](https://www.marticliment.com/unigetui/) confirms the
maintenance transfer.

[Windows Backup](https://support.microsoft.com/en-us/windows/experience/backup-recovery/back-up-and-restore-with-windows-backup)
includes personalization such as wallpaper, colors, themes, and Start layout. Its
consumer workflow uses a personal Microsoft account; personalization requires
OneDrive sign-in and available storage. This is a cloud restore workflow, not
a documented arbitrary local profile-export API. WinstyleS reads its own
supported local settings instead of claiming access to the account backup.

[Terminal configuration](https://learn.microsoft.com/en-us/windows/terminal/install#configuration)
is a local settings.json, with stable, preview and unpackaged locations; generated
defaults are not an export source. Configuration may contain command lines and
machine-specific paths, so exporting the entire file is not automatically portable.

[PowerToys](https://learn.microsoft.com/en-us/windows/powertoys/general#back-up--restore)
has its own settings backup/restore location. Official support for backups is
not a blanket stable schema contract for every module or monitor layout.

[VS Code Settings Sync](https://code.visualstudio.com/docs/configure/settings-sync)
uses Microsoft/GitHub sign-in and a dedicated backend, excludes machine-scoped
settings by default, and does not synchronize workspace tasks. WinstyleS should
complement this with reviewed local data, not harvest sync credentials or claim
the full cloud account can be exported.

## Documentation cleanup

Applied [Matt Pocock's writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
and [AGENTS.md guide](https://www.aihero.dev/a-complete-guide-to-agents-md): keep
startup context small, put domain detail behind a trigger-specific link, group
related caveats, use observable completion criteria, and remove duplicate/stale
facts that are cheap to obtain from the repository itself.

Removed the four numbered spec documents and their traceability-only test;
merged useful runtime behavior and test pointers into `behavior.md`. Kept the
actual behavior tests. Removed the spec-adoption ADR/change scaffold, superseded
Phase framework stub, duplicate technical reference, empty design file, stale
Ruff output, and generated healthcare/app-store design master. None establishes
a current user requirement. Git at `ce70fef` retains all removed tracked material.
Rewrote AGENTS/CONTRIBUTING/README around purpose, operations and specific checks;
removed implicit mandatory push and the hardcoded external Beads workflow.

License and historical backlog were preserved. The first slice added no new write
endpoint. The second added separate reviewed import/recovery endpoints and the
local request checks above; this is still not a multi-user service design.
