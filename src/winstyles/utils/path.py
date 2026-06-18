"""
路径工具 - 处理 Windows 环境变量和路径规范化
"""

import os
import re
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

_WINDOWS_ENV_VAR_RE = re.compile(r"%([^%]+)%")


def _get_env_case_insensitive(name: str) -> str | None:
    """Look up environment variables using Windows-style case-insensitive names."""
    value = os.environ.get(name)
    if value:
        return value

    lowered_name = name.lower()
    empty_match = value if value is not None else None
    for env_name, env_value in os.environ.items():
        if env_name.lower() == lowered_name:
            if env_value:
                return env_value
            if empty_match is None:
                empty_match = env_value

    return empty_match


def _expand_environment_vars(path: str) -> str:
    """Expand both POSIX-style and Windows %VAR% environment references."""

    def replace_windows_var(match: re.Match[str]) -> str:
        value = _get_env_case_insensitive(match.group(1))
        return match.group(0) if value is None else value

    return os.path.expandvars(_WINDOWS_ENV_VAR_RE.sub(replace_windows_var, path))


def expand_path_vars(path: str, normalize_separators: bool = False) -> str:
    """
    展开路径中的环境变量，不解析为绝对路径。

    Args:
        path: 包含环境变量的路径
        normalize_separators: 是否将 Windows 反斜杠规范化为当前平台分隔符

    Returns:
        展开环境变量后的路径
    """
    expanded = _expand_environment_vars(path)
    if normalize_separators:
        return _normalize_separators(expanded)
    return expanded


def _normalize_separators(path: str) -> str:
    if os.sep == "/":
        return path.replace("\\", os.sep)
    return path


def _resolve_path(path: str) -> str:
    normalized = expand_path_vars(path, normalize_separators=True)
    return str(Path(normalized).resolve())


def _is_same_or_child(path: str, parent: str) -> bool:
    folded_path = path.lower()
    folded_parent = parent.lower()

    if folded_path == folded_parent:
        return True

    return folded_path.startswith(f"{folded_parent.rstrip(os.sep)}{os.sep}")


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
    return _resolve_path(path)


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
    path = _resolve_path(path)

    # 按照路径长度排序，优先匹配更长的路径
    sorted_vars = sorted(
        COMMON_VARS,
        key=lambda x: len(_get_env_case_insensitive(x[0]) or ""),
        reverse=True,
    )

    for var_name, var_placeholder in sorted_vars:
        var_value = _get_env_case_insensitive(var_name)
        if not var_value:
            continue

        # 规范化环境变量的值
        var_value = _resolve_path(var_value)

        # 不区分大小写比较 (Windows)
        if _is_same_or_child(path, var_value):
            # 替换为环境变量
            relative_part = path[len(var_value) :]
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
    return _resolve_path(path)


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
    user_profile = _get_env_case_insensitive("USERPROFILE") or ""
    if not user_profile:
        return False

    normalized_path = normalize_path(path)
    normalized_profile = normalize_path(user_profile)

    return _is_same_or_child(normalized_path, normalized_profile)
