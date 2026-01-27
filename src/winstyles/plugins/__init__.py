"""
插件系统 - 扫描器插件
"""

from winstyles.plugins.base import BaseScanner
from winstyles.plugins.cursor import CursorScanner
from winstyles.plugins.fonts import FontLinkScanner, FontSubstitutesScanner
from winstyles.plugins.terminal import PowerShellProfileScanner, WindowsTerminalScanner
from winstyles.plugins.theme import ThemeScanner
from winstyles.plugins.vscode import VSCodeScanner
from winstyles.plugins.wallpaper import WallpaperScanner

__all__ = [
    "BaseScanner",
    "FontSubstitutesScanner",
    "FontLinkScanner",
    "WindowsTerminalScanner",
    "PowerShellProfileScanner",
    "ThemeScanner",
    "WallpaperScanner",
    "CursorScanner",
    "VSCodeScanner",
]
