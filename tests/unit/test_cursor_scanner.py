from pathlib import Path

from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.cursor import CursorScanner


def test_cursor_scanner_normalizes_path_and_collects_size(tmp_path: Path, monkeypatch) -> None:
    system_root = tmp_path / "windows"
    cursors_dir = system_root / "cursors"
    cursors_dir.mkdir(parents=True, exist_ok=True)
    arrow_file = cursors_dir / "aero_arrow.cur"
    arrow_file.write_bytes(b"cursor")

    monkeypatch.setenv("SystemRoot", str(system_root))
    registry = MockRegistryAdapter(
        {
            r"HKCU\Control Panel\Cursors": {
                "": "Windows Default",
                "Arrow": r"%SystemRoot%\cursors\aero_arrow.cur",
                "CursorBaseSize": "48",
            }
        }
    )

    scanner = CursorScanner(registry, WindowsFileSystemAdapter())
    items = scanner.scan()
    by_key = {item.key: item for item in items}

    assert by_key["cursor.size"].current_value == 48
    assert by_key["cursor.arrow"].current_value == str(arrow_file)
    assert by_key["cursor.arrow"].metadata["raw_value"] == r"%SystemRoot%\cursors\aero_arrow.cur"
    assert by_key["cursor.arrow"].associated_files


def test_cursor_scanner_apply_updates_cursor_size() -> None:
    registry = MockRegistryAdapter({r"HKCU\Control Panel\Cursors": {"CursorBaseSize": 32}})
    scanner = CursorScanner(registry, WindowsFileSystemAdapter())

    item = scanner.scan()
    cursor_size_item = next(i for i in item if i.key == "cursor.size")
    cursor_size_item = cursor_size_item.model_copy(update={"current_value": 64})

    assert scanner.apply(cursor_size_item) is True
    value, _ = registry.get_value(r"HKCU\Control Panel\Cursors", "CursorBaseSize")
    assert value == 64
