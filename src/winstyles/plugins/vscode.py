"""
VSCodeScanner - VS Code 配置扫描器

扫描:
- 用户设置 (settings.json)
- 字体设置
- 主题设置
- 终端字体设置
"""

import json
import os
from pathlib import Path
from typing import Any

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner


class VSCodeScanner(BaseScanner):
    """
    VS Code 配置扫描器

    扫描 %AppData%/Code/User/settings.json
    """

    # 要提取的设置键
    SETTINGS_KEYS = [
        # 编辑器字体
        "editor.fontFamily",
        "editor.fontSize",
        "editor.fontWeight",
        "editor.fontLigatures",
        "editor.lineHeight",
        # 主题
        "workbench.colorTheme",
        "workbench.iconTheme",
        "workbench.productIconTheme",
        # 终端字体
        "terminal.integrated.fontFamily",
        "terminal.integrated.fontSize",
        "terminal.integrated.fontWeight",
        # 颜色自定义
        "workbench.colorCustomizations",
        "editor.tokenColorCustomizations",
    ]

    @property
    def id(self) -> str:
        return "vscode"

    @property
    def name(self) -> str:
        return "VS Code"

    @property
    def category(self) -> str:
        return "vscode"

    @property
    def description(self) -> str:
        return "扫描 VS Code 字体和主题配置"

    def _get_settings_path(self) -> Path | None:
        """获取 VS Code 用户设置路径"""
        app_data = os.environ.get("APPDATA", "")
        if not app_data:
            return None

        # 标准 VS Code
        settings_path = Path(app_data) / "Code" / "User" / "settings.json"
        if settings_path.exists():
            return settings_path

        # VS Code Insiders
        insiders_path = Path(app_data) / "Code - Insiders" / "User" / "settings.json"
        if insiders_path.exists():
            return insiders_path

        return None

    def _get_nested_value(self, data: dict[str, Any], key: str) -> Any:
        """获取嵌套的设置值"""
        parts = key.split(".")
        current = data
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current

    def scan(self) -> list[ScannedItem]:
        """扫描 VS Code 设置"""
        items: list[ScannedItem] = []

        settings_path = self._get_settings_path()
        if not settings_path:
            return items

        try:
            content = self._fs.read_text(str(settings_path))
            # VS Code 设置可能包含注释，需要容错处理
            settings = self._parse_jsonc(content)
        except Exception:
            return items

        for key in self.SETTINGS_KEYS:
            value = settings.get(key)
            if value is not None:
                # 对于复杂对象，转换为 JSON 字符串
                if isinstance(value, (dict, list)):
                    display_value = json.dumps(value, ensure_ascii=False)
                else:
                    display_value = value

                items.append(
                    ScannedItem(
                        category=self.category,
                        key=f"vscode.{key}",
                        current_value=display_value,
                        default_value=self._get_default_for_key(key),
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.FILE,
                        source_path=str(settings_path),
                        metadata={"raw_value": value},
                    )
                )

        # 添加整个设置文件作为关联文件
        if items:
            try:
                size = settings_path.stat().st_size
            except OSError:
                size = None

            # 只在第一个 item 上添加关联文件
            items[0].associated_files.append(
                AssociatedFile(
                    type=AssetType.CONFIG,
                    name="settings.json",
                    path=str(settings_path),
                    exists=True,
                    size_bytes=size,
                    sha256=None,
                )
            )

        return items

    def _parse_jsonc(self, content: str) -> dict[str, Any]:
        """解析带注释的 JSON (JSONC)"""
        import re

        # 移除单行注释
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # 移除多行注释
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        # 移除尾随逗号
        content = re.sub(r",(\s*[}\]])", r"\1", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    def apply(self, item: ScannedItem) -> bool:
        """应用 VS Code 设置"""
        settings_path = self._get_settings_path()
        if not settings_path:
            return False

        try:
            # 读取现有设置
            if settings_path.exists():
                content = self._fs.read_text(str(settings_path))
                settings = self._parse_jsonc(content)
            else:
                settings = {}

            # 提取键名（移除 vscode. 前缀）
            key = item.key.replace("vscode.", "")

            # 获取原始值
            value = item.metadata.get("raw_value", item.current_value)

            # 如果是 JSON 字符串，解析回对象
            if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass

            # 设置值
            settings[key] = value

            # 写回文件
            self._fs.write_text(
                str(settings_path),
                json.dumps(settings, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )

            return True
        except Exception:
            return False

    def _get_default_for_key(self, key: str) -> Any:
        """获取设置的默认值"""
        defaults = {
            "editor.fontFamily": "Consolas, 'Courier New', monospace",
            "editor.fontSize": 14,
            "editor.fontWeight": "normal",
            "editor.fontLigatures": False,
            "editor.lineHeight": 0,
            "workbench.colorTheme": "Default Dark Modern",
            "workbench.iconTheme": "vs-seti",
            "terminal.integrated.fontFamily": "",
            "terminal.integrated.fontSize": 14,
            "terminal.integrated.fontWeight": "normal",
        }
        return defaults.get(key)

    def get_default_values(self) -> dict[str, object]:
        """VS Code 默认设置"""
        return {
            "vscode.editor.fontFamily": "Consolas, 'Courier New', monospace",
            "vscode.editor.fontSize": 14,
            "vscode.workbench.colorTheme": "Default Dark Modern",
        }
