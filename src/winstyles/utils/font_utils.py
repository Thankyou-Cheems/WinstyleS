"""
字体工具库

提供字体文件查找和版本读取功能
"""

import os
import winreg
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
except ImportError:
    TTFont = None  # type: ignore


def find_font_path(font_name: str) -> Path | None:
    """
    根据字体名称查找字体文件路径
    
    Args:
        font_name: 字体名称，如 "Consolas" 或 "Maple Mono"
        
    Returns:
        Path: 字体文件绝对路径，如果未找到则返回 None
    """
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
        ) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    i += 1

                    # 注册表键名通常包含 "(TrueType)" 等后缀
                    # 例如: "Consolas (TrueType)", "Arial Bold (TrueType)"
                    real_name = name.split("(")[0].strip()

                    # 简单的不区分大小写匹配
                    # TODO: 支持更复杂的匹配逻辑（如 Regular/Bold/Italic 处理）
                    if real_name.lower() == font_name.lower():
                        return _resolve_font_path(value)

                    # 尝试前缀匹配
                    if font_name.lower() in real_name.lower():
                        # 如果没有精确匹配，暂存这个模糊匹配，继续找精确匹配
                        # 这里简单起见先直接返回，或者需要更好的评分机制
                        # 暂时只返回精确匹配
                        pass

                except OSError:
                    break
    except Exception:
        pass

    return None


def _resolve_font_path(filename: str) -> Path | None:
    """解析字体文件名为绝对路径"""
    # 很多字体直接在 C:\Windows\Fonts 下
    system_fonts = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Fonts"
    path = system_fonts / filename

    if path.exists():
        return path

    # 有些字体注册的是绝对路径
    path = Path(filename)
    if path.exists():
        return path

    return None


def get_font_version(file_path: Path) -> str | None:
    """
    读取字体文件中的版本信息的
    
    Args:
        file_path: 字体文件路径
        
    Returns:
        str: 版本字符串 (如 "Version 1.00"), 失败返回 None
    """
    if not TTFont:
        return None

    try:
        font = TTFont(file_path)
        # ID 5 是 Version 字符串
        # 遍历 name records 寻找英文版本信息
        version = None
        for record in font["name"].names:
            if record.nameID == 5:
                # 尝试获取 Unicode 字符串
                text = record.toUnicode()
                # 优先取 PlatformID=3 (Windows) 的记录
                if record.platformID == 3:
                     return text
                version = text

        return version
    except Exception:
        return None
