"""
StyleEngine - 核心引擎，负责调度扫描器和管理工作流
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from winstyles.core.analyzer import DiffAnalyzer
from winstyles.domain.models import Manifest, ScannedItem, ScanResult
from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import WindowsRegistryAdapter
from winstyles.plugins.base import BaseScanner
from winstyles.plugins.fonts import FontLinkScanner, FontSubstitutesScanner
from winstyles.plugins.terminal import PowerShellProfileScanner, WindowsTerminalScanner


class StyleEngine:
    """
    WinstyleS 核心引擎 - 编排者模式

    负责:
    - 加载和管理扫描器插件
    - 协调扫描、导出、导入流程
    - 加载默认值数据库
    """

    def __init__(self) -> None:
        self._scanners: list[BaseScanner] = []
        self._defaults_db: dict[str, Any] = {}
        self._load_plugins()
        self._load_defaults()

    def _load_plugins(self) -> None:
        """动态加载所有扫描器插件"""
        registry = WindowsRegistryAdapter()
        fs = WindowsFileSystemAdapter()
        self.register_scanner(FontSubstitutesScanner(registry, fs))
        self.register_scanner(FontLinkScanner(registry, fs))
        self.register_scanner(WindowsTerminalScanner(registry, fs))
        self.register_scanner(PowerShellProfileScanner(registry, fs))

    def _load_defaults(self) -> None:
        """加载 Windows 默认值数据库"""
        defaults_dir = Path(__file__).resolve().parents[3] / "data" / "defaults"
        if not defaults_dir.exists():
            self._defaults_db = {}
            return

        candidates = sorted(defaults_dir.glob("*.json"))
        if not candidates:
            self._defaults_db = {}
            return

        default_file = candidates[0]
        try:
            raw = json.loads(default_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._defaults_db = {}
            return

        self._defaults_db = self._flatten_defaults(raw)

    def _flatten_defaults(self, raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """将默认值 JSON 规整为 {category: {key: value}} 结构"""
        defaults: dict[str, dict[str, Any]] = {}

        fonts = raw.get("fonts", {})
        if isinstance(fonts, dict):
            font_defaults: dict[str, Any] = {}
            substitutes = fonts.get("substitutes", {})
            if isinstance(substitutes, dict):
                font_defaults.update(substitutes)
            font_link = fonts.get("font_link", {})
            if isinstance(font_link, dict):
                font_defaults.update(font_link)
            if font_defaults:
                defaults["fonts"] = font_defaults

        terminal = raw.get("terminal", {})
        if isinstance(terminal, dict):
            wt = terminal.get("windows_terminal", {})
            if isinstance(wt, dict):
                terminal_defaults: dict[str, Any] = {}
                key_map = {
                    "default_profile": "windowsTerminal.defaultProfile",
                    "theme": "windowsTerminal.theme",
                    "use_acrylic": "windowsTerminal.useAcrylicInTabRow",
                }
                for src_key, dest_key in key_map.items():
                    if src_key in wt:
                        terminal_defaults[dest_key] = wt[src_key]
                if terminal_defaults:
                    defaults["terminal"] = terminal_defaults

        return defaults

    def register_scanner(self, scanner: BaseScanner) -> None:
        """注册一个扫描器"""
        self._scanners.append(scanner)

    def scan_all(self, categories: list[str] | None = None) -> ScanResult:
        """
        执行全量扫描

        Args:
            categories: 要扫描的类别列表，None 表示扫描全部

        Returns:
            ScanResult: 扫描结果
        """
        items: list[ScannedItem] = []

        for scanner in self._scanners:
            if categories is None or scanner.category in categories:
                try:
                    scanned = scanner.scan()
                    items.extend(scanned)
                except Exception as e:
                    # TODO: 使用 logger 记录错误
                    print(f"Scanner {scanner.name} failed: {e}")

        analyzed_items = (
            DiffAnalyzer.compare(items, self._defaults_db) if self._defaults_db else items
        )

        return ScanResult(
            os_version="",
            items=analyzed_items,
            summary=self._generate_summary(analyzed_items),
            duration_ms=None,
        )

    def _generate_summary(self, items: list[ScannedItem]) -> dict[str, int]:
        """生成扫描结果摘要"""
        summary: dict[str, int] = {}
        for item in items:
            category = item.category
            summary[category] = summary.get(category, 0) + 1
        return summary

    def export_package(
        self,
        scan_result: ScanResult,
        output_path: Path,
        include_assets: bool = True,
    ) -> Manifest:
        """
        导出配置包

        Args:
            scan_result: 扫描结果
            output_path: 输出路径
            include_assets: 是否包含资源文件

        Returns:
            Manifest: 导出包的清单
        """
        # TODO: 实现导出逻辑
        raise NotImplementedError("Export not implemented yet")

    def import_package(
        self,
        package_path: Path,
        dry_run: bool = False,
        create_restore_point: bool = True,
    ) -> None:
        """
        导入配置包

        Args:
            package_path: 配置包路径
            dry_run: 仅预览，不实际应用
            create_restore_point: 是否创建系统还原点
        """
        # TODO: 实现导入逻辑
        raise NotImplementedError("Import not implemented yet")
