"""
字体工具库

提供字体文件查找和版本读取功能
"""

import fnmatch
import importlib
import json
import os
import winreg
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict


class OpenSourceFontMatch(TypedDict):
    name: str
    patterns: list[str]
    homepage: str
    download: str
    license: str
    description: str


TTFontLoader = Callable[[Path], Any]
_TTFONT_LOADER: TTFontLoader | None = None

try:
    _ttlib = importlib.import_module("fontTools.ttLib")
    _ttfont = getattr(_ttlib, "TTFont", None)
    if callable(_ttfont):
        _TTFONT_LOADER = _ttfont
except Exception:
    _TTFONT_LOADER = None

GENERIC_FONT_FAMILIES = {
    "serif",
    "sans-serif",
    "sans",
    "monospace",
    "system-ui",
    "cursive",
    "fantasy",
    "emoji",
    "math",
    "fangsong",
}


def _default_opensource_db_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "opensource_fonts.json"


@lru_cache(maxsize=4)
def _load_opensource_font_entries(db_path: str) -> tuple[OpenSourceFontMatch, ...]:
    path = Path(db_path)
    if not path.exists():
        return ()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()

    if not isinstance(payload, dict):
        return ()

    raw_fonts = payload.get("fonts", [])
    if not isinstance(raw_fonts, list):
        return ()

    entries: list[OpenSourceFontMatch] = []
    for raw in raw_fonts:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name", "")).strip()
        if not name:
            continue

        raw_patterns = raw.get("patterns", [])
        patterns: list[str] = []
        if isinstance(raw_patterns, list):
            for pattern in raw_patterns:
                text = str(pattern).strip()
                if text:
                    patterns.append(text)

        entries.append(
            OpenSourceFontMatch(
                name=name,
                patterns=patterns,
                homepage=str(raw.get("homepage", "")),
                download=str(raw.get("download", "")),
                license=str(raw.get("license", "")),
                description=str(raw.get("description", "")),
            )
        )

    return tuple(entries)


def identify_opensource(font_name: str, db_path: Path | None = None) -> OpenSourceFontMatch | None:
    """
    根据字体名识别是否为开源字体。

    Args:
        font_name: 字体名称（如 "Maple Mono SC NF"）
        db_path: 可选数据库路径，默认读取 data/opensource_fonts.json

    Returns:
        匹配到时返回字体信息，否则返回 None。
    """
    normalized = _normalize_font_name(font_name)
    if not normalized:
        return None

    raw_name = str(font_name).strip().lower()
    lookup_path = db_path if db_path is not None else _default_opensource_db_path()
    for entry in _load_opensource_font_entries(str(lookup_path)):
        patterns = entry.get("patterns", [])
        for pattern in patterns:
            normalized_pattern = _normalize_font_name(pattern)
            pattern_lower = str(pattern).strip().lower()
            if fnmatch.fnmatch(normalized, normalized_pattern) or fnmatch.fnmatch(
                raw_name, pattern_lower
            ):
                return entry

    return None


def find_font_path(font_name: str) -> Path | None:
    """
    根据字体名称查找字体文件路径

    Args:
        font_name: 字体名称，如 "Consolas" 或 "Maple Mono"

    Returns:
        Path: 字体文件绝对路径，如果未找到则返回 None
    """
    paths = find_font_paths(font_name)
    if not paths:
        return None
    return paths[0]


def find_font_paths(font_name: str) -> list[Path]:
    """
    根据字体名称查找候选字体文件路径（可能多个）
    """
    query = _normalize_font_name(font_name)
    if not query:
        return []

    exact_matches: list[Path] = []
    fuzzy_matches: list[Path] = []

    for root, reg_path in (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
    ):
        try:
            with winreg.OpenKey(root, reg_path) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        i += 1
                    except OSError:
                        break

                    reg_name = _normalize_font_name(name)
                    path = _resolve_font_path(str(value))
                    if path is None:
                        continue

                    if reg_name == query:
                        exact_matches.append(path)
                    elif query in reg_name or reg_name in query:
                        fuzzy_matches.append(path)
        except Exception:
            continue

    return _dedupe_paths(exact_matches + fuzzy_matches)


def split_font_families(font_family: str) -> list[str]:
    """
    解析 CSS/配置中的 font family 字符串为字体名列表。
    """
    parts = [p.strip().strip("'").strip('"') for p in str(font_family).split(",")]
    result = []
    for part in parts:
        if not part:
            continue
        if part.lower() in GENERIC_FONT_FAMILIES:
            continue
        result.append(part)
    return result


def _resolve_font_path(filename: str) -> Path | None:
    """解析字体文件名为绝对路径"""
    # 很多字体直接在 C:\Windows\Fonts 下
    system_fonts = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Fonts"
    path = system_fonts / filename

    if path.exists():
        return path

    # 用户级字体目录（按用户安装）
    user_fonts = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts"
    if str(user_fonts):
        user_path = user_fonts / filename
        if user_path.exists():
            return user_path

    # 有些字体注册的是绝对路径
    path = Path(filename)
    if path.exists():
        return path

    return None


def _normalize_font_name(name: str) -> str:
    raw = str(name).split("(")[0].strip().lower()
    return " ".join(raw.split())


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def get_font_version(file_path: Path) -> str | None:
    """
    读取字体文件中的版本信息的

    Args:
        file_path: 字体文件路径

    Returns:
        str: 版本字符串 (如 "Version 1.00"), 失败返回 None
    """
    if _TTFONT_LOADER is None:
        return None

    try:
        font = _TTFONT_LOADER(file_path)
        # ID 5 是 Version 字符串
        # 遍历 name records 寻找英文版本信息
        version = None
        name_table = font["name"]

        for record in getattr(name_table, "names", []):
            if getattr(record, "nameID", None) == 5:
                text = str(record.toUnicode())
                # 优先取 PlatformID=3 (Windows) 的记录
                if getattr(record, "platformID", None) == 3:
                    return text
                version = text

        return version
    except Exception:
        return None
