"""
路径工具 - 处理 Windows 环境变量和路径规范化
"""

import os
from pathlib import Path

# 常用环境变量及其对应的系统变量名
COMMON_VARS = [
    # 用户相关
    ("USERPROFILE", "%USERPROFILE%"),
    ("APPDATA", "%APPDATA%"),
    ("LOCALAPPDATA", "%LOCALAPPDATA%"),
    ("TEMP", "%TEMP%"),
    ("TMP", "%TMP%"),
    # 系统相关
    ("PROGRAMDATA", "%PROGRAMDATA%"),
    ("PROGRAMFILES", "%PROGRAMFILES%"),
    ("PROGRAMFILES(X86)", "%PROGRAMFILES(X86)%"),
    ("WINDIR", "%WINDIR%"),
    ("SYSTEMROOT", "%SYSTEMROOT%"),
    ("SYSTEMDRIVE", "%SYSTEMDRIVE%"),
]


def expand_vars(path: str) -> str:
    """
    展开路径中的环境变量

    将 %AppData% 等环境变量展开为实际路径。

    Args:
        path: 包含环境变量的路径

    Returns:
        展开后的绝对路径

    Examples:
        >>> expand_vars("%APPDATA%\\Code\\User\\settings.json")
        "C:\\Users\\Alice\\AppData\\Roaming\\Code\\User\\settings.json"
    """
    # 使用 os.path.expandvars 展开环境变量
    expanded = os.path.expandvars(path)

    # 规范化路径
    return str(Path(expanded).resolve())


def collapse_vars(path: str, prefer_vars: bool = True) -> str:
    """
    将路径中的用户特定部分替换为环境变量

    这对于导出配置非常重要，确保配置可以在其他机器上使用。

    Args:
        path: 绝对路径
        prefer_vars: 是否优先使用环境变量

    Returns:
        包含环境变量的路径

    Examples:
        >>> collapse_vars("C:\\Users\\Alice\\AppData\\Roaming\\Code")
        "%APPDATA%\\Code"
    """
    if not prefer_vars:
        return path

    # 规范化输入路径
    path = str(Path(path).resolve())

    # 按照路径长度排序，优先匹配更长的路径
    sorted_vars = sorted(
        COMMON_VARS,
        key=lambda x: len(os.environ.get(x[0], "")),
        reverse=True,
    )

    for var_name, var_placeholder in sorted_vars:
        var_value = os.environ.get(var_name, "")
        if not var_value:
            continue

        # 规范化环境变量的值
        var_value = str(Path(var_value).resolve())

        # 不区分大小写比较 (Windows)
        if path.lower().startswith(var_value.lower()):
            # 替换为环境变量
            relative_part = path[len(var_value):]
            return f"{var_placeholder}{relative_part}"

    return path


def normalize_path(path: str) -> str:
    """
    规范化路径

    - 解析相对路径为绝对路径
    - 统一使用反斜杠 (Windows 风格)
    - 移除多余的分隔符

    Args:
        path: 原始路径

    Returns:
        规范化后的路径
    """
    # 先展开环境变量
    expanded = os.path.expandvars(path)

    # 解析为绝对路径
    resolved = Path(expanded).resolve()

    # 返回字符串形式
    return str(resolved)


def get_env_vars_mapping() -> dict[str, str]:
    """
    获取常用环境变量的当前值映射

    Returns:
        {变量名: 值} 的字典
    """
    mapping = {}
    for var_name, _ in COMMON_VARS:
        value = os.environ.get(var_name)
        if value:
            mapping[var_name] = normalize_path(value)
    return mapping


def is_under_user_profile(path: str) -> bool:
    """
    检查路径是否在用户目录下

    Args:
        path: 要检查的路径

    Returns:
        是否在用户目录下
    """
    user_profile = os.environ.get("USERPROFILE", "")
    if not user_profile:
        return False

    normalized_path = normalize_path(path)
    normalized_profile = normalize_path(user_profile)

    return normalized_path.lower().startswith(normalized_profile.lower())
