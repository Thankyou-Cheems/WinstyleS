from pathlib import Path

from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.terminal import OhMyPoshScanner


def test_oh_my_posh_scanner_detects_install_and_theme(tmp_path: Path, monkeypatch) -> None:
    user_profile = tmp_path / "user"
    profile_dir = user_profile / "Documents" / "PowerShell"
    profile_dir.mkdir(parents=True, exist_ok=True)

    theme_file = user_profile / "themes" / "jandedobbeleer.omp.json"
    theme_file.parent.mkdir(parents=True, exist_ok=True)
    theme_file.write_text("{}", encoding="utf-8")

    profile_path = profile_dir / "Microsoft.PowerShell_profile.ps1"
    profile_path.write_text(
        f'oh-my-posh init pwsh --config "{theme_file}" | Invoke-Expression',
        encoding="utf-8",
    )

    exe_path = tmp_path / "oh-my-posh.exe"
    exe_path.write_bytes(b"exe")

    monkeypatch.setenv("USERPROFILE", str(user_profile))
    monkeypatch.setattr("winstyles.plugins.terminal.shutil.which", lambda _: str(exe_path))

    scanner = OhMyPoshScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    items = scanner.scan()
    by_key = {item.key: item for item in items}

    installed_item = by_key["ohMyPosh.installed"]
    assert installed_item.current_value is True
    assert installed_item.metadata["readonly"] is True

    theme_item = by_key["ohMyPosh.theme.PowerShell"]
    assert theme_item.current_value == str(theme_file)
    assert theme_item.associated_files
    assert theme_item.associated_files[0].path == str(theme_file)


def test_oh_my_posh_scanner_handles_absent_installation(tmp_path: Path, monkeypatch) -> None:
    user_profile = tmp_path / "user"
    profile_dir = user_profile / "Documents" / "PowerShell"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "Microsoft.PowerShell_profile.ps1").write_text(
        "Write-Host 'no oh my posh'",
        encoding="utf-8",
    )

    monkeypatch.setenv("USERPROFILE", str(user_profile))
    monkeypatch.setattr("winstyles.plugins.terminal.shutil.which", lambda _: None)

    scanner = OhMyPoshScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    items = scanner.scan()
    keys = {item.key for item in items}

    assert "ohMyPosh.installed" in keys
    installed_item = next(item for item in items if item.key == "ohMyPosh.installed")
    assert installed_item.current_value is False
    assert all(not key.startswith("ohMyPosh.theme.") for key in keys)
