import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from winstyles.core.engine import StyleEngine
from winstyles.core.import_review import ReviewError, item_id
from winstyles.domain.models import AssociatedFile, ScannedItem, ScanResult
from winstyles.domain.types import AssetType, SourceType
from winstyles.plugins.base import BaseScanner


class FixtureScanner(BaseScanner):
    def __init__(self):
        self.values = {"one": 1, "two": 1, "other": 9}
        self.writes = []
        self.fail_key = None
        self.fail_restore = False

    @property
    def id(self):
        return "fixture"

    @property
    def name(self):
        return "Fixture"

    @property
    def category(self):
        return "theme"

    def scan(self):
        return [
            ScannedItem(
                category="theme",
                key=key,
                current_value=value,
                source_type=SourceType.REGISTRY,
                source_path=f"HKCU\\Fixture\\{key}",
            )
            for key, value in self.values.items()
        ]

    def apply(self, item):
        self.writes.append((item.key, item.current_value, item.source_path))
        if self.fail_restore and item.current_value == 1:
            return False
        self.values[item.key] = item.current_value
        return not (item.key == self.fail_key and item.current_value != 1)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    scanner = FixtureScanner()
    engine = StyleEngine()
    engine._scanners = [scanner]
    monkeypatch.setattr(engine, "_create_restore_point_or_error", lambda total: None)

    def backup(scan):
        path = tmp_path / "backup.zip"
        path.write_bytes(b"fixture backup")
        return path

    monkeypatch.setattr(engine, "_create_pre_import_backup", backup)
    path = tmp_path / "profile.zip"
    targets = [
        item.model_copy(update={"current_value": value})
        for item, value in zip(scanner.scan(), [2, 3, 8], strict=True)
    ]
    write_package(path, targets)
    return engine, scanner, path, targets


def write_package(path, items, manifest=None, extra=None):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("scan.json", ScanResult(items=items).model_dump_json())
        if manifest is not None:
            archive.writestr("manifest.json", json.dumps(manifest))
        if extra:
            archive.writestr(extra, b"malicious fixture")


def test_current_target_preview_and_selected_scope(setup):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    assert preview["dry_run_plan"][0]["before"] == 1
    assert preview["dry_run_plan"][0]["after"] == 2
    assert scanner.writes == []
    result = engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    assert result["selected"] == 1
    assert scanner.values == {"one": 2, "two": 1, "other": 9}
    journal = json.loads(Path(result["journal_path"]).read_text(encoding="utf-8"))
    assert [entry["before"]["key"] for entry in journal["items"]] == ["one"]


@pytest.mark.parametrize("selection", [[], ["unknown"], ["duplicate", "duplicate"], "all", None])
def test_invalid_selection_never_writes(setup, selection):
    engine, scanner, path, _ = setup
    preview = engine.preview_import(path)
    with pytest.raises(ReviewError, match="Select|Selection|Duplicate"):
        engine.apply_reviewed_import(path, selection, preview["review_digest"])
    assert scanner.writes == []


def test_readonly_dependencies_missing_and_unchanged_are_skipped(setup):
    engine, scanner, path, targets = setup
    targets[0].metadata["readonly"] = True
    targets[1].associated_files = [
        AssociatedFile(type=AssetType.FONT, name="fixture.ttf", path="C:/missing.ttf")
    ]
    targets[2].current_value = 9
    missing = targets[0].model_copy(update={"key": "missing", "metadata": {}})
    write_package(path, [*targets, missing])
    preview = engine.preview_import(path)
    assert not any(item["selectable"] for item in preview["dry_run_plan"])
    assert all(item["reason"] for item in preview["dry_run_plan"])
    with pytest.raises(ReviewError):
        engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    assert scanner.writes == []


@pytest.mark.parametrize("extra", ["../outside", "/absolute", "C:/evil", "assets/../../evil"])
def test_malicious_members_are_rejected_before_scan(setup, extra):
    engine, scanner, path, targets = setup
    write_package(path, targets, extra=extra)
    with pytest.raises(ReviewError) as error:
        engine.preview_import(path)
    assert error.value.code == "unsafe_zip"
    assert scanner.writes == []


@pytest.mark.parametrize("version", ["2.0.0", "unknown", None])
def test_unknown_schema_is_rejected(setup, version):
    engine, scanner, path, targets = setup
    write_package(path, targets, manifest={"$schema": version})
    with pytest.raises(ReviewError) as error:
        engine.preview_import(path)
    assert error.value.code == "unsupported_schema"
    assert scanner.writes == []


def test_duplicate_identities_are_rejected(setup):
    engine, _, path, targets = setup
    write_package(path, [targets[0], targets[0]])
    with pytest.raises(ReviewError) as error:
        engine.preview_import(path)
    assert error.value.code == "ambiguous_items"


@pytest.mark.parametrize("change", ["package", "current"])
def test_stale_review_cannot_apply(setup, change):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    if change == "package":
        targets[0].current_value = 77
        write_package(path, targets)
    else:
        scanner.values["one"] = 4
    with pytest.raises(ReviewError) as error:
        engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    assert error.value.code == "review_stale"
    assert scanner.writes == []


