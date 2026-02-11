"""
FontScanner - 系统字体扫描器

扫描:
- 字体替换 (FontSubstitutes)
- 字体链接 (FontLink)
- 已安装字体列表
"""

import os
from pathlib import Path
from typing import Any

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.infra.registry import REG_DWORD
from winstyles.plugins.base import BaseScanner
from winstyles.utils.font_utils import get_font_version, identify_opensource


class FontSubstitutesScanner(BaseScanner):
    """
    字体替换扫描器

    扫描 HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes
    """

    REGISTRY_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes"
    FONTS_REGISTRY_PATH = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"

    @property
    def id(self) -> str:
        return "font_substitutes"

    @property
    def name(self) -> str:
        return "系统字体替换"

    @property
    def category(self) -> str:
        return "fonts"

    @property
    def description(self) -> str:
        return "扫描系统字体替换规则 (FontSubstitutes)"

    def supports_item(self, item: ScannedItem) -> bool:
        return item.source_path.startswith(f"HKLM\\{self.REGISTRY_PATH}\\")

    def scan(self) -> list[ScannedItem]:
        """扫描字体替换注册表项"""
        items: list[ScannedItem] = []

        try:
            # 使用注册表适配器读取所有值
            values = self._registry.get_all_values(f"HKLM\\{self.REGISTRY_PATH}")

            for name, value in values.items():
                item = ScannedItem(
                    category=self.category,
                    key=name,
                    current_value=value,
                    default_value=None,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"HKLM\\{self.REGISTRY_PATH}\\{name}",
                )

                # 尝试查找对应的字体文件
                font_file = self._find_font_file(value)
                if font_file:
                    item.associated_files.append(font_file)

                items.append(item)

        except Exception as e:
            # TODO: 使用 logger
            print(f"FontSubstitutesScanner error: {e}")

        return items

    def _find_font_file(self, font_name: str) -> AssociatedFile | None:
        """根据字体名称查找字体文件"""
        # 通过 HKLM\...\Fonts 反查字体文件路径
        normalized_name = str(font_name).split(",")[0].strip().lower()
        if not normalized_name:
            return None

        try:
            values = self._registry.get_all_values(self.FONTS_REGISTRY_PATH)
        except Exception:
            return None

        for reg_name, reg_value in values.items():
            display_name = str(reg_name).split("(")[0].strip().lower()
            if display_name != normalized_name:
                continue

            font_path = self._resolve_font_path(str(reg_value))
            if font_path is None or not font_path.exists():
                return None

            try:
                size = font_path.stat().st_size
            except OSError:
                size = None

            return AssociatedFile(
                type=AssetType.FONT,
                name=font_path.name,
                path=str(font_path),
                exists=True,
                size_bytes=size,
                sha256=None,
            )

        return None

    def _resolve_font_path(self, font_value: str) -> Path | None:
        path = Path(font_value)
        if path.is_absolute() and path.exists():
            return path

        system_root = Path(r"C:\Windows")
        candidate = system_root / "Fonts" / font_value
        if candidate.exists():
            return candidate
        return None

    def apply(self, item: ScannedItem) -> bool:
        """应用字体替换"""
        try:
            self._registry.set_value(
                f"HKLM\\{self.REGISTRY_PATH}",
                item.key,
                item.current_value,
            )
            return True
        except Exception:
            return False

    def get_default_values(self) -> dict[str, Any]:
        """Windows 默认的字体替换规则"""
        return {
            "MS Shell Dlg": "Microsoft Sans Serif",
            "MS Shell Dlg 2": "Tahoma",
        }


