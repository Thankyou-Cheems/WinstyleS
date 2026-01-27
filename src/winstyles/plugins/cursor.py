"""
CursorScanner - 鼠标指针扫描器

扫描:
- 指针方案名称
- 各类指针路径
"""

from pathlib import Path

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


class CursorScanner(BaseScanner):
    """
    鼠标指针扫描器

    扫描 HKCU\\Control Panel\\Cursors
    """

    CURSORS_PATH = r"Control Panel\Cursors"

    # 指针类型列表
    CURSOR_TYPES = [
        "Arrow",
        "Help",
        "AppStarting",
        "Wait",
        "Crosshair",
        "IBeam",
        "NWPen",
        "No",
        "SizeNS",
        "SizeWE",
        "SizeNWSE",
        "SizeNESW",
        "SizeAll",
        "UpArrow",
        "Hand",
    ]

    @property
    def id(self) -> str:
        return "cursor"

    @property
    def name(self) -> str:
        return "鼠标指针"

    @property
    def category(self) -> str:
        return "cursor"

    @property
    def description(self) -> str:
        return "扫描鼠标指针方案"

    def scan(self) -> list[ScannedItem]:
        """扫描鼠标指针设置"""
        items: list[ScannedItem] = []
        cursors_key = f"HKCU\\{self.CURSORS_PATH}"

        # 扫描指针方案名称（默认值）
        try:
            scheme_name, _ = self._registry.get_value(cursors_key, "")
            if scheme_name:
                items.append(
                    ScannedItem(
                        category=self.category,
                        key="cursor.scheme",
                        current_value=scheme_name,
                        default_value="Windows Default",
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.REGISTRY,
                        source_path=f"{cursors_key}\\(Default)",
                    )
                )
        except (FileNotFoundError, OSError):
            pass

        # 扫描各类指针
        for cursor_type in self.CURSOR_TYPES:
            try:
                cursor_path, _ = self._registry.get_value(cursors_key, cursor_type)
                if cursor_path:
                    associated_files = []
                    cursor_file = Path(cursor_path)

                    # 展开环境变量
                    if "%SystemRoot%" in cursor_path:
                        import os

                        expanded = cursor_path.replace(
                            "%SystemRoot%", os.environ.get("SystemRoot", "C:\\Windows")
                        )
                        cursor_file = Path(expanded)

                    if cursor_file.exists():
                        try:
                            size = cursor_file.stat().st_size
                        except OSError:
                            size = None

                        associated_files.append(
                            AssociatedFile(
                                type=AssetType.CURSOR,
                                name=cursor_file.name,
                                path=str(cursor_file),
                                exists=True,
                                size_bytes=size,
                                sha256=None,
                            )
                        )

                    items.append(
                        ScannedItem(
                            category=self.category,
                            key=f"cursor.{cursor_type.lower()}",
                            current_value=cursor_path,
                            default_value=None,
                            change_type=ChangeType.MODIFIED,
                            source_type=SourceType.REGISTRY,
                            source_path=f"{cursors_key}\\{cursor_type}",
                            associated_files=associated_files,
                        )
                    )
            except (FileNotFoundError, OSError):
                pass

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用鼠标指针设置"""
        try:
            if item.key == "cursor.scheme":
                self._registry.set_value(f"HKCU\\{self.CURSORS_PATH}", "", item.current_value)
                return True

            if item.key.startswith("cursor."):
                cursor_type = item.key.replace("cursor.", "")
                # 找到原始大小写形式
                for ct in self.CURSOR_TYPES:
                    if ct.lower() == cursor_type:
                        self._registry.set_value(
                            f"HKCU\\{self.CURSORS_PATH}", ct, item.current_value
                        )
                        return True

            return False
        except Exception:
            return False

    def get_default_values(self) -> dict[str, object]:
        """Windows 默认指针"""
        return {
            "cursor.scheme": "Windows Default",
        }
