from pathlib import Path

from winstyles.core.engine import StyleEngine
from winstyles.domain.models import AssociatedFile, ScannedItem, ScanResult
from winstyles.domain.types import AssetType, ChangeType, SourceType


def _build_scan_result(font_path: Path, image_path: Path) -> ScanResult:
    return ScanResult(
        items=[
            ScannedItem(
                category="fonts",
                key="MS Shell Dlg",
                current_value="Test Font",
                default_value=None,
                change_type=ChangeType.MODIFIED,
                source_type=SourceType.REGISTRY,
                source_path="HKLM\\test",
                associated_files=[
                    AssociatedFile(
                        type=AssetType.FONT,
                        name=font_path.name,
                        path=str(font_path),
                        exists=True,
                    )
                ],
            ),
            ScannedItem(
                category="wallpaper",
                key="wallpaper.path",
                current_value=str(image_path),
                default_value=None,
                change_type=ChangeType.MODIFIED,
                source_type=SourceType.FILE,
                source_path=str(image_path),
                associated_files=[
                    AssociatedFile(
                        type=AssetType.IMAGE,
                        name=image_path.name,
                        path=str(image_path),
                        exists=True,
                    )
                ],
            ),
        ]
    )


def test_export_assets_skips_font_files_when_disabled(tmp_path) -> None:
    font_path = tmp_path / "TestFont.ttf"
    image_path = tmp_path / "wallpaper.jpg"
    font_path.write_bytes(b"font")
    image_path.write_bytes(b"image")

    scan_result = _build_scan_result(font_path, image_path)
    assets_dir = tmp_path / "assets_off"

    engine = StyleEngine.__new__(StyleEngine)
    engine._export_assets(scan_result, assets_dir, include_font_files=False)

    assert not (assets_dir / "fonts" / font_path.name).exists()
    assert (assets_dir / "wallpaper" / image_path.name).exists()


def test_export_assets_includes_font_files_when_enabled(tmp_path) -> None:
    font_path = tmp_path / "TestFont.ttf"
    image_path = tmp_path / "wallpaper.jpg"
    font_path.write_bytes(b"font")
    image_path.write_bytes(b"image")

    scan_result = _build_scan_result(font_path, image_path)
    assets_dir = tmp_path / "assets_on"

    engine = StyleEngine.__new__(StyleEngine)
    engine._export_assets(scan_result, assets_dir, include_font_files=True)

    assert (assets_dir / "fonts" / font_path.name).exists()
    assert (assets_dir / "wallpaper" / image_path.name).exists()
