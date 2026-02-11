from pathlib import Path

from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.wallpaper import WallpaperScanner


def test_wallpaper_scanner_collects_desktop_and_lockscreen_fields(
    tmp_path: Path, monkeypatch
) -> None:
    app_data = tmp_path / "appdata"
    local_app_data = tmp_path / "localappdata"
    themes_dir = app_data / "Microsoft" / "Windows" / "Themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    transcoded = themes_dir / "TranscodedWallpaper"
    transcoded.write_bytes(b"desktop-transcoded")

    desktop_image = tmp_path / "desktop.jpg"
    desktop_image.write_bytes(b"desktop")
    lockscreen_image = tmp_path / "lockscreen.jpg"
    lockscreen_image.write_bytes(b"lockscreen")

    spotlight_assets = (
        local_app_data
        / "Packages"
        / "Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy"
        / "LocalState"
        / "Assets"
    )
    spotlight_assets.mkdir(parents=True, exist_ok=True)
    (spotlight_assets / "asset_big").write_bytes(b"x" * (120 * 1024))
    (spotlight_assets / "asset_small").write_bytes(b"x" * 1024)

    monkeypatch.setenv("APPDATA", str(app_data))
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    registry = MockRegistryAdapter(
        {
            r"HKCU\Control Panel\Desktop": {
                "Wallpaper": str(desktop_image),
                "WallpaperStyle": "10",
                "TileWallpaper": "0",
            },
            r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization": {
                "LockScreenImage": str(lockscreen_image),
            },
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager": {
                "RotatingLockScreenEnabled": 1,
                "RotatingLockScreenOverlayEnabled": "1",
            },
        }
    )

    scanner = WallpaperScanner(registry, WindowsFileSystemAdapter())
    items = scanner.scan()
    by_key = {item.key: item for item in items}

    assert by_key["wallpaper.path"].metadata["surface"] == "desktop"
    assert by_key["wallpaper.lockscreen.path"].metadata["surface"] == "lockscreen"
    assert by_key["wallpaper.lockscreen.spotlightEnabled"].current_value is True
    assert by_key["wallpaper.lockscreen.spotlightOverlayEnabled"].current_value is True
    assert by_key["wallpaper.lockscreen.spotlightAssetCount"].current_value == 1
