"""
类型定义 - 枚举和类型别名
"""

from enum import Enum


class ChangeType(str, Enum):
    """变更类型"""

    ADDED = "added"  # 新增配置（默认值库中不存在）
    MODIFIED = "modified"  # 修改配置（与默认值不同）
    DEFAULT = "default"  # 保持默认（与默认值相同）
    REMOVED = "removed"  # 已删除（仅在对比两个包时使用）


class Category(str, Enum):
    """配置类别"""

    FONTS = "fonts"  # 系统字体
    THEME = "theme"  # 主题外观
    WALLPAPER = "wallpaper"  # 壁纸
    CURSOR = "cursor"  # 鼠标指针
    TERMINAL = "terminal"  # 终端配置
    VSCODE = "vscode"  # VS Code
    BROWSER = "browser"  # 浏览器
    EXPLORER = "explorer"  # 资源管理器


class SourceType(str, Enum):
    """配置来源类型"""

    REGISTRY = "registry"  # Windows 注册表
    FILE = "file"  # 配置文件
    SYSTEM_API = "system_api"  # Windows API


class AssetType(str, Enum):
    """资源文件类型"""

    FONT = "font"  # 字体文件
    IMAGE = "image"  # 图片（壁纸、背景等）
    CURSOR = "cursor"  # 鼠标指针
    SCRIPT = "script"  # 脚本文件
    CONFIG = "config"  # 配置文件
