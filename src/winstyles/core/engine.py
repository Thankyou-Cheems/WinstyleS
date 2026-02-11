"""
StyleEngine - 核心引擎，负责调度扫描器和管理工作流
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from winstyles.core.analyzer import DiffAnalyzer
from winstyles.domain.models import ExportOptions, Manifest, ScannedItem, ScanResult, SourceSystem
from winstyles.domain.types import AssetType
from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import WindowsRegistryAdapter
from winstyles.infra.restore import RestorePointManager
from winstyles.infra.system import SystemAPI
from winstyles.plugins.base import BaseScanner
from winstyles.plugins.cursor import CursorScanner
from winstyles.plugins.fonts import (
    FontLinkScanner,
    FontSubstitutesScanner,
    InstalledFontsScanner,
)
from winstyles.plugins.terminal import (
    OhMyPoshScanner,
    PowerShellProfileScanner,
    WindowsTerminalScanner,
)
from winstyles.plugins.theme import ThemeScanner
from winstyles.plugins.vscode import VSCodeScanner
from winstyles.plugins.wallpaper import WallpaperScanner


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
        self._defaults_os_version = ""
        self._load_plugins()
        self._load_defaults()

    def _load_plugins(self) -> None:
        """动态加载所有扫描器插件"""
        registry = WindowsRegistryAdapter()
        fs = WindowsFileSystemAdapter()
        # 字体扫描器
        self.register_scanner(FontSubstitutesScanner(registry, fs))
        self.register_scanner(FontLinkScanner(registry, fs))
        self.register_scanner(InstalledFontsScanner(registry, fs))
        # 终端扫描器
        self.register_scanner(WindowsTerminalScanner(registry, fs))
        self.register_scanner(PowerShellProfileScanner(registry, fs))
        self.register_scanner(OhMyPoshScanner(registry, fs))
        # 主题扫描器
        self.register_scanner(ThemeScanner(registry, fs))
        # 壁纸扫描器
        self.register_scanner(WallpaperScanner(registry, fs))
        # 鼠标指针扫描器
        self.register_scanner(CursorScanner(registry, fs))
        # VS Code 扫描器
        self.register_scanner(VSCodeScanner(registry, fs))

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

        self._defaults_os_version = str(raw.get("os_version", "")).strip()
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
                    "font_face": "windowsTerminal.defaults.font.face",
                    "font_size": "windowsTerminal.defaults.font.size",
                }
                for src_key, dest_key in key_map.items():
                    if src_key in wt:
                        terminal_defaults[dest_key] = wt[src_key]
                if "use_acrylic" in wt:
                    terminal_defaults["windowsTerminal.defaults.useAcrylic"] = wt["use_acrylic"]
                if "font_face" in wt:
                    terminal_defaults["windowsTerminal.defaults.fontFace"] = wt["font_face"]
                if "font_size" in wt:
                    terminal_defaults["windowsTerminal.defaults.fontSize"] = wt["font_size"]
                if terminal_defaults:
                    defaults["terminal"] = terminal_defaults

        theme = raw.get("theme", {})
        appearance = raw.get("appearance", {})
        theme_defaults: dict[str, Any] = {}
        if isinstance(theme, dict):
            theme_map = {
                "appsUseLightTheme": "theme.appsUseLightTheme",
                "systemUsesLightTheme": "theme.systemUsesLightTheme",
                "enableTransparency": "theme.enableTransparency",
                "colorPrevalence": "theme.colorPrevalence",
                "accentColor": "theme.accentColor",
            }
            for src_key, dest_key in theme_map.items():
                if src_key in theme:
                    theme_defaults[dest_key] = theme[src_key]
        if isinstance(appearance, dict):
            appearance_map = {
                "colorization_color": "theme.dwm.colorizationColor",
                "colorization_color_balance": "theme.dwm.colorizationColorBalance",
                "colorization_afterglow": "theme.dwm.colorizationAfterglow",
                "colorization_afterglow_balance": "theme.dwm.colorizationAfterglowBalance",
                "colorization_blur_balance": "theme.dwm.colorizationBlurBalance",
                "accent_color_inactive": "theme.dwm.accentColorInactive",
            }
            color_keys = {
                "colorization_color",
                "colorization_afterglow",
                "accent_color_inactive",
            }
            for src_key, dest_key in appearance_map.items():
                if src_key in appearance:
                    value = appearance[src_key]
                    if src_key in color_keys:
                        value = self._normalize_dwm_color_default(value)
                    theme_defaults[dest_key] = value
        if theme_defaults:
            defaults["theme"] = theme_defaults

        wallpaper = raw.get("wallpaper", {})
        if isinstance(wallpaper, dict):
            wallpaper_defaults: dict[str, Any] = {}
            if "style" in wallpaper:
                wallpaper_defaults["wallpaper.style"] = wallpaper["style"]
            if "tile" in wallpaper:
                wallpaper_defaults["wallpaper.tile"] = wallpaper["tile"]
            if wallpaper_defaults:
                defaults["wallpaper"] = wallpaper_defaults

        cursor = raw.get("cursor", {})
        if isinstance(cursor, dict):
            cursor_defaults: dict[str, Any] = {}
            if "scheme" in cursor:
                cursor_defaults["cursor.scheme"] = cursor["scheme"]

            cursors = cursor.get("cursors", {})
            if isinstance(cursors, dict):
                for key, value in cursors.items():
                    cursor_defaults[f"cursor.{str(key).lower()}"] = (
                        self._normalize_default_cursor_path(value)
                    )
            if cursor_defaults:
                defaults["cursor"] = cursor_defaults

        return defaults

    def _normalize_default_cursor_path(self, raw_value: Any) -> Any:
        if not isinstance(raw_value, str):
            return raw_value
        value = raw_value.strip()
        if not value:
            return value
        expanded = os.path.expandvars(value)
        return str(Path(expanded))

    def _normalize_dwm_color_default(self, raw_value: Any) -> Any:
        if isinstance(raw_value, int):
            return self._abgr_to_hex(raw_value)
        if isinstance(raw_value, str):
            text = raw_value.strip()
            if text.startswith("0x"):
                try:
                    return self._abgr_to_hex(int(text, 16))
                except ValueError:
                    return raw_value
            if text.startswith("#"):
                return text.upper()
        return raw_value

    def _abgr_to_hex(self, value: int) -> str:
        r = value & 0xFF
        g = (value >> 8) & 0xFF
        b = (value >> 16) & 0xFF
        return f"#{r:02X}{g:02X}{b:02X}"

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
            os_version=self._defaults_os_version,
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
        include_font_files: bool = False,
    ) -> Manifest:
        """
        导出配置包

        Args:
            scan_result: 扫描结果
            output_path: 输出路径
            include_assets: 是否包含资源文件
            include_font_files: 是否包含字体文件

        Returns:
            Manifest: 导出包的清单
        """
        output_path = Path(output_path)
        if output_path.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_dir = Path(tmp_dir)
                manifest = self._write_package(
                    output_dir,
                    scan_result=scan_result,
                    include_assets=include_assets,
                    include_font_files=include_font_files,
                )
                self._zip_dir(output_dir, output_path)
                return manifest

        output_path.mkdir(parents=True, exist_ok=True)
        return self._write_package(
            output_path,
            scan_result=scan_result,
            include_assets=include_assets,
            include_font_files=include_font_files,
        )

    def import_package(
        self,
        package_path: Path,
        dry_run: bool = False,
        create_restore_point: bool = True,
    ) -> dict[str, Any]:
        """
        导入配置包

        Args:
            package_path: 配置包路径
            dry_run: 仅预览，不实际应用
            create_restore_point: 是否创建系统还原点
        """
        package_path = Path(package_path)
        if package_path.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory() as tmp_dir:
                output_dir = Path(tmp_dir)
                with zipfile.ZipFile(package_path, "r") as zip_ref:
                    zip_ref.extractall(output_dir)
                return self._import_from_dir(
                    output_dir,
                    dry_run=dry_run,
                    create_restore_point=create_restore_point,
                )

        return self._import_from_dir(
            package_path,
            dry_run=dry_run,
            create_restore_point=create_restore_point,
        )

    def _write_package(
        self,
        output_dir: Path,
        scan_result: ScanResult,
        include_assets: bool,
        include_font_files: bool,
    ) -> Manifest:
        output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = output_dir / "assets"

        if include_assets:
            assets_dir.mkdir(parents=True, exist_ok=True)

        source_system = self._build_source_system()
        export_options = self._build_export_options(scan_result)

        manifest = Manifest.model_validate(
            {
                "$schema": "1.0.0",
                "version": "1.0.0",
                "created_by": "WinstyleS",
                "source_system": source_system.model_dump(mode="json"),
                "export_options": export_options.model_dump(mode="json"),
            }
        )

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                manifest.model_dump(mode="json", by_alias=True),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        scan_path = output_dir / "scan.json"
        scan_path.write_text(
            json.dumps(scan_result.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if include_assets:
            self._export_assets(
                scan_result,
                assets_dir,
                include_font_files=include_font_files,
            )

        return manifest

    def _export_assets(
        self,
        scan_result: ScanResult,
        assets_dir: Path,
        include_font_files: bool,
    ) -> None:
        copied_by_category: dict[str, set[str]] = {}
        for item in scan_result.items:
            category_key = item.category
            if category_key not in copied_by_category:
                copied_by_category[category_key] = set()
            for file in item.associated_files:
                if file.type == AssetType.FONT and not include_font_files:
                    continue
                if not file.exists:
                    continue
                src_path = Path(file.path)
                if not src_path.exists():
                    continue
                normalized_src = str(src_path).lower()
                if normalized_src in copied_by_category[category_key]:
                    continue
                dest_dir = assets_dir / item.category
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / src_path.name
                if dest_path.exists():
                    dest_path = dest_dir / f"{src_path.stem}_{abs(hash(src_path))}{src_path.suffix}"
                shutil.copy2(src_path, dest_path)
                copied_by_category[category_key].add(normalized_src)

    def _zip_dir(self, source_dir: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    zip_ref.write(file_path, file_path.relative_to(source_dir))

    def _import_from_dir(
        self,
        package_dir: Path,
        dry_run: bool,
        create_restore_point: bool,
    ) -> dict[str, Any]:
        scan_path = package_dir / "scan.json"
        if not scan_path.exists():
            return {"total": 0, "applied": 0, "failed": 0, "skipped": 0}

        scan_data = json.loads(scan_path.read_text(encoding="utf-8"))
        scan_result = ScanResult.model_validate(scan_data)
        resolved_scan = self._resolve_import_assets(scan_result, package_dir)

        if dry_run:
            plan = self._build_dry_run_plan(resolved_scan.items)
            would_apply = sum(1 for item in plan if item["action"] == "apply")
            would_skip = len(plan) - would_apply
            return {
                "total": len(resolved_scan.items),
                "applied": 0,
                "failed": 0,
                "skipped": len(resolved_scan.items),
                "would_apply": would_apply,
                "would_skip": would_skip,
                "dry_run_plan": plan,
                "risk_summary": self._summarize_risk(plan),
            }

        if create_restore_point:
            restore_manager = RestorePointManager()
            restore_manager.create_restore_point()

        applied = 0
        failed = 0
        skipped = 0

        for item in resolved_scan.items:
            readonly_flag = item.metadata.get("readonly")
            if isinstance(readonly_flag, bool) and readonly_flag:
                skipped += 1
                continue

            scanner = self._find_scanner_for_item(item)
            if scanner is None:
                skipped += 1
                continue
            try:
                if scanner.apply(item):
                    applied += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

        return {
            "total": len(resolved_scan.items),
            "applied": applied,
            "failed": failed,
            "skipped": skipped,
        }

    def _build_dry_run_plan(self, items: list[ScannedItem]) -> list[dict[str, Any]]:
        plan: list[dict[str, Any]] = []
        for item in items:
            readonly_flag = item.metadata.get("readonly")
            is_readonly = isinstance(readonly_flag, bool) and readonly_flag
            scanner = self._find_scanner_for_item(item)

            action = "apply"
            reason = "可由对应扫描器写回"
            if is_readonly:
                action = "skip"
                reason = "只读项，导入时不会写回"
            elif scanner is None:
                action = "skip"
                reason = "未找到可处理该项的扫描器"

            risk, risk_reason = self._assess_import_risk(item, action)
            plan.append(
                {
                    "category": item.category,
                    "key": item.key,
                    "action": action,
                    "operation": self._infer_import_operation(item, action),
                    "target": item.source_path,
                    "risk": risk,
                    "reason": reason,
                    "risk_reason": risk_reason,
                }
            )
        return plan

    def _summarize_risk(self, plan: list[dict[str, Any]]) -> dict[str, int]:
        summary = {"low": 0, "medium": 0, "high": 0}
        for entry in plan:
            risk = str(entry.get("risk", "")).lower()
            if risk in summary:
                summary[risk] += 1
        return summary

    def _infer_import_operation(self, item: ScannedItem, action: str) -> str:
        if action == "skip":
            return "skip"
        if item.source_type.value == "registry":
            return "set_registry_value"
        if item.source_type.value == "file":
            return "write_file"
        if item.source_type.value == "system_api":
            return "invoke_system_api"
        return "apply"

    def _assess_import_risk(self, item: ScannedItem, action: str) -> tuple[str, str]:
        if action == "skip":
            return "low", "dry-run 仅预览，不会执行写入"

        if item.source_type.value == "registry":
            if item.category in {"fonts", "theme", "cursor", "wallpaper"}:
                return "high", "涉及系统外观相关注册表写入"
            return "medium", "涉及注册表写入"

        if item.source_type.value == "file":
            if item.associated_files:
                return "medium", "涉及配置文件与关联资源调整"
            return "low", "仅涉及配置文件写入"

        if item.source_type.value == "system_api":
            return "high", "涉及系统 API 调用"

        return "medium", "未知来源类型，建议谨慎执行"

    def _resolve_import_assets(self, scan_result: ScanResult, package_dir: Path) -> ScanResult:
        assets_root = package_dir / "assets"
        if not assets_root.exists():
            return scan_result

        home_root = Path.home() / ".winstyles" / "imported_assets" / scan_result.scan_id
        home_root.mkdir(parents=True, exist_ok=True)

        rewritten_items: list[ScannedItem] = []
        for item in scan_result.items:
            rewritten_files = []
            for file in item.associated_files:
                source_path = Path(file.path)
                if source_path.exists():
                    rewritten_files.append(file)
                    continue

                package_file = self._find_asset_in_package(
                    assets_root / item.category,
                    file.name,
                )
                if package_file is None:
                    rewritten_files.append(file)
                    continue

                target_dir = home_root / item.category
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / package_file.name
                if not target_path.exists():
                    shutil.copy2(package_file, target_path)

                rewritten_files.append(
                    file.model_copy(
                        update={
                            "path": str(target_path),
                            "exists": True,
                            "size_bytes": target_path.stat().st_size,
                        }
                    )
                )

            updated_item = item.model_copy(update={"associated_files": rewritten_files})
            if rewritten_files:
                if updated_item.key in {"wallpaper.path", "wallpaper.transcoded"}:
                    updated_item = updated_item.model_copy(
                        update={"current_value": rewritten_files[0].path}
                    )
                elif updated_item.key.startswith("cursor."):
                    updated_item = updated_item.model_copy(
                        update={"current_value": rewritten_files[0].path}
                    )
            rewritten_items.append(updated_item)

        return scan_result.model_copy(update={"items": rewritten_items})

    def _find_asset_in_package(self, category_dir: Path, name: str) -> Path | None:
        if not category_dir.exists():
            return None

        exact = category_dir / name
        if exact.exists():
            return exact

        stem = Path(name).stem
        suffix = Path(name).suffix
        for candidate in category_dir.glob(f"{stem}_*{suffix}"):
            if candidate.is_file():
                return candidate
        return None

    def load_scan_result(self, package_path: Path) -> ScanResult | None:
        data = self._read_json_from_package(Path(package_path), "scan.json")
        if data is None:
            return None
        return ScanResult.model_validate(data)

    def load_manifest(self, package_path: Path) -> Manifest | None:
        data = self._read_json_from_package(Path(package_path), "manifest.json")
        if data is None:
            return None
        return Manifest.model_validate(data)

    def _read_json_from_package(self, package_path: Path, filename: str) -> dict[str, Any] | None:
        if package_path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(package_path, "r") as zip_ref:
                    if filename not in zip_ref.namelist():
                        return None
                    with zip_ref.open(filename) as handle:
                        payload = json.loads(handle.read().decode("utf-8"))
                        if isinstance(payload, dict):
                            return payload
                        return None
            except (OSError, KeyError, json.JSONDecodeError):
                return None

        file_path = package_path / filename
        if not file_path.exists():
            return None
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
            return None
        except (OSError, json.JSONDecodeError):
            return None

    def diff_packages(self, package_a: Path, package_b: Path) -> dict[str, Any]:
        scan_a = self.load_scan_result(package_a)
        scan_b = self.load_scan_result(package_b)
        if scan_a is None or scan_b is None:
            return {
                "error": "scan.json not found",
                "package_a": str(package_a),
                "package_b": str(package_b),
            }

        items_a = {(item.category, item.key): item for item in scan_a.items}
        items_b = {(item.category, item.key): item for item in scan_b.items}

        all_keys = sorted(set(items_a) | set(items_b))
        diff_items: list[dict[str, Any]] = []
        counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}

        for category, key in all_keys:
            item_a = items_a.get((category, key))
            item_b = items_b.get((category, key))
            if item_a is None:
                change = "added"
                before = None
                after = item_b.current_value if item_b else None
            elif item_b is None:
                change = "removed"
                before = item_a.current_value
                after = None
            else:
                before = item_a.current_value
                after = item_b.current_value
                change = "unchanged" if before == after else "modified"

            counts[change] += 1
            diff_items.append(
                {
                    "category": category,
                    "key": key,
                    "change": change,
                    "before": before,
                    "after": after,
                }
            )

        return {
            "package_a": str(package_a),
            "package_b": str(package_b),
            "total": len(all_keys),
            "added": counts["added"],
            "removed": counts["removed"],
            "modified": counts["modified"],
            "unchanged": counts["unchanged"],
            "items": diff_items,
        }

    def _find_scanner_for_item(self, item: ScannedItem) -> BaseScanner | None:
        for scanner in self._scanners:
            if scanner.category != item.category:
                continue
            if scanner.supports_item(item):
                return scanner
        return None

    def _build_source_system(self) -> SourceSystem:
        major, minor, build = SystemAPI.get_windows_version()
        os_name = platform.system() or "Windows"
        version = platform.release() or ""
        if self._defaults_os_version:
            if self._defaults_os_version.startswith("Windows "):
                version = self._defaults_os_version.replace("Windows ", "").strip()
            else:
                version = self._defaults_os_version

        hostname = platform.node() or os.environ.get("COMPUTERNAME", "")
        try:
            username = os.getlogin()
        except OSError:
            username = os.environ.get("USERNAME", "")

        return SourceSystem(
            os=os_name,
            version=version,
            build=str(build if build else ""),
            hostname=hostname,
            username=username,
        )

    def _build_export_options(self, scan_result: ScanResult) -> ExportOptions:
        categories = {item.category for item in scan_result.items}
        return ExportOptions(
            include_fonts="fonts" in categories,
            include_wallpapers="wallpaper" in categories,
            include_cursors="cursor" in categories,
            include_terminal="terminal" in categories,
            include_vscode="vscode" in categories,
            include_browser="browser" in categories,
        )
