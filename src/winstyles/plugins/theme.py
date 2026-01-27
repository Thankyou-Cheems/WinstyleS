"""
ThemeScanner - 系统主题扫描器

扫描:
- 深色/浅色模式
- 强调色
- 透明效果
- 颜色模式
"""

from winstyles.domain.models import ScannedItem
from winstyles.domain.types import ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


class ThemeScanner(BaseScanner):
    """
    Windows 主题扫描器

    扫描 HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize
    """

    PERSONALIZE_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    ACCENT_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Accent"

    @property
    def id(self) -> str:
        return "theme"

    @property
    def name(self) -> str:
        return "系统主题"

    @property
    def category(self) -> str:
        return "theme"

    @property
    def description(self) -> str:
        return "扫描系统主题设置（深色/浅色模式、强调色、透明效果）"

    def scan(self) -> list[ScannedItem]:
        """扫描主题设置"""
        items: list[ScannedItem] = []

        # 扫描 Personalize 设置
        personalize_items = [
            ("AppsUseLightTheme", "theme.appsUseLightTheme"),
            ("SystemUsesLightTheme", "theme.systemUsesLightTheme"),
            ("EnableTransparency", "theme.enableTransparency"),
            ("ColorPrevalence", "theme.colorPrevalence"),
        ]

        personalize_key = f"HKCU\\{self.PERSONALIZE_PATH}"

        for reg_name, key_name in personalize_items:
            try:
                value, _ = self._registry.get_value(personalize_key, reg_name)
                items.append(
                    ScannedItem(
                        category=self.category,
                        key=key_name,
                        current_value=value,
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"{personalize_key}\\{reg_name}",
                    )
                )
            except (FileNotFoundError, OSError):
                pass

        # 扫描强调色
        accent_key = f"HKCU\\{self.ACCENT_PATH}"
        try:
            accent_color, _ = self._registry.get_value(accent_key, "AccentColorMenu")
            # 转换为十六进制颜色值
            if isinstance(accent_color, int):
                # ABGR 格式转换为 #RRGGBB
                r = accent_color & 0xFF
                g = (accent_color >> 8) & 0xFF
                b = (accent_color >> 16) & 0xFF
                hex_color = f"#{r:02X}{g:02X}{b:02X}"
                items.append(
                    ScannedItem(
                        category=self.category,
                        key="theme.accentColor",
                        current_value=hex_color,
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"{accent_key}\\AccentColorMenu",
                        metadata={"raw_value": accent_color},
                    )
                )
        except (FileNotFoundError, OSError):
            pass

        # 扫描 AccentPalette
        try:
            palette, _ = self._registry.get_value(accent_key, "AccentPalette")
            if isinstance(palette, bytes):
                items.append(
                    ScannedItem(
                        category=self.category,
                        key="theme.accentPalette",
                        current_value=palette.hex(),
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"{accent_key}\\AccentPalette",
                    )
                )
        except (FileNotFoundError, OSError):
            pass

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用主题设置"""
        try:
            key_path = item.source_path.rsplit("\\", 1)[0]
            value_name = item.source_path.rsplit("\\", 1)[1]

            value = item.current_value

            # 处理强调色
            if item.key == "theme.accentColor" and item.metadata.get("raw_value"):
                value = item.metadata["raw_value"]
            elif item.key == "theme.accentPalette" and isinstance(value, str):
                value = bytes.fromhex(value)

            self._registry.set_value(key_path, value_name, value)
            return True
        except Exception:
            return False

    def get_default_values(self) -> dict[str, object]:
        """Windows 11 默认主题设置"""
        return {
            "theme.appsUseLightTheme": 1,
            "theme.systemUsesLightTheme": 1,
            "theme.enableTransparency": 1,
            "theme.colorPrevalence": 0,
            "theme.accentColor": "#0078D4",  # Windows 默认蓝色
        }
