"""
插件系统 - 扫描器插件
"""

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

__all__ = [
    "BaseScanner",
    "FontSubstitutesScanner",
    "FontLinkScanner",
    "InstalledFontsScanner",
    "WindowsTerminalScanner",
    "PowerShellProfileScanner",
    "OhMyPoshScanner",
    "ThemeScanner",
    "WallpaperScanner",
    "CursorScanner",
    "VSCodeScanner",
]
