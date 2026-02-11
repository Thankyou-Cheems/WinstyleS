import json
from pathlib import Path

from winstyles.core.engine import StyleEngine
from winstyles.domain.models import ScannedItem, ScanResult
from winstyles.domain.types import ChangeType, SourceType


class _DummyScanner:
    def __init__(self, category: str, prefix: str) -> None:
        self.category = category
        self._prefix = prefix
        self.applied: list[str] = []

    def supports_item(self, item: ScannedItem) -> bool:
        return item.key.startswith(self._prefix)

    def apply(self, item: ScannedItem) -> bool:
        self.applied.append(item.key)
        return True


def _write_scan_package(path: Path, items: list[ScannedItem]) -> None:
    scan = ScanResult(items=items, summary={})
    (path / "scan.json").write_text(
        json.dumps(scan.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_import_routes_items_to_scanner_by_supports_item(tmp_path: Path) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir(parents=True, exist_ok=True)

    terminal_item = ScannedItem(
        category="terminal",
        key="windowsTerminal.theme",
        current_value="One Half Dark",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path="settings.json",
    )
    powershell_item = ScannedItem(
        category="terminal",
        key="powershell.profile.PowerShell",
        current_value="Write-Host test",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path="profile.ps1",
    )
    _write_scan_package(package_dir, [terminal_item, powershell_item])

    wt_scanner = _DummyScanner("terminal", "windowsTerminal.")
    ps_scanner = _DummyScanner("terminal", "powershell.profile.")

    engine = StyleEngine()
    engine._scanners = [wt_scanner, ps_scanner]

    summary = engine.import_package(package_dir, dry_run=False, create_restore_point=False)

    assert summary["applied"] == 2
    assert summary["failed"] == 0
    assert wt_scanner.applied == ["windowsTerminal.theme"]
    assert ps_scanner.applied == ["powershell.profile.PowerShell"]


def test_import_skips_readonly_items(tmp_path: Path) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir(parents=True, exist_ok=True)

    readonly_item = ScannedItem(
        category="fonts",
        key="installed.machine.Maple Mono (TrueType)",
        current_value="C:\\Windows\\Fonts\\MapleMono-Regular.ttf",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path=(
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts\\Maple Mono (TrueType)"
        ),
        metadata={"readonly": True},
    )
    writable_item = ScannedItem(
        category="fonts",
        key="cleartype.enabled",
        current_value=True,
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path="HKCU\\Control Panel\\Desktop\\FontSmoothing",
    )
    _write_scan_package(package_dir, [readonly_item, writable_item])

    font_scanner = _DummyScanner("fonts", "")

    engine = StyleEngine()
    engine._scanners = [font_scanner]

    summary = engine.import_package(package_dir, dry_run=False, create_restore_point=False)

    assert summary["applied"] == 1
    assert summary["skipped"] == 1
    assert summary["failed"] == 0
    assert font_scanner.applied == ["cleartype.enabled"]


def test_import_dry_run_returns_itemized_plan_and_risk(tmp_path: Path) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir(parents=True, exist_ok=True)

    readonly_item = ScannedItem(
        category="fonts",
        key="installed.machine.Maple Mono (TrueType)",
        current_value="C:\\Windows\\Fonts\\MapleMono-Regular.ttf",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path=(
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts\\Maple Mono (TrueType)"
        ),
        metadata={"readonly": True},
    )
    writable_item = ScannedItem(
        category="fonts",
        key="cleartype.enabled",
        current_value=True,
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path="HKCU\\Control Panel\\Desktop\\FontSmoothing",
    )
    unsupported_item = ScannedItem(
        category="fonts",
        key="fontSubstitutes.Segoe UI",
        current_value="Maple Mono",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path="HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes",
    )
    _write_scan_package(package_dir, [readonly_item, writable_item, unsupported_item])

    font_scanner = _DummyScanner("fonts", "cleartype.")
    engine = StyleEngine()
    engine._scanners = [font_scanner]

    summary = engine.import_package(package_dir, dry_run=True, create_restore_point=False)

    assert summary["total"] == 3
    assert summary["applied"] == 0
    assert summary["failed"] == 0
    assert summary["skipped"] == 3
    assert summary["would_apply"] == 1
    assert summary["would_skip"] == 2
    assert font_scanner.applied == []

    plan = summary["dry_run_plan"]
    assert isinstance(plan, list)
    assert len(plan) == 3
    entries = {entry["key"]: entry for entry in plan}

    assert entries["cleartype.enabled"]["action"] == "apply"
    assert entries["cleartype.enabled"]["operation"] == "set_registry_value"
    assert entries["cleartype.enabled"]["risk"] == "high"

    assert entries["installed.machine.Maple Mono (TrueType)"]["action"] == "skip"
    assert entries["installed.machine.Maple Mono (TrueType)"]["operation"] == "skip"
    assert entries["installed.machine.Maple Mono (TrueType)"]["risk"] == "low"

    assert entries["fontSubstitutes.Segoe UI"]["action"] == "skip"
    assert entries["fontSubstitutes.Segoe UI"]["operation"] == "skip"
    assert entries["fontSubstitutes.Segoe UI"]["risk"] == "low"

    risk_summary = summary["risk_summary"]
    assert risk_summary == {"low": 2, "medium": 0, "high": 1}
