"""
TerminalScanner - 终端配置扫描器

扫描:
- Windows Terminal 设置
- PowerShell Profile
- Oh My Posh 主题
"""

import json
import os
import re
import shutil
from pathlib import Path

from winstyles.domain.models import AssociatedFile, ScannedItem
from winstyles.domain.types import AssetType, ChangeType, SourceType
from winstyles.plugins.base import BaseScanner
from winstyles.utils.font_utils import find_font_paths, split_font_families


class WindowsTerminalScanner(BaseScanner):
    """
    Windows Terminal 配置扫描器
    """

    @property
    def id(self) -> str:
        return "windows_terminal"

    @property
    def name(self) -> str:
        return "Windows Terminal"

    @property
    def category(self) -> str:
        return "terminal"

    @property
    def description(self) -> str:
        return "扫描 Windows Terminal 配置"

    def supports_item(self, item: ScannedItem) -> bool:
        return item.key.startswith("windowsTerminal.")

    def _find_settings_path(self) -> Path | None:
        """查找 Windows Terminal 设置文件路径"""
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            return None

        packages_dir = Path(local_app_data) / "Packages"
        if not packages_dir.exists():
            return None

        # 查找 Windows Terminal 包目录
        for item in packages_dir.iterdir():
            if item.name.startswith("Microsoft.WindowsTerminal"):
                settings_path = item / "LocalState" / "settings.json"
                if settings_path.exists():
                    return settings_path

        return None

    def scan(self) -> list[ScannedItem]:
        """扫描 Windows Terminal 设置"""
        items: list[ScannedItem] = []

        settings_path = self._find_settings_path()
        if not settings_path:
            return items

        try:
            # 读取整个设置文件
            settings_content = self._fs.read_text(str(settings_path))
            settings = json.loads(settings_content)

            # 提取关键配置项
            key_settings = [
                ("defaultProfile", settings.get("defaultProfile")),
                ("theme", settings.get("theme")),
                ("useAcrylicInTabRow", settings.get("useAcrylicInTabRow")),
            ]

            for key, value in key_settings:
                if value is not None:
                    items.append(
                        ScannedItem(
                            category=self.category,
                            key=f"windowsTerminal.{key}",
                            current_value=value,
                            default_value=None,
                            change_type=ChangeType.MODIFIED,
                            source_type=SourceType.FILE,
                            source_path=str(settings_path),
                        )
                    )

            # 扫描 profiles.defaults
            defaults = settings.get("profiles", {}).get("defaults", {})
            for key, value in self._flatten_profile_defaults(defaults):
                associated_files: list[AssociatedFile] = []
                if key in {"font.face", "fontFace"}:
                    associated_files = self._build_font_associated_files(value)
                items.append(
                    ScannedItem(
                        category=self.category,
                        key=f"windowsTerminal.defaults.{key}",
                        current_value=value,
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.FILE,
                        source_path=str(settings_path),
                        associated_files=associated_files,
                    )
                )

        except Exception as e:
            print(f"WindowsTerminalScanner error: {e}")

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用 Windows Terminal 设置"""
        settings_path = self._find_settings_path()
        if not settings_path:
            return False

        if not item.key.startswith("windowsTerminal."):
            return False

        try:
            raw = self._fs.read_text(str(settings_path))
            settings = json.loads(raw)
        except Exception:
            settings = {}

        key_tail = item.key.replace("windowsTerminal.", "")
        if key_tail.startswith("defaults."):
            path_parts = ["profiles", "defaults", *key_tail.replace("defaults.", "", 1).split(".")]
        else:
            path_parts = key_tail.split(".")
        if not path_parts:
            return False

        try:
            self._set_nested_value(settings, path_parts, item.current_value)
            self._fs.write_text(
                str(settings_path),
                json.dumps(settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except Exception:
            return False

    def _flatten_profile_defaults(
        self,
        data: dict[str, object],
        prefix: str = "",
    ) -> list[tuple[str, object]]:
        """展开 profiles.defaults 的嵌套结构为点分键"""
        flattened: list[tuple[str, object]] = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flattened.extend(self._flatten_profile_defaults(value, full_key))
            else:
                flattened.append((full_key, value))
        return flattened

    def _set_nested_value(
        self,
        container: dict[str, object],
        path_parts: list[str],
        value: object,
    ) -> None:
        current: dict[str, object] = container
        for part in path_parts[:-1]:
            next_value = current.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
            current[part] = next_value
            current = next_value
        current[path_parts[-1]] = value

    def _build_font_associated_files(self, value: object) -> list[AssociatedFile]:
        files: list[AssociatedFile] = []
        for family in split_font_families(str(value)):
            for path in find_font_paths(family):
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


class PowerShellProfileScanner(BaseScanner):
    """
    PowerShell Profile 扫描器
    """

    @property
    def id(self) -> str:
        return "powershell_profile"

    @property
    def name(self) -> str:
        return "PowerShell Profile"

    @property
    def category(self) -> str:
        return "terminal"

    @property
    def description(self) -> str:
        return "扫描 PowerShell 配置文件"

    def supports_item(self, item: ScannedItem) -> bool:
        return item.key.startswith("powershell.profile.")

    def _get_profile_paths(self) -> list[Path]:
        """获取所有可能的 Profile 路径"""
        user_profile = os.environ.get("USERPROFILE", "")
        if not user_profile:
            return []

        paths = [
            Path(user_profile) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
            Path(user_profile)
            / "Documents"
            / "WindowsPowerShell"
            / "Microsoft.PowerShell_profile.ps1",
        ]

        return [p for p in paths if p.exists()]

    def scan(self) -> list[ScannedItem]:
        """扫描 PowerShell Profile"""
        items: list[ScannedItem] = []

        for profile_path in self._get_profile_paths():
            try:
                content = self._fs.read_text(str(profile_path))

                items.append(
                    ScannedItem(
                        category=self.category,
                        key=f"powershell.profile.{profile_path.parent.name}",
                        current_value=content,
                        default_value=None,
                        change_type=ChangeType.MODIFIED,
                        source_type=SourceType.FILE,
                        source_path=str(profile_path),
                        associated_files=[
                            AssociatedFile(
                                type=AssetType.SCRIPT,
                                name=profile_path.name,
                                path=str(profile_path),
                                exists=True,
                                size_bytes=None,
                                sha256=None,
                            )
                        ],
                    )
                )

            except Exception as e:
                print(f"PowerShellProfileScanner error: {e}")

        return items

    def apply(self, item: ScannedItem) -> bool:
        """应用 PowerShell Profile"""
        try:
            if not isinstance(item.current_value, str):
                return False
            target_path = self._resolve_target_profile_path(item)
            self._fs.write_text(str(target_path), item.current_value, encoding="utf-8")
            return True
        except Exception:
            return False

    def _resolve_target_profile_path(self, item: ScannedItem) -> Path:
        existing_paths = self._get_profile_paths()
        if item.key.endswith(".WindowsPowerShell"):
            for path in existing_paths:
                if path.parent.name == "WindowsPowerShell":
                    return path
        elif item.key.endswith(".PowerShell"):
            for path in existing_paths:
                if path.parent.name == "PowerShell":
                    return path

        user_profile = Path(os.environ.get("USERPROFILE", ""))
        if item.key.endswith(".WindowsPowerShell"):
            return (
                user_profile
                / "Documents"
                / "WindowsPowerShell"
                / "Microsoft.PowerShell_profile.ps1"
            )
        return user_profile / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"


class OhMyPoshScanner(BaseScanner):
    """
    Oh My Posh 检测扫描器
    """

    @property
    def id(self) -> str:
        return "oh_my_posh"

    @property
    def name(self) -> str:
        return "Oh My Posh"

    @property
    def category(self) -> str:
        return "terminal"

    @property
    def description(self) -> str:
        return "扫描 Oh My Posh 安装状态与主题配置"

    def supports_item(self, item: ScannedItem) -> bool:
        return item.key.startswith("ohMyPosh.")

    def scan(self) -> list[ScannedItem]:
        items: list[ScannedItem] = []

        executable = self._find_executable()
        installed = executable is not None
        executable_path = str(executable) if executable else ""

        installed_metadata: dict[str, object] = {
            "executable_path": executable_path,
            "readonly": True,
        }
        items.append(
            ScannedItem(
                category=self.category,
                key="ohMyPosh.installed",
                current_value=installed,
                default_value=None,
                change_type=ChangeType.MODIFIED,
                source_type=SourceType.FILE,
                source_path=executable_path or "oh-my-posh",
                metadata=installed_metadata,
            )
        )

        for profile_path in self._get_profile_paths():
            try:
                content = self._fs.read_text(str(profile_path))
            except Exception:
                continue

            theme_path = self._extract_theme_path(content, profile_path)
            if theme_path is None:
                continue

            associated_files: list[AssociatedFile] = []
            if theme_path.exists():
                try:
                    size = theme_path.stat().st_size
                except OSError:
                    size = None
                associated_files.append(
                    AssociatedFile(
                        type=AssetType.CONFIG,
                        name=theme_path.name,
                        path=str(theme_path),
                        exists=True,
                        size_bytes=size,
                        sha256=None,
                    )
                )

            items.append(
                ScannedItem(
                    category=self.category,
                    key=f"ohMyPosh.theme.{profile_path.parent.name}",
                    current_value=str(theme_path),
                    default_value=None,
                    change_type=ChangeType.MODIFIED,
                    source_type=SourceType.FILE,
                    source_path=str(profile_path),
                    associated_files=associated_files,
                    metadata={"readonly": True},
                )
            )

        return items

    def apply(self, item: ScannedItem) -> bool:
        # 当前阶段仅做检测，不自动改写 Oh My Posh 配置
        return item.key.startswith("ohMyPosh.")

    def _find_executable(self) -> Path | None:
        from_path = shutil.which("oh-my-posh")
        if from_path:
            path = Path(from_path)
            if path.exists():
                return path

        candidates = [
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs"
            / "oh-my-posh"
            / "bin"
            / "oh-my-posh.exe",
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "oh-my-posh"
            / "bin"
            / "oh-my-posh.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _get_profile_paths(self) -> list[Path]:
        user_profile = os.environ.get("USERPROFILE", "")
        if not user_profile:
            return []

        paths = [
            Path(user_profile) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
            Path(user_profile)
            / "Documents"
            / "WindowsPowerShell"
            / "Microsoft.PowerShell_profile.ps1",
        ]
        return [path for path in paths if path.exists()]

    def _extract_theme_path(self, content: str, profile_path: Path) -> Path | None:
        for line in content.splitlines():
            if "oh-my-posh" not in line or "init" not in line:
                continue
            match = re.search(r"--config\s+(\"[^\"]+\"|'[^']+'|[^\s|]+)", line)
            if not match:
                continue
            raw_path = match.group(1).strip().strip("'\"")
            return self._normalize_theme_path(raw_path, profile_path)

        for line in content.splitlines():
            match = re.search(r"POSH_THEME\s*=\s*(\"[^\"]+\"|'[^']+'|[^\s;]+)", line)
            if not match:
                continue
            raw_path = match.group(1).strip().strip("'\"")
            return self._normalize_theme_path(raw_path, profile_path)

        return None

    def _normalize_theme_path(self, raw_path: str, profile_path: Path) -> Path:
        expanded = self._expand_powershell_env(raw_path)
        candidate = Path(expanded)
        if candidate.is_absolute():
            return candidate
        return (profile_path.parent / candidate).resolve()

    def _expand_powershell_env(self, raw: str) -> str:
        expanded = raw
        for name, value in os.environ.items():
            expanded = re.sub(
                rf"\$env:{re.escape(name)}",
                lambda _: value,
                expanded,
                flags=re.IGNORECASE,
            )
        return os.path.expandvars(expanded)
