"""
WallpaperScanner - 壁纸扫描器

扫描:
- 桌面壁纸路径
- 壁纸样式
- 壁纸实际文件
"""

import os
import shutil
from pathlib import Path

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


class WallpaperScanner(BaseScanner):
    """
    壁纸扫描器

    扫描 HKCU\\Control Panel\\Desktop 中的壁纸设置
    """

    DESKTOP_PATH = r"Control Panel\Desktop"

    @property
    def id(self) -> str:
        return "wallpaper"

    @property
    def name(self) -> str:
        return "桌面壁纸"

    @property
    def category(self) -> str:
        return "wallpaper"

    @property
    def description(self) -> str:
        return "扫描桌面壁纸设置"

    def _get_transcoded_wallpaper_path(self) -> Path | None:
        """获取 TranscodedWallpaper 路径"""
        app_data = os.environ.get("APPDATA", "")
        if not app_data:
            return None

        transcoded_path = (
            Path(app_data) / "Microsoft" / "Windows" / "Themes" / "TranscodedWallpaper"
        )
        if transcoded_path.exists():
            return transcoded_path
        return None

    def scan(self) -> list[ScannedItem]:
        """扫描壁纸设置"""
        items: list[ScannedItem] = []
        desktop_key = f"HKCU\\{self.DESKTOP_PATH}"

        # 扫描壁纸路径
        try:
            wallpaper_path, _ = self._registry.get_value(desktop_key, "Wallpaper")
            if wallpaper_path:
                associated_files = []
                wallpaper_file = Path(wallpaper_path)

                if wallpaper_file.exists():
                    try:
                        size = wallpaper_file.stat().st_size
                    except OSError:
                        size = None

                    associated_files.append(
                        AssociatedFile(
                            type=AssetType.IMAGE,
                            name=wallpaper_file.name,
                            path=str(wallpaper_file),
                            exists=True,
                            size_bytes=size,
                            sha256=None,
                        )
                    )

                items.append(
                    ScannedItem(
                        category=self.category,
                        key="wallpaper.path",
                        current_value=wallpaper_path,
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"{desktop_key}\\Wallpaper",
                        associated_files=associated_files,
                    )
                )
        except (FileNotFoundError, OSError):
            pass

        # 扫描壁纸样式
        try:
            style, _ = self._registry.get_value(desktop_key, "WallpaperStyle")
            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.style",
                    current_value=style,
                    default_value="10",  # Fill (默认)
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{desktop_key}\\WallpaperStyle",
                    metadata={"style_map": self._get_style_map()},
                )
            )
        except (FileNotFoundError, OSError):
            pass

        # 扫描平铺设置
        try:
            tile, _ = self._registry.get_value(desktop_key, "TileWallpaper")
            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.tile",
                    current_value=tile,
                    default_value="0",
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{desktop_key}\\TileWallpaper",
                )
            )
        except (FileNotFoundError, OSError):
            pass

        # 扫描 TranscodedWallpaper（实际显示的壁纸）
        transcoded = self._get_transcoded_wallpaper_path()
        if transcoded and transcoded.exists():
            try:
                size = transcoded.stat().st_size
            except OSError:
                size = None

            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.transcoded",
                    current_value=str(transcoded),
                    default_value=None,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.FILE,
                    source_path=str(transcoded),
                    associated_files=[
                        AssociatedFile(
                            type=AssetType.IMAGE,
                            name="TranscodedWallpaper",
                            path=str(transcoded),
                            exists=True,
                            size_bytes=size,
                            sha256=None,
                        )
                    ],
                )
            )

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用壁纸设置"""
        try:
            if item.key in ("wallpaper.path", "wallpaper.style", "wallpaper.tile"):
                key_path = item.source_path.rsplit("\\", 1)[0]
                value_name = item.source_path.rsplit("\\", 1)[1]
                self._registry.set_value(key_path, value_name, item.current_value)

                # 如果是壁纸路径，还需要复制文件
                if item.key == "wallpaper.path" and item.associated_files:
                    # 壁纸文件会在 export_assets 中处理
                    pass

                return True

            if item.key == "wallpaper.transcoded":
                # TranscodedWallpaper 需要复制文件
                if item.associated_files:
                    src = Path(item.associated_files[0].path)
                    dst = self._get_transcoded_wallpaper_path()
                    if src.exists() and dst:
                        shutil.copy2(src, dst)
                        return True
                return False

            return False
        except Exception:
            return False

    def _get_style_map(self) -> dict[str, str]:
        """壁纸样式映射"""
        return {
            "0": "Centered",
            "2": "Stretched",
            "6": "Fit",
            "10": "Fill",
            "22": "Span",
        }

    def get_default_values(self) -> dict[str, object]:
        """默认壁纸设置"""
        return {
            "wallpaper.style": "10",
            "wallpaper.tile": "0",
        }