def test_package_change_after_validation_cannot_change_snapshot(setup, monkeypatch):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)

    def replace_package(scan, create_restore_point, audit):
        targets[0].current_value = 77
        write_package(path, targets)
        return None, path.parent / "backup.zip"

    monkeypatch.setattr(engine, "_prepare_import_apply", replace_package)
    engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    assert scanner.values["one"] == 2


def test_untrusted_source_is_replaced_by_local_target(setup):
    engine, scanner, path, targets = setup
    targets[0].source_path = "HKLM\\Unrelated\\Danger"
    write_package(path, targets)
    preview = engine.preview_import(path)
    engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    assert scanner.writes[0][2] == "HKCU\\Fixture\\one"


def test_partial_failure_restores_only_touched_selection(setup):
    engine, scanner, path, targets = setup
    scanner.fail_key = "two"
    preview = engine.preview_import(path)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    assert result["error_code"] == "reviewed_apply_failed"
    assert result["recovery_status"] == "rolled_back"
    assert scanner.values == {"one": 1, "two": 1, "other": 9}
    assert [key for key, _, _ in scanner.writes] == ["one", "two", "two", "one"]


def test_recovery_receipt_and_later_conflicts(setup):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    result = engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    journal = Path(result["journal_path"])
    with pytest.raises(ReviewError) as error:
        engine.recover_reviewed_import(journal, "tampered")
    assert error.value.code == "journal_changed"
    scanner.values["one"] = 10
    with pytest.raises(ReviewError) as error:
        engine.recover_reviewed_import(journal, result["journal_digest"])
    assert error.value.code == "recovery_conflict"
    assert scanner.values["one"] == 10
    scanner.values["one"] = 2
    recovery = engine.recover_reviewed_import(journal, result["journal_digest"])
    assert recovery["recovery_status"] == "restored"
    assert scanner.values["one"] == 1


def test_failed_rollback_keeps_receipt_for_retry(setup):
    engine, scanner, path, targets = setup
    scanner.fail_key = "two"
    scanner.fail_restore = True
    preview = engine.preview_import(path)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    assert result["recovery_status"] == "recovery_required"
    scanner.fail_restore = False
    recovery = engine.recover_reviewed_import(
        Path(result["journal_path"]), result["journal_digest"]
    )
    assert recovery["recovery_status"] == "restored"
    assert scanner.values == {"one": 1, "two": 1, "other": 9}


def test_recovery_rejects_unknown_schema(setup):
    engine, _, path, _ = setup
    raw = json.dumps({"schema_version": "future", "items": []}).encode()
    path.write_bytes(raw)
    with pytest.raises(ReviewError) as error:
        engine.recover_reviewed_import(path, hashlib.sha256(raw).hexdigest())
    assert error.value.code == "unsupported_schema"


def test_elevation_is_checked_only_for_selected_local_targets(setup, monkeypatch):
    engine, scanner, path, targets = setup
    scan = scanner.scan

    def local_scan():
        items = scan()
        items[1].source_path = "HKLM\\Fixture\\two"
        return items

    monkeypatch.setattr(scanner, "scan", local_scan)
    monkeypatch.setattr("winstyles.core.engine.SystemAPI.is_admin", lambda: False)
    preview = engine.preview_import(path)
    assert preview["dry_run_plan"][1]["requires_admin"] is True
    denied = engine.apply_reviewed_import(path, [item_id(targets[1])], preview["review_digest"])
    assert denied["error_code"] == "admin_required"
    assert scanner.writes == []
    engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
    assert scanner.values == {"one": 2, "two": 1, "other": 9}


def test_scanner_failure_during_apply_keeps_receipt_for_safe_retry(setup, monkeypatch):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    scan = scanner.scan

    def changing_scan():
        if scanner.writes:
            raise RuntimeError("fixture read error")
        return scan()

    monkeypatch.setattr(scanner, "scan", changing_scan)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    assert result["error_code"] == "reviewed_apply_failed"
    # Fail closed if the scanner cannot establish whether a foreign value changed.
    assert result["recovery_status"] == "recovery_required"
    assert scanner.values["one"] == 2
    monkeypatch.setattr(scanner, "scan", scan)
    recovery = engine.recover_reviewed_import(
        Path(result["journal_path"]), result["journal_digest"]
    )
    assert recovery["recovery_status"] == "restored"
    assert scanner.values["one"] == 1


