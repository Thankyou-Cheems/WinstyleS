"""
FontScanner - 系统字体扫描器

扫描:
- 字体替换 (FontSubstitutes)
- 字体链接 (FontLink)
- 已安装字体列表
"""

from typing import Any

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import SourceType
from winstyles.plugins.base import BaseScanner


class FontSubstitutesScanner(BaseScanner):
    """
    字体替换扫描器

    扫描 HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes
    """

    REGISTRY_PATH = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\FontSubstitutes"

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
            values = self._registry.get_all_values(
                f"HKLM\\{self.REGISTRY_PATH}"
            )

            for name, value in values.items():
                item = ScannedItem(
                    category=self.category,
                    key=name,
                    current_value=value,
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
        # TODO: 实现字体名称到文件的映射
        # 需要查询 HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts
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
            values = self._registry.get_all_values(
                f"HKLM\\{self.REGISTRY_PATH}"
            )

            for name, value in values.items():
                items.append(ScannedItem(
                    category=self.category,
                    key=name,
                    current_value=value,
                    source_type=SourceType.REGISTRY,
                    source_path=f"HKLM\\{self.REGISTRY_PATH}\\{name}",
                ))

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
