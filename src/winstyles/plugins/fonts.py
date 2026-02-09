"""
FontScanner - 系统字体扫描器

扫描:
- 字体替换 (FontSubstitutes)
- 字体链接 (FontLink)
- 已安装字体列表
"""

from pathlib import Path
from typing import Any

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


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