def test_real_terminal_adapter_changes_only_selected_setting_and_recovers(tmp_path, monkeypatch):
    from winstyles.infra.filesystem import WindowsFileSystemAdapter
    from winstyles.infra.registry import MockRegistryAdapter
    from winstyles.plugins.terminal import WindowsTerminalScanner

    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "theme": "light",
                "defaultProfile": "profile",
                "profiles": {"defaults": {"opacity": 95}},
            }
        ),
        encoding="utf-8",
    )
    scanner = WindowsTerminalScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    monkeypatch.setattr(scanner, "_find_settings_path", lambda: settings)
    engine = StyleEngine()
    engine._scanners = [scanner]
    monkeypatch.setattr(engine, "_create_restore_point_or_error", lambda total: None)
    monkeypatch.setattr(
        engine, "_create_pre_import_backup", lambda scan: tmp_path / "fixture-backup.zip"
    )
    items = scanner.scan()
    theme = next(item for item in items if item.key == "windowsTerminal.theme")
    theme.current_value = "dark"
    package = tmp_path / "profile.zip"
    write_package(package, items)
    preview = engine.preview_import(package)
    result = engine.apply_reviewed_import(package, [item_id(theme)], preview["review_digest"])
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data == {
        "theme": "dark",
        "defaultProfile": "profile",
        "profiles": {"defaults": {"opacity": 95}},
    }
    engine.recover_reviewed_import(Path(result["journal_path"]), result["journal_digest"])
    assert json.loads(settings.read_text(encoding="utf-8"))["theme"] == "light"


@pytest.mark.parametrize("fail_at", [1, 2, 3])
def test_journal_failure_does_not_leave_a_selected_setting_changed(setup, monkeypatch, fail_at):
    from winstyles.core.import_review import ReviewedImport

    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    save = ReviewedImport._save
    calls = 0

    def fail_once(self, journal_path, journal):
        nonlocal calls
        calls += 1
        if calls == fail_at:
            raise OSError("fixture journal failure")
        return save(self, journal_path, journal)

    monkeypatch.setattr(ReviewedImport, "_save", fail_once)
    if fail_at == 1:
        with pytest.raises(OSError):
            engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
        assert scanner.writes == []
    else:
        result = engine.apply_reviewed_import(path, [item_id(targets[0])], preview["review_digest"])
        assert result["recovery_status"] == "rolled_back"
        assert result["journal_error"] == "fixture journal failure"
    assert scanner.values == {"one": 1, "two": 1, "other": 9}


def test_drift_between_selected_writes_preserves_foreign_change(setup, monkeypatch):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    apply = scanner.apply

    def changing_apply(item):
        success = apply(item)
        if item.key == "one" and item.current_value == 2:
            scanner.values["two"] = 77
        return success

    monkeypatch.setattr(scanner, "apply", changing_apply)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    assert result["recovery_status"] == "rolled_back"
    assert scanner.values == {"one": 1, "two": 77, "other": 9}
    assert all(key != "two" for key, _, _ in scanner.writes)


def test_drift_during_recovery_stops_before_overwriting_foreign_change(setup, monkeypatch):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    apply = scanner.apply

    def changing_apply(item):
        success = apply(item)
        if item.key == "two" and item.current_value == 1:
            scanner.values["one"] = 77
        return success

    monkeypatch.setattr(scanner, "apply", changing_apply)
    recovery = engine.recover_reviewed_import(
        Path(result["journal_path"]), result["journal_digest"]
    )
    assert recovery["error_code"] == "recovery_conflict"
    assert recovery["journal_digest"] != result["journal_digest"]
    assert scanner.values == {"one": 77, "two": 1, "other": 9}


def test_failure_rollback_does_not_overwrite_foreign_change(setup, monkeypatch):
    engine, scanner, path, targets = setup
    scanner.fail_key = "two"
    preview = engine.preview_import(path)
    apply = scanner.apply

    def changing_apply(item):
        success = apply(item)
        if item.key == "two" and item.current_value == 3:
            scanner.values["one"] = 77
        return success

    monkeypatch.setattr(scanner, "apply", changing_apply)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    assert result["recovery_status"] == "recovery_required"
    assert scanner.values == {"one": 77, "two": 1, "other": 9}
    assert [key for key, _, _ in scanner.writes] == ["one", "two", "two"]


def test_read_failure_after_partial_recovery_returns_updated_receipt(setup, monkeypatch):
    engine, scanner, path, targets = setup
    preview = engine.preview_import(path)
    result = engine.apply_reviewed_import(
        path, [item_id(item) for item in targets[:2]], preview["review_digest"]
    )
    scan = scanner.scan
    apply = scanner.apply

    def breaking_apply(item):
        success = apply(item)
        if item.key == "two" and item.current_value == 1:
            monkeypatch.setattr(scanner, "scan", lambda: (_ for _ in ()).throw(OSError("fixture")))
        return success

    monkeypatch.setattr(scanner, "apply", breaking_apply)
    recovery = engine.recover_reviewed_import(
        Path(result["journal_path"]), result["journal_digest"]
    )
    assert recovery["error_code"] == "current_scan_failed"
    assert recovery["journal_digest"] != result["journal_digest"]
    monkeypatch.setattr(scanner, "scan", scan)
    monkeypatch.setattr(scanner, "apply", apply)
    retry = engine.recover_reviewed_import(
        Path(recovery["journal_path"]), recovery["journal_digest"]
    )
    assert retry["recovery_status"] == "restored"
