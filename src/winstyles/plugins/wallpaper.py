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
from typing import Any

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


class WallpaperScanner(BaseScanner):
    """
    壁纸扫描器

    扫描 HKCU\\Control Panel\\Desktop 中的壁纸设置
    """

    DESKTOP_PATH = r"Control Panel\Desktop"
    LOCKSCREEN_POLICY_PATH = r"SOFTWARE\Policies\Microsoft\Windows\Personalization"
    CONTENT_DELIVERY_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"

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

    def _get_spotlight_assets_dir(self) -> Path | None:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            return None
        assets_dir = (
            Path(local_app_data)
            / "Packages"
            / "Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy"
            / "LocalState"
            / "Assets"
        )
        if assets_dir.exists():
            return assets_dir
        return None

    def _normalize_image_path(self, path: str) -> Path:
        expanded = os.path.expanduser(os.path.expandvars(str(path).strip().strip('"')))
        return Path(expanded)

    def _safe_int(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except ValueError:
            return None

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
                normalized_wallpaper = self._normalize_image_path(str(wallpaper_path))

                if normalized_wallpaper.exists():
                    try:
                        size = normalized_wallpaper.stat().st_size
                    except OSError:
                        size = None

                    associated_files.append(
                        AssociatedFile(
                            type=AssetType.IMAGE,
                            name=normalized_wallpaper.name,
                            path=str(normalized_wallpaper),
                            exists=True,
                            size_bytes=size,
                            sha256=None,
                        )
                    )

                items.append(
                    ScannedItem(
                        category=self.category,
                        key="wallpaper.path",
                        current_value=str(normalized_wallpaper),
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"{desktop_key}\\Wallpaper",
                        associated_files=associated_files,
                        metadata={"surface": "desktop", "raw_value": wallpaper_path},
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
                    metadata={"style_map": self._get_style_map(), "surface": "desktop"},
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
                    metadata={"surface": "desktop"},
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
                    metadata={"surface": "desktop"},
                )
            )

        lockscreen_policy_key = f"HKLM\\{self.LOCKSCREEN_POLICY_PATH}"
        try:
            lockscreen_image, _ = self._registry.get_value(lockscreen_policy_key, "LockScreenImage")
            normalized_lockscreen = self._normalize_image_path(str(lockscreen_image))
            associated_files = []
            if normalized_lockscreen.exists():
                try:
                    size = normalized_lockscreen.stat().st_size
                except OSError:
                    size = None
                associated_files.append(
                    AssociatedFile(
                        type=AssetType.IMAGE,
                        name=normalized_lockscreen.name,
                        path=str(normalized_lockscreen),
                        exists=True,
                        size_bytes=size,
                        sha256=None,
                    )
                )
            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.lockscreen.path",
                    current_value=str(normalized_lockscreen),
                    default_value=None,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{lockscreen_policy_key}\\LockScreenImage",
                    associated_files=associated_files,
                    metadata={"surface": "lockscreen", "readonly": True},
                )
            )
        except (FileNotFoundError, OSError):
            pass

        content_delivery_key = f"HKCU\\{self.CONTENT_DELIVERY_PATH}"
        spotlight_enabled = False
        try:
            raw_spotlight, _ = self._registry.get_value(
                content_delivery_key, "RotatingLockScreenEnabled"
            )
            parsed = self._safe_int(raw_spotlight)
            spotlight_enabled = bool(parsed and parsed > 0)
            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.lockscreen.spotlightEnabled",
                    current_value=spotlight_enabled,
                    default_value=False,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{content_delivery_key}\\RotatingLockScreenEnabled",
                    metadata={
                        "surface": "lockscreen",
                        "raw_value": raw_spotlight,
                        "readonly": True,
                    },
                )
            )
        except (FileNotFoundError, OSError):
            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.lockscreen.spotlightEnabled",
                    current_value=False,
                    default_value=False,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{content_delivery_key}\\RotatingLockScreenEnabled",
                    metadata={"surface": "lockscreen", "readonly": True},
                )
            )

        try:
            raw_overlay, _ = self._registry.get_value(
                content_delivery_key,
                "RotatingLockScreenOverlayEnabled",
            )
            parsed_overlay = self._safe_int(raw_overlay)
            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.lockscreen.spotlightOverlayEnabled",
                    current_value=bool(parsed_overlay and parsed_overlay > 0),
                    default_value=False,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{content_delivery_key}\\RotatingLockScreenOverlayEnabled",
                    metadata={"surface": "lockscreen", "raw_value": raw_overlay, "readonly": True},
                )
            )
        except (FileNotFoundError, OSError):
            pass

        assets_dir = self._get_spotlight_assets_dir()
        if assets_dir:
            try:
                candidates = [
                    file
                    for file in assets_dir.iterdir()
                    if file.is_file() and file.stat().st_size >= 100 * 1024
                ]
                asset_count = len(candidates)
            except OSError:
                asset_count = 0

            items.append(
                ScannedItem(
                    category=self.category,
                    key="wallpaper.lockscreen.spotlightAssetCount",
                    current_value=asset_count,
                    default_value=0,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.FILE,
                    source_path=str(assets_dir),
                    metadata={
                        "surface": "lockscreen",
                        "spotlight_enabled": spotlight_enabled,
                        "readonly": True,
                    },
                )
            )

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用壁纸设置"""
        try:
            readonly_flag = item.metadata.get("readonly")
            if isinstance(readonly_flag, bool) and readonly_flag:
                return True

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