class FontLinkScanner(BaseScanner):
    """
    字体链接扫描器

    扫描 HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontLink\\SystemLink
    """

    REGISTRY_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontLink\SystemLink"
    FONTS_DIR = Path(r"C:\Windows\Fonts")

    @property
    def id(self) -> str:
        return "font_link"

    @property
    def name(self) -> str:
        return "字体链接"

    @property
    def category(self) -> str:
        return "fonts"

    @property
    def description(self) -> str:
        return "扫描字体链接规则 (FontLink)"

    def supports_item(self, item: ScannedItem) -> bool:
        return item.source_path.startswith(f"HKLM\\{self.REGISTRY_PATH}\\")

    def scan(self) -> list[ScannedItem]:
        """扫描字体链接注册表项"""
        items: list[ScannedItem] = []

        try:
            values = self._registry.get_all_values(f"HKLM\\{self.REGISTRY_PATH}")

            for name, value in values.items():
                associated_files = self._extract_linked_files(value)
                items.append(
                    ScannedItem(
                        category=self.category,
                        key=name,
                        current_value=value,
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"HKLM\\{self.REGISTRY_PATH}\\{name}",
                        associated_files=associated_files,
                    )
                )

        except Exception as e:
            print(f"FontLinkScanner error: {e}")

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用字体链接"""
        try:
            self._registry.set_value(
                f"HKLM\\{self.REGISTRY_PATH}",
                item.key,
                item.current_value,
            )
            return True
        except Exception:
            return False

    def _extract_linked_files(self, value: Any) -> list[AssociatedFile]:
        entries: list[str] = []
        if isinstance(value, list):
            entries = [str(v) for v in value]
        elif isinstance(value, str):
            entries = [value]

        files: list[AssociatedFile] = []
        for entry in entries:
            # 常见格式: "msgothic.ttc,MS UI Gothic"
            filename = entry.split(",")[0].strip()
            if not filename:
                continue

            path = self.FONTS_DIR / filename
            if not path.exists():
                continue

            try:
                size = path.stat().st_size
            except OSError:
                size = None

            files.append(
                AssociatedFile(
                    type=AssetType.FONT,
                    name=path.name,
                    path=str(path),
                    exists=True,
                    size_bytes=size,
                    sha256=None,
                )
            )
        return files


class InstalledFontsScanner(BaseScanner):
    """
    已安装字体与 ClearType 扫描器

    扫描:
    - HKLM/HKCU 字体清单
    - ClearType 状态与参数
    """

    MACHINE_FONTS_REGISTRY_PATH = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    USER_FONTS_REGISTRY_PATH = r"HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    CLEARTYPE_REGISTRY_PATH = r"HKCU\Control Panel\Desktop"

    CLEARTYPE_VALUE_MAP = {
        "FontSmoothing": "cleartype.enabled",
        "FontSmoothingType": "cleartype.mode",
        "FontSmoothingGamma": "cleartype.gamma",
        "FontSmoothingOrientation": "cleartype.orientation",
        "FontSmoothingContrast": "cleartype.contrast",
    }

    CLEARTYPE_ITEM_TO_VALUE = {value: key for key, value in CLEARTYPE_VALUE_MAP.items()}

    @property
    def id(self) -> str:
        return "installed_fonts"

    @property
    def name(self) -> str:
        return "已安装字体与 ClearType"

    @property
    def category(self) -> str:
        return "fonts"

    @property
    def description(self) -> str:
        return "扫描字体安装清单、ClearType 状态及开源字体识别结果"

    def supports_item(self, item: ScannedItem) -> bool:
        return item.key.startswith("installed.") or item.key.startswith("cleartype.")

    def scan(self) -> list[ScannedItem]:
        items: list[ScannedItem] = []
        items.extend(
            self._scan_installed_fonts_from_registry(
                self.MACHINE_FONTS_REGISTRY_PATH, scope="machine"
            )
        )
        items.extend(
            self._scan_installed_fonts_from_registry(
                self.USER_FONTS_REGISTRY_PATH,
                scope="user",
            )
        )
        items.extend(self._scan_cleartype_settings())
        return items

    def apply(self, item: ScannedItem) -> bool:
        if item.key.startswith("installed."):
            # 纯观察型数据，不参与导入写回
            return True

        if not item.key.startswith("cleartype."):
            return False

        value_name = self.CLEARTYPE_ITEM_TO_VALUE.get(item.key)
        if value_name is None:
            return False

        try:
            value_to_write: object = item.current_value
            if item.key == "cleartype.enabled":
                value_to_write = 2 if bool(item.current_value) else 0

            if isinstance(value_to_write, bool):
                value_to_write = int(value_to_write)

            if isinstance(value_to_write, int):
                self._registry.set_value(
                    self.CLEARTYPE_REGISTRY_PATH,
                    value_name,
                    value_to_write,
                    value_type=REG_DWORD,
                )
            else:
                self._registry.set_value(
                    self.CLEARTYPE_REGISTRY_PATH,
                    value_name,
                    value_to_write,
                )
            return True
        except Exception:
            return False

    def _scan_installed_fonts_from_registry(
        self, registry_path: str, scope: str
    ) -> list[ScannedItem]:
        try:
            values = self._registry.get_all_values(registry_path)
        except Exception:
            return []

        items: list[ScannedItem] = []
        for reg_name, reg_value in sorted(values.items()):
            normalized_name = self._normalize_registry_font_name(reg_name)
            resolved_path = self._resolve_font_path(str(reg_value))

            associated_files: list[AssociatedFile] = []
            current_value: object = str(reg_value)
            metadata: dict[str, Any] = {
                "scope": scope,
                "registry_name": reg_name,
                "registry_value": reg_value,
                "readonly": True,
            }

            if resolved_path is not None and resolved_path.exists():
                try:
                    size = resolved_path.stat().st_size
                except OSError:
                    size = None

                associated_files.append(
                    AssociatedFile(
                        type=AssetType.FONT,
                        name=resolved_path.name,
                        path=str(resolved_path),
                        exists=True,
                        size_bytes=size,
                        sha256=None,
                    )
                )
                current_value = str(resolved_path)

                version = get_font_version(resolved_path)
                if version:
                    metadata["version"] = version

            match = identify_opensource(normalized_name)
            if match is not None:
                metadata["is_opensource"] = True
                metadata["opensource"] = dict(match)
            else:
                metadata["is_opensource"] = False

            items.append(
                ScannedItem(
                    category=self.category,
                    key=f"installed.{scope}.{reg_name}",
                    current_value=current_value,
                    default_value=None,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{registry_path}\\{reg_name}",
                    associated_files=associated_files,
                    metadata=metadata,
                )
            )

        return items

    def _scan_cleartype_settings(self) -> list[ScannedItem]:
        try:
            values = self._registry.get_all_values(self.CLEARTYPE_REGISTRY_PATH)
        except Exception:
            return []

        items: list[ScannedItem] = []
        for value_name, item_key in self.CLEARTYPE_VALUE_MAP.items():
            if value_name not in values:
                continue

            raw_value = values[value_name]
            current_value: object = raw_value
            if item_key == "cleartype.enabled":
                parsed = self._parse_int(raw_value)
                current_value = (parsed or 0) > 0
            else:
                parsed = self._parse_int(raw_value)
                if parsed is not None:
                    current_value = parsed

            items.append(
                ScannedItem(
                    category=self.category,
                    key=item_key,
                    current_value=current_value,
                    default_value=None,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{self.CLEARTYPE_REGISTRY_PATH}\\{value_name}",
                    metadata={"raw_value": raw_value},
                )
            )

        return items

    def _normalize_registry_font_name(self, value_name: str) -> str:
        return str(value_name).split("(")[0].strip()

    def _resolve_font_path(self, raw_value: str) -> Path | None:
        candidate = Path(raw_value)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        system_fonts = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Fonts" / raw_value
        if system_fonts.exists():
            return system_fonts

        user_fonts = (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts" / raw_value
        )
        if user_fonts.exists():
            return user_fonts

        return None

    def _parse_int(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except ValueError:
            return None
