import json

from winstyles.domain.models import ScannedItem
from winstyles.domain.types import ChangeType, SourceType
from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.terminal import PowerShellProfileScanner, WindowsTerminalScanner


def test_windows_terminal_apply_updates_nested_keys(tmp_path, monkeypatch) -> None:
    package_root = tmp_path / "LocalAppData" / "Packages"
    package_root = package_root / "Microsoft.WindowsTerminal_8wekyb3d8bbwe"
    settings_path = package_root / "LocalState" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps({"profiles": {"defaults": {}}}), encoding="utf-8")

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))

    scanner = WindowsTerminalScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    item = ScannedItem(
        category="terminal",
        key="windowsTerminal.defaults.font.face",
        current_value="Maple Mono",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path=str(settings_path),
    )
    assert scanner.apply(item) is True

    loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    assert loaded["profiles"]["defaults"]["font"]["face"] == "Maple Mono"


def test_powershell_apply_targets_current_user_profile(tmp_path, monkeypatch) -> None:
    user_profile = tmp_path / "userA"
    monkeypatch.setenv("USERPROFILE", str(user_profile))

    scanner = PowerShellProfileScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    item = ScannedItem(
        category="terminal",
        key="powershell.profile.PowerShell",
        current_value="Set-PSReadLineOption -EditMode Windows",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path=r"C:\other-user\Documents\PowerShell\Microsoft.PowerShell_profile.ps1",
    )
    assert scanner.apply(item) is True

    target = user_profile / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    assert target.exists()
    assert "Set-PSReadLineOption" in target.read_text(encoding="utf-8")
