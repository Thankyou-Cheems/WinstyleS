import json
import zipfile
from pathlib import Path

from pytest import MonkeyPatch

from winstyles.core.engine import StyleEngine
from winstyles.domain.models import AssociatedFile, ScannedItem, ScanResult
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


class _DummyScanner(BaseScanner):
    def __init__(self, category: str, prefix: str) -> None:
        self._category = category
        self._prefix = prefix
        self.applied: list[str] = []
        self.applied_items: list[ScannedItem] = []

    @property
    def id(self) -> str:
        return f"dummy_{self._category}"

    @property
    def name(self) -> str:
        return "Dummy Scanner"

    @property
    def category(self) -> str:
        return self._category

    def scan(self) -> list[ScannedItem]:
        return []

    def supports_item(self, item: ScannedItem) -> bool:
        return item.key.startswith(self._prefix)

    def apply(self, item: ScannedItem) -> bool:
        self.applied.append(item.key)
        self.applied_items.append(item)
        return True


def _write_scan_package(path: Path, items: list[ScannedItem]) -> None:
    scan = ScanResult(items=items, summary={}, os_version="", duration_ms=None)
    (path / "scan.json").write_text(
        json.dumps(scan.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _scan_json(items: list[ScannedItem], scan_id: str = "202602100001") -> str:
    scan = ScanResult(scan_id=scan_id, items=items, summary={}, os_version="", duration_ms=None)
    return json.dumps(scan.model_dump(mode="json"), ensure_ascii=False, indent=2)


def test_import_routes_items_to_scanner_by_supports_item(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

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


def test_import_skips_readonly_items(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

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


def test_import_aborts_admin_required_items_without_admin_on_windows(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir(parents=True, exist_ok=True)

    item = ScannedItem(
        category="fonts",
        key="fontSubstitutes.Segoe UI",
        current_value="Maple Mono",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path="HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes",
    )
    _write_scan_package(package_dir, [item])

    scanner = _DummyScanner("fonts", "fontSubstitutes.")
    engine = StyleEngine()
    engine._scanners = [scanner]

    monkeypatch.setattr("winstyles.core.engine.platform.system", lambda: "Windows")
    monkeypatch.setattr("winstyles.core.engine.SystemAPI.is_admin", lambda: False)

    summary = engine.import_package(package_dir, dry_run=False, create_restore_point=False)

    assert summary["aborted"] is True
    assert summary["error_code"] == "admin_required"
    assert summary["applied"] == 0
    assert summary["skipped"] == 1
    assert scanner.applied == []
    assert Path(summary["import_log_path"]).exists()


def test_import_writes_pre_import_backup_and_import_log(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    package_dir = tmp_path / "pkg"
    package_dir.mkdir(parents=True, exist_ok=True)

    item = ScannedItem(
        category="terminal",
        key="windowsTerminal.theme",
        current_value="One Half Dark",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path="settings.json",
    )
    _write_scan_package(package_dir, [item])

    scanner = _DummyScanner("terminal", "windowsTerminal.")
    engine = StyleEngine()
    engine._scanners = [scanner]

    summary = engine.import_package(package_dir, dry_run=False, create_restore_point=False)

    backup_path = Path(summary["pre_import_backup_path"])
    log_path = Path(summary["import_log_path"])
    assert summary["applied"] == 1
    assert backup_path.exists()
    assert log_path.exists()

    with zipfile.ZipFile(backup_path, "r") as zip_ref:
        assert "scan.json" in zip_ref.namelist()

    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["result"]["pre_import_backup_path"] == str(backup_path)
    assert {step["name"] for step in log["steps"]} >= {
        "load_scan",
        "admin_check",
        "restore_point",
        "pre_import_backup",
        "resolve_assets",
        "apply_items",
    }
    assert log["items"][0]["key"] == "windowsTerminal.theme"
    assert log["items"][0]["status"] == "applied"


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


def test_import_dry_run_does_not_resolve_assets(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    package_dir = tmp_path / "pkg"
    (package_dir / "assets" / "wallpaper").mkdir(parents=True)
    (package_dir / "assets" / "wallpaper" / "wall.jpg").write_bytes(b"wall")

    item = ScannedItem(
        category="wallpaper",
        key="wallpaper.path",
        current_value=r"C:\missing\wall.jpg",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path=r"HKCU\Control Panel\Desktop\Wallpaper",
        associated_files=[
            AssociatedFile(
                type=AssetType.IMAGE,
                name="wall.jpg",
                path=r"C:\missing\wall.jpg",
                exists=True,
                size_bytes=None,
                sha256=None,
            )
        ],
    )
    _write_scan_package(package_dir, [item])

    scanner = _DummyScanner("wallpaper", "wallpaper.")
    engine = StyleEngine()
    engine._scanners = [scanner]

    summary = engine.import_package(package_dir, dry_run=True, create_restore_point=False)

    assert summary["would_apply"] == 1
    assert scanner.applied == []
    assert not (home / ".winstyles").exists()


def test_import_zip_dry_run_does_not_resolve_assets(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    item = ScannedItem(
        category="wallpaper",
        key="wallpaper.path",
        current_value=r"C:\missing\wall.jpg",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path=r"HKCU\Control Panel\Desktop\Wallpaper",
        associated_files=[
            AssociatedFile(
                type=AssetType.IMAGE,
                name="wall.jpg",
                path=r"C:\missing\wall.jpg",
                exists=True,
                size_bytes=None,
                sha256=None,
            )
        ],
    )
    zip_path = tmp_path / "pkg.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        zip_ref.writestr("scan.json", _scan_json([item]))
        zip_ref.writestr("assets/wallpaper/wall.jpg", b"wall")

    scanner = _DummyScanner("wallpaper", "wallpaper.")
    engine = StyleEngine()
    engine._scanners = [scanner]

    summary = engine.import_package(zip_path, dry_run=True, create_restore_point=False)

    assert summary["would_apply"] == 1
    assert scanner.applied == []
    assert not (home / ".winstyles").exists()


def test_import_aborts_when_restore_point_creation_fails(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir(parents=True, exist_ok=True)

    item = ScannedItem(
        category="fonts",
        key="cleartype.enabled",
        current_value=True,
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path="HKCU\\Control Panel\\Desktop\\FontSmoothing",
    )
    _write_scan_package(package_dir, [item])

    class _FailingRestorePointManager:
        def create_restore_point(self) -> tuple[bool, int]:
            return False, 0

    monkeypatch.setattr("winstyles.core.engine.RestorePointManager", _FailingRestorePointManager)

    font_scanner = _DummyScanner("fonts", "")
    engine = StyleEngine()
    engine._scanners = [font_scanner]

    summary = engine.import_package(package_dir, dry_run=False, create_restore_point=True)

    assert summary["aborted"] is True
    assert summary["error_code"] == "restore_point_failed"
    assert summary["applied"] == 0
    assert summary["skipped"] == 1
    assert font_scanner.applied == []


def test_import_zip_rejects_path_traversal(tmp_path: Path) -> None:
    zip_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        zip_ref.writestr("scan.json", _scan_json([]))
        zip_ref.writestr("../evil.txt", b"bad")

    engine = StyleEngine()
    engine._scanners = []

    summary = engine.import_package(zip_path, dry_run=False, create_restore_point=False)

    assert summary["aborted"] is True
    assert summary["error_code"] == "unsafe_zip"
    assert not (tmp_path / "evil.txt").exists()


def test_import_bad_zip_returns_structured_failure(tmp_path: Path) -> None:
    zip_path = tmp_path / "bad.zip"
    zip_path.write_bytes(b"not a zip")

    engine = StyleEngine()
    engine._scanners = []

    summary = engine.import_package(zip_path, dry_run=True, create_restore_point=False)

    assert summary["aborted"] is True
    assert summary["error_code"] == "invalid_zip"


def test_import_zip_missing_scan_returns_structured_failure(tmp_path: Path) -> None:
    zip_path = tmp_path / "missing-scan.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        zip_ref.writestr("assets/wallpaper/wall.jpg", b"wall")

    engine = StyleEngine()
    engine._scanners = []

    summary = engine.import_package(zip_path, dry_run=True, create_restore_point=False)

    assert summary["aborted"] is True
    assert summary["error_code"] == "scan_json_missing"


def test_import_zip_apply_resolves_assets(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home)

    item = ScannedItem(
        category="wallpaper",
        key="wallpaper.path",
        current_value=r"C:\missing\wall.jpg",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.REGISTRY,
        source_path=r"HKCU\Control Panel\Desktop\Wallpaper",
        associated_files=[
            AssociatedFile(
                type=AssetType.IMAGE,
                name="wall.jpg",
                path=r"C:\missing\wall.jpg",
                exists=True,
                size_bytes=None,
                sha256=None,
            )
        ],
    )
    zip_path = tmp_path / "pkg.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        zip_ref.writestr("scan.json", _scan_json([item]))
        zip_ref.writestr("assets/wallpaper/wall.jpg", b"wall")

    scanner = _DummyScanner("wallpaper", "wallpaper.")
    engine = StyleEngine()
    engine._scanners = [scanner]

    summary = engine.import_package(zip_path, dry_run=False, create_restore_point=False)

    target = home / ".winstyles" / "imported_assets" / "202602100001" / "wallpaper" / "wall.jpg"
    assert summary["applied"] == 1
    assert scanner.applied == ["wallpaper.path"]
    assert scanner.applied_items[0].current_value == str(target)
    assert target.read_bytes() == b"wall"
