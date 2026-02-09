from pathlib import Path

from winstyles.core.engine import StyleEngine
from winstyles.domain.models import AssociatedFile, ScannedItem, ScanResult
from winstyles.domain.types import AssetType, ChangeType, SourceType


def test_resolve_import_assets_rewrites_cursor_and_wallpaper_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    package_dir = tmp_path / "package"
    (package_dir / "assets" / "cursor").mkdir(parents=True)
    (package_dir / "assets" / "wallpaper").mkdir(parents=True)
    cursor_asset = package_dir / "assets" / "cursor" / "arrow.cur"
    wallpaper_asset = package_dir / "assets" / "wallpaper" / "wall.jpg"
    cursor_asset.write_bytes(b"cursor")
    wallpaper_asset.write_bytes(b"wall")

    scan_result = ScanResult(
        scan_id="202602100001",
        items=[
            ScannedItem(
                category="cursor",
                key="cursor.arrow",
                current_value=r"C:\old\arrow.cur",
                default_value=None,
                change_type=ChangeType.MODIFIED,
                source_type=SourceType.REGISTRY,
                source_path=r"HKCU\Control Panel\Cursors\Arrow",
                associated_files=[
                    AssociatedFile(
                        type=AssetType.CURSOR,
                        name="arrow.cur",
                        path=r"C:\old\arrow.cur",
                        exists=True,
                    )
                ],
            ),
            ScannedItem(
                category="wallpaper",
                key="wallpaper.path",
                current_value=r"C:\old\wall.jpg",
                default_value=None,
                change_type=ChangeType.MODIFIED,
                source_type=SourceType.REGISTRY,
                source_path=r"HKCU\Control Panel\Desktop\Wallpaper",
                associated_files=[
                    AssociatedFile(
                        type=AssetType.IMAGE,
                        name="wall.jpg",
                        path=r"C:\old\wall.jpg",
                        exists=True,
                    )
                ],
            ),
        ],
    )

    engine = StyleEngine.__new__(StyleEngine)
    resolved = engine._resolve_import_assets(scan_result, package_dir)

    cursor_item = resolved.items[0]
    wallpaper_item = resolved.items[1]
    assert cursor_item.current_value.endswith(r"imported_assets\202602100001\cursor\arrow.cur")
    assert wallpaper_item.current_value.endswith(r"imported_assets\202602100001\wallpaper\wall.jpg")
    assert Path(cursor_item.associated_files[0].path).exists()
    assert Path(wallpaper_item.associated_files[0].path).exists()


def test_find_asset_in_package_supports_hashed_fallback(tmp_path) -> None:
    category_dir = tmp_path / "fonts"
    category_dir.mkdir()
    hashed = category_dir / "maple_123456.ttf"
    hashed.write_bytes(b"font")

    engine = StyleEngine.__new__(StyleEngine)
    found = engine._find_asset_in_package(category_dir, "maple.ttf")
    assert found == hashed
