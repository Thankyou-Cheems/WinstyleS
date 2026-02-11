"""
CursorScanner - 鼠标指针扫描器

扫描:
- 指针方案名称
- 各类指针路径
"""

import os
from pathlib import Path
from typing import Any

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.infra.registry import REG_DWORD
from winstyles.plugins.base import BaseScanner


class CursorScanner(BaseScanner):
    """
    鼠标指针扫描器

    扫描 HKCU\\Control Panel\\Cursors
    """

    CURSORS_PATH = r"Control Panel\Cursors"
    CURSOR_SIZE_KEYS = ["CursorBaseSize", "CursorSize"]

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

    def _normalize_cursor_path(self, raw_path: str) -> Path | None:
        value = str(raw_path).strip().strip('"')
        if not value:
            return None

        expanded = os.path.expandvars(value)
        if expanded.startswith(r"\??\\"):
            expanded = expanded[4:]
        candidate = Path(expanded)

        if not candidate.is_absolute():
            candidate = (
                Path(os.environ.get("SystemRoot", r"C:\Windows")) / "cursors" / candidate.name
            )

        return candidate

    def _safe_int(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        try:
            return int(str(value).strip())
        except ValueError:
            return None

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

        for size_key in self.CURSOR_SIZE_KEYS:
            try:
                size_value, _ = self._registry.get_value(cursors_key, size_key)
            except (FileNotFoundError, OSError):
                continue

            parsed_size = self._safe_int(size_value)
            if parsed_size is None:
                continue
            items.append(
                ScannedItem(
                    category=self.category,
                    key="cursor.size",
                    current_value=parsed_size,
                    default_value=32,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.REGISTRY,
                    source_path=f"{cursors_key}\\{size_key}",
                )
            )
            break

        # 扫描各类指针
        for cursor_type in self.CURSOR_TYPES:
            try:
                cursor_path, _ = self._registry.get_value(cursors_key, cursor_type)
                if cursor_path:
                    associated_files = []
                    normalized_path = self._normalize_cursor_path(str(cursor_path))
                    current_value = str(normalized_path) if normalized_path else str(cursor_path)

                    if normalized_path and normalized_path.exists():
                        try:
                            size = normalized_path.stat().st_size
                        except OSError:
                            size = None

                        associated_files.append(
                            AssociatedFile(
                                type=AssetType.CURSOR,
                                name=normalized_path.name,
                                path=str(normalized_path),
                                exists=True,
                                size_bytes=size,
                                sha256=None,
                            )
                        )

                    items.append(
                        ScannedItem(
                            category=self.category,
                            key=f"cursor.{cursor_type.lower()}",
                            current_value=current_value,
                            default_value=None,
                            change_type=ChangeType.MODIFIED,
                            source_type=SourceType.REGISTRY,
                            source_path=f"{cursors_key}\\{cursor_type}",
                            associated_files=associated_files,
                            metadata={"raw_value": cursor_path},
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

            if item.key == "cursor.size":
                parsed = self._safe_int(item.current_value)
                if parsed is None:
                    return False
                self._registry.set_value(
                    f"HKCU\\{self.CURSORS_PATH}",
                    "CursorBaseSize",
                    parsed,
                    value_type=REG_DWORD,
                )
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
