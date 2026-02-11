from pathlib import Path

from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.fonts import InstalledFontsScanner


def test_installed_fonts_scanner_collects_fonts_and_opensource_match(
    tmp_path: Path,
    monkeypatch,
) -> None:
    system_root = tmp_path / "windows"
    system_fonts = system_root / "Fonts"
    system_fonts.mkdir(parents=True, exist_ok=True)

    local_app_data = tmp_path / "localappdata"
    user_fonts = local_app_data / "Microsoft" / "Windows" / "Fonts"
    user_fonts.mkdir(parents=True, exist_ok=True)

    machine_font = system_fonts / "MapleMono-Regular.ttf"
    user_font = user_fonts / "CustomUser.ttf"
    machine_font.write_bytes(b"maple")
    user_font.write_bytes(b"user")

    monkeypatch.setenv("SystemRoot", str(system_root))
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    registry = MockRegistryAdapter(
        {
            InstalledFontsScanner.MACHINE_FONTS_REGISTRY_PATH: {
                "Maple Mono (TrueType)": "MapleMono-Regular.ttf",
            },
            InstalledFontsScanner.USER_FONTS_REGISTRY_PATH: {
                "Custom User Font (TrueType)": "CustomUser.ttf",
            },
        }
    )
    scanner = InstalledFontsScanner(registry, WindowsFileSystemAdapter())

    items = scanner.scan()
    installed_items = [item for item in items if item.key.startswith("installed.")]
    assert len(installed_items) == 2

    maple_item = next(item for item in installed_items if "Maple Mono" in item.key)
    assert maple_item.current_value == str(machine_font)
    assert maple_item.associated_files
    assert maple_item.metadata["is_opensource"] is True
    opensource = maple_item.metadata.get("opensource")
    assert isinstance(opensource, dict)
    assert opensource.get("name") == "Maple Mono"


def test_installed_fonts_scanner_collects_cleartype_settings(tmp_path: Path) -> None:
    registry = MockRegistryAdapter(
        {
            InstalledFontsScanner.CLEARTYPE_REGISTRY_PATH: {
                "FontSmoothing": "2",
                "FontSmoothingType": 2,
                "FontSmoothingGamma": "1900",
                "FontSmoothingOrientation": 1,
                "FontSmoothingContrast": "1400",
            }
        }
    )
    scanner = InstalledFontsScanner(registry, WindowsFileSystemAdapter())

    items = scanner.scan()
    by_key = {item.key: item for item in items}

    assert by_key["cleartype.enabled"].current_value is True
    assert by_key["cleartype.mode"].current_value == 2
    assert by_key["cleartype.gamma"].current_value == 1900
    assert by_key["cleartype.orientation"].current_value == 1
    assert by_key["cleartype.contrast"].current_value == 1400
