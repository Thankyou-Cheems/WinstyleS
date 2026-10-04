"""Settings-only reviewed imports: immutable packages, explicit scope, recovery receipts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from winstyles.core.exceptions import PackageError
from winstyles.domain.models import ScannedItem, ScanResult
from winstyles.domain.types import AssetType

if TYPE_CHECKING:
    from winstyles.core.engine import StyleEngine


class ReviewError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def item_id(item: ScannedItem) -> str:
    return digest([item.category, item.key])


def value_of(item: ScannedItem) -> Any:
    return item.metadata.get("raw_value", item.current_value)


class ReviewedImport:
    def __init__(self, engine: StyleEngine) -> None:
        self.engine = engine

    def _load(self, path: Path) -> tuple[ScanResult, str]:
        if path.suffix.lower() != ".zip":
            raise ReviewError("review_requires_zip", "Reviewed import requires a zip package")
        if path.stat().st_size > 32 * 1024 * 1024:
            raise ReviewError("package_too_large", "Reviewed package exceeds 32 MiB")
        with path.open("rb") as handle:
            raw = handle.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024:
            raise ReviewError("package_too_large", "Reviewed package exceeds 32 MiB")
        try:
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                self.engine._validate_zip_members(archive)
                names = archive.namelist()
                if len(names) != len(set(names)):
                    raise ReviewError("ambiguous_package", "Duplicate zip member names")
                if sum(info.file_size for info in archive.infolist()) > 128 * 1024 * 1024:
                    raise ReviewError("package_too_large", "Expanded package exceeds 128 MiB")
                if "manifest.json" in names:
                    manifest = json.loads(archive.read("manifest.json"))
                    if not isinstance(manifest, dict):
                        raise ReviewError("invalid_schema", "Manifest must be an object")
                    self._schema(manifest)
                data = json.loads(archive.read("scan.json"))
                if not isinstance(data, dict):
                    raise ReviewError("invalid_schema", "Scan must be an object")
                self._schema(data)
                scan = ScanResult.model_validate(data)
        except PackageError as exc:
            raise ReviewError("unsafe_zip", str(exc)) from exc
        except (KeyError, zipfile.BadZipFile, json.JSONDecodeError, UnicodeError) as exc:
            raise ReviewError("invalid_package", "Invalid scan package") from exc
        ids = [item_id(item) for item in scan.items]
        if len(ids) != len(set(ids)):
            raise ReviewError("ambiguous_items", "Duplicate category/key identities")
        return scan, hashlib.sha256(raw).hexdigest()

    def _schema(self, data: dict[str, Any]) -> None:
        for key in ("$schema", "schema_version"):
            if key in data and data[key] != "1.0.0":
                raise ReviewError("unsupported_schema", "Only schema 1.0.0 is supported")

    def _current(self, targets: list[ScannedItem]) -> dict[str, ScannedItem]:
        scanners = {
            scanner.id: scanner
            for item in targets
            if (scanner := self.engine._find_scanner_for_item(item)) is not None
        }
        current: dict[str, ScannedItem] = {}
        try:
            for scanner in scanners.values():
                for item in scanner.scan():
                    identity = item_id(item)
                    if identity in current:
                        raise ReviewError(
                            "ambiguous_current", "Local settings have duplicate identities"
                        )
                    current[identity] = item
        except ReviewError:
            raise
        except Exception as exc:
            raise ReviewError(
                "current_scan_failed", "Could not read current configuration"
            ) from exc
        return current

    def _inspect(
        self, path: Path
    ) -> tuple[dict[str, Any], list[ScannedItem], dict[str, ScannedItem]]:
        target, package_hash = self._load(path)
        current = self._current(target.items)
        plans = self.engine._build_dry_run_plan(target.items)
        effective: list[ScannedItem] = []
        for item, plan in zip(target.items, plans, strict=True):
            identity = item_id(item)
            before = current.get(identity)
            reason = None
            if plan["action"] != "apply":
                reason = plan["reason"]
            elif before is None:
                reason = "本机缺少可恢复旧值；此阶段不创建新设置"
            elif before.metadata.get("readonly") is True:
                reason = "本机项目只读"
            elif before.source_type != item.source_type:
                reason = "本机与包内来源类型不同"
            elif item.source_type.value == "system_api" or item.key.startswith(
                ("powershell.", "powerShell", "ohMyPosh.")
            ):
                reason = "脚本或系统 API 不属于可撤回设置导入"
            elif item.key in {"wallpaper.path", "wallpaper.transcoded"} or (
                item.key.startswith("cursor.") and item.key not in {"cursor.scheme", "cursor.size"}
            ):
                reason = "资源路径设置需另行迁移依赖；本阶段不复制资源"
            elif any(file.type != AssetType.CONFIG for file in item.associated_files):
                reason = "依赖字体或外观资源；本阶段不复制或安装资源"
            elif value_of(before) == value_of(item):
                reason = "当前值与目标相同"
            if before is not None:
                metadata = dict(before.metadata)
                metadata.pop("raw_value", None)
                if "raw_value" in item.metadata:
                    metadata["raw_value"] = item.metadata["raw_value"]
                applied_item = before.model_copy(
                    update={
                        "current_value": item.current_value,
                        "metadata": metadata,
                        "associated_files": [],
                    }
                )
                if self.engine._find_scanner_for_item(applied_item) is None:
                    reason = "本机目标无法由原扫描器写回"
                effective.append(applied_item)
            else:
                effective.append(item)
            plan.update(
                {
                    "id": identity,
                    "selectable": reason is None,
                    "before": value_of(before) if before else None,
                    "after": value_of(item),
                    "change": (
                        "missing"
                        if before is None
                        else ("unchanged" if value_of(before) == value_of(item) else "modified")
                    ),
                    "package_target": item.source_path,
                    "target": before.source_path if before else "",
                }
            )
            if reason is not None:
                plan.update(
                    {
                        "action": "skip",
                        "operation": "skip",
                        "reason": reason,
                        "requires_admin": False,
                    }
                )
            elif before is not None:
                plan["requires_admin"] = self.engine._item_requires_admin(effective[-1])
        binding = {
            "package": package_hash,
            "current": {key: item.model_dump(mode="json") for key, item in current.items()},
        }
        eligible = sum(entry["selectable"] for entry in plans)
        summary = {
            "total": len(plans),
            "applied": 0,
            "failed": 0,
            "skipped": len(plans),
            "would_apply": eligible,
            "would_skip": len(plans) - eligible,
            "admin_required": any(entry["requires_admin"] for entry in plans),
            "dry_run_plan": plans,
            "risk_summary": self.engine._summarize_risk(plans),
            "review_digest": digest(binding),
            "package_digest": package_hash,
        }
        return summary, effective, current

    def preview(self, path: Path) -> dict[str, Any]:
        return self._inspect(path)[0]

    def apply(
        self,
        path: Path,
        selected_ids: list[str],
        review_digest: str,
        create_restore_point: bool = True,
    ) -> dict[str, Any]:
        summary, effective, current = self._inspect(path)
        if review_digest != summary["review_digest"]:
            raise ReviewError("review_stale", "Package or current settings changed; preview again")
        if (
            not isinstance(selected_ids, list)
            or not selected_ids
            or any(not isinstance(key, str) for key in selected_ids)
        ):
            raise ReviewError("invalid_selection", "Select at least one reviewed setting")
        if len(selected_ids) != len(set(selected_ids)):
            raise ReviewError("invalid_selection", "Duplicate selected identities")
        eligible = {entry["id"] for entry in summary["dry_run_plan"] if entry["selectable"]}
        if not set(selected_ids).issubset(eligible):
            raise ReviewError("invalid_selection", "Selection includes unknown or skipped settings")
        chosen = [item for item in effective if item_id(item) in selected_ids]
        scan = ScanResult(
            items=chosen, scan_id=summary["package_digest"][:24], os_version="", duration_ms=None
        )
        audit = self.engine._start_import_audit(path, False, create_restore_point)
        error, backup = self.engine._prepare_import_apply(scan, create_restore_point, audit)
        if error is not None:
            return self.engine._finalize_import_audit(audit, error)
        entries = [
            {
                "before": current[item_id(item)].model_dump(mode="json"),
                "after": item.model_dump(mode="json"),
                "status": "pending",
            }
            for item in chosen
        ]
        journal = {
            "schema_version": "1.0.0",
            "items": entries,
            "status": "prepared",
            "package_digest": summary["package_digest"],
            "review_digest": review_digest,
        }
        journal_path = self.engine._build_import_log_path(audit).with_name("review_journal.json")
        self._save(journal_path, journal)
        failed = False
        journal_error = None
        try:
            for item, entry in zip(chosen, entries, strict=True):
                now = self._current([item]).get(item_id(item))
                if (
                    now is None
                    or now.source_path != current[item_id(item)].source_path
                    or value_of(now) != value_of(current[item_id(item)])
                ):
                    failed = True
                    entry["error"] = "current_changed_before_write"
                    break
                entry["status"] = "attempting"
                self._save(journal_path, journal)
                scanner = self.engine._find_scanner_for_item(item)
                try:
                    success = scanner is not None and scanner.apply(item)
                except Exception:
                    success = False
                entry["status"] = "applied" if success else "failed"
                self._save(journal_path, journal)
                if not success:
                    failed = True
                    break
        except ReviewError as exc:
            failed = True
            entry["error"] = exc.code
        except OSError as exc:
            failed = True
            journal_error = str(exc)
        if failed:
            for entry in reversed(entries):
                if entry["status"] not in {"applied", "failed", "attempting"}:
                    continue
                original = ScannedItem.model_validate(entry["before"])
                scanner = self.engine._find_scanner_for_item(original)
                try:
                    now = self._current([original]).get(item_id(original))
                    target = ScannedItem.model_validate(entry["after"])
                    if (
                        now is None
                        or now.source_path != original.source_path
                        or value_of(now) not in [value_of(original), value_of(target)]
                    ):
                        entry["error"] = "rollback_conflict"
                        restored = False
                    else:
                        restored = scanner is not None and scanner.apply(original)
                except ReviewError as exc:
                    entry["error"] = exc.code
                    restored = False
                except Exception:
                    restored = False
                entry["status"] = "restored" if restored else "restore_failed"
                try:
                    self._save(journal_path, journal)
                except OSError as exc:
                    journal_error = str(exc)
        journal["status"] = "rolled_back" if failed else "applied"
        if any(entry["status"] == "restore_failed" for entry in entries):
            journal["status"] = "recovery_required"
        try:
            self._save(journal_path, journal)
        except OSError as exc:
            journal_error = str(exc)
        result = {
            "total": len(summary["dry_run_plan"]),
            "selected": len(chosen),
            "applied": sum(entry["status"] == "applied" for entry in entries),
            "failed": int(failed),
            "skipped": len(summary["dry_run_plan"]) - len(chosen),
            "journal_path": str(journal_path),
            "journal_digest": hashlib.sha256(journal_path.read_bytes()).hexdigest(),
            "recovery_status": journal["status"],
            "pre_import_backup_path": str(backup),
        }
        if journal_error is not None:
            result["journal_error"] = journal_error
        if failed:
            result.update(
                {
                    "error_code": "reviewed_apply_failed",
                    "error": "Apply stopped; inspect recovery status",
                }
            )
        return self.engine._finalize_import_audit(audit, result)

    def _save(self, path: Path, journal: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def recover(self, path: Path, expected_digest: str) -> dict[str, Any]:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_digest:
            raise ReviewError("journal_changed", "Journal differs from the saved receipt")
        journal = json.loads(raw)
        if not isinstance(journal, dict) or journal.get("schema_version") != "1.0.0":
            raise ReviewError("unsupported_schema", "Unsupported recovery journal")
        entries = journal.get("items")
        if not isinstance(entries, list):
            raise ReviewError("invalid_journal", "Journal has no items")
        originals = [ScannedItem.model_validate(entry["before"]) for entry in entries]
        targets = [ScannedItem.model_validate(entry["after"]) for entry in entries]
        current = self._current(originals)
        for original, target, entry in zip(originals, targets, entries, strict=True):
            if item_id(original) != item_id(target):
                raise ReviewError("invalid_journal", "Journal identities differ")
            if entry["status"] in {"pending", "restored"}:
                continue
            now = current.get(item_id(original))
            if (
                now is None
                or now.source_path != original.source_path
                or value_of(now) not in [value_of(original), value_of(target)]
            ):
                raise ReviewError(
                    "recovery_conflict", "Settings changed after import; recovery stopped"
                )
        permission_error = self.engine._admin_check_or_error(
            ScanResult(
                os_version="",
                duration_ms=None,
                items=[
                    original
                    for original, entry in zip(originals, entries, strict=True)
                    if entry["status"] not in {"pending", "restored"}
                ],
            )
        )
        if permission_error is not None:
            return permission_error
        for original, entry in reversed(list(zip(originals, entries, strict=True))):
            if entry["status"] in {"pending", "restored"}:
                continue
            # Check again immediately before each write; another process can drift
            # after the initial conflict check while earlier items are restored.
            try:
                now = self._current([original]).get(item_id(original))
            except ReviewError as exc:
                return {
                    "error_code": exc.code,
                    "error": str(exc),
                    "recovery_status": "recovery_required",
                    "journal_path": str(path),
                    "journal_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            target = ScannedItem.model_validate(entry["after"])
            if (
                now is None
                or now.source_path != original.source_path
                or value_of(now) not in [value_of(original), value_of(target)]
            ):
                journal["status"] = "recovery_required"
                self._save(path, journal)
                return {
                    "error_code": "recovery_conflict",
                    "error": "Settings changed during recovery; recovery stopped",
                    "recovery_status": "recovery_required",
                    "journal_path": str(path),
                    "journal_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            scanner = self.engine._find_scanner_for_item(original)
            try:
                restored = scanner is not None and scanner.apply(original)
            except Exception:
                restored = False
            entry["status"] = "restored" if restored else "restore_failed"
            self._save(path, journal)
        journal["status"] = (
            "restored"
            if all(entry["status"] in {"pending", "restored"} for entry in entries)
            else "recovery_required"
        )
        self._save(path, journal)
        return {
            "recovery_status": journal["status"],
            "journal_path": str(path),
            "journal_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
