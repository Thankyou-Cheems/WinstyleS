import json
from pathlib import Path

from pytest import MonkeyPatch

from winstyles.domain.models import ScannedItem
from winstyles.domain.types import ChangeType, SourceType
from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.vscode import VSCodeScanner


def test_vscode_apply_preserves_url_strings_and_unrelated_keys(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings_path = tmp_path / "AppData" / "Code" / "User" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        """
        {
          // comments should be ignored
          "workbench.colorTheme": "Default Dark Modern",
          "remote.SSH.defaultForwardedPorts": [
            {
              "name": "site",
              "localPort": 3000,
              "remotePort": 3000,
              "protocol": "https://example.test/path",
            },
          ],
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))

    scanner = VSCodeScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    item = ScannedItem(
        category="vscode",
        key="vscode.editor.fontFamily",
        current_value="Maple Mono",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path=str(settings_path),
    )

    assert scanner.apply(item) is True

    loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    assert loaded["editor.fontFamily"] == "Maple Mono"
    assert loaded["workbench.colorTheme"] == "Default Dark Modern"
    assert loaded["remote.SSH.defaultForwardedPorts"][0]["protocol"] == "https://example.test/path"


def test_vscode_apply_does_not_overwrite_invalid_json(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings_path = tmp_path / "AppData" / "Code" / "User" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    original = '{"workbench.colorTheme": '
    settings_path.write_text(original, encoding="utf-8")
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))

    scanner = VSCodeScanner(MockRegistryAdapter(), WindowsFileSystemAdapter())
    item = ScannedItem(
        category="vscode",
        key="vscode.editor.fontFamily",
        current_value="Maple Mono",
        default_value=None,
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path=str(settings_path),
    )

    assert scanner.apply(item) is False
    assert settings_path.read_text(encoding="utf-8") == original
