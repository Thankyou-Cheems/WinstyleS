"""
TerminalScanner - 终端配置扫描器

扫描:
- Windows Terminal 设置
- PowerShell Profile
- Oh My Posh 主题
"""

from typing import List
from pathlib import Path
import os
import json

from winstyles.plugins.base import BaseScanner
from winstyles.domain.models import ScannedItem, AssociatedFile
from winstyles.domain.types import SourceType, AssetType


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
    
    def scan(self) -> List[ScannedItem]:
        """扫描 Windows Terminal 设置"""
        items: List[ScannedItem] = []
        
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
                    items.append(ScannedItem(
                        category=self.category,
                        key=f"windowsTerminal.{key}",
                        current_value=value,
                        source_type=SourceType.FILE,
                        source_path=str(settings_path),
                    ))
            
            # 扫描 profiles.defaults
            defaults = settings.get("profiles", {}).get("defaults", {})
            for key, value in defaults.items():
                items.append(ScannedItem(
                    category=self.category,
                    key=f"windowsTerminal.defaults.{key}",
                    current_value=value,
                    source_type=SourceType.FILE,
                    source_path=str(settings_path),
                ))
                
        except Exception as e:
            print(f"WindowsTerminalScanner error: {e}")
        
        return items
    
    def apply(self, item: ScannedItem) -> bool:
        """应用 Windows Terminal 设置"""
        # TODO: 实现设置应用逻辑
        return False


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
    
    def _get_profile_paths(self) -> List[Path]:
        """获取所有可能的 Profile 路径"""
        user_profile = os.environ.get("USERPROFILE", "")
        if not user_profile:
            return []
        
        paths = [
            Path(user_profile) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
            Path(user_profile) / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
        ]
        
        return [p for p in paths if p.exists()]
    
    def scan(self) -> List[ScannedItem]:
        """扫描 PowerShell Profile"""
        items: List[ScannedItem] = []
        
        for profile_path in self._get_profile_paths():
            try:
                content = self._fs.read_text(str(profile_path))
                
                items.append(ScannedItem(
                    category=self.category,
                    key=f"powershell.profile.{profile_path.parent.name}",
                    current_value=content,
                    source_type=SourceType.FILE,
                    source_path=str(profile_path),
                    associated_files=[
                        AssociatedFile(
                            type=AssetType.SCRIPT,
                            name=profile_path.name,
                            path=str(profile_path),
                            exists=True,
                        )
                    ],
                ))
                
            except Exception as e:
                print(f"PowerShellProfileScanner error: {e}")
        
        return items
    
    def apply(self, item: ScannedItem) -> bool:
        """应用 PowerShell Profile"""
        # TODO: 实现应用逻辑
        return False
