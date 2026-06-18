"""
ReportGenerator - 扫描报告生成器

生成人类可读的扫描结果报告，包括:
- 变更分类（用户自定义 vs 系统差异 vs 系统标准）
- 开源字体识别
- Markdown/HTML 格式输出
"""

from __future__ import annotations

import fnmatch
import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from importlib import resources
from pathlib import Path
from urllib.parse import urlparse

from winstyles.core.update_checker import UpdateChecker, UpdateInfo
from winstyles.domain.models import OpenSourceFontInfo, ScannedItem, ScanResult
from winstyles.domain.types import ChangeType
from winstyles.utils.font_utils import find_font_path, get_font_version

_ALLOWED_HREF_SCHEMES = {"http", "https", "mailto"}


def _winstyles_resource_path(*parts: str) -> Path:
    """Resolve packaged resources first, then fall back to the source tree."""
    try:
        candidate = resources.files("winstyles").joinpath(*parts)
        path = Path(str(candidate))
        if path.exists():
            return path
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        pass

    return Path(__file__).resolve().parents[3].joinpath(*parts)


@dataclass
class ClassifiedChanges:
    """分类后的变更"""

    user_customizations: list[ScannedItem] = field(default_factory=list)
    version_differences: list[ScannedItem] = field(default_factory=list)
    system_defaults: list[ScannedItem] = field(default_factory=list)
    detected_fonts: list[tuple[ScannedItem, OpenSourceFontInfo, UpdateInfo | None]] = field(
        default_factory=list
    )


class ReportGenerator:
    """扫描报告生成器"""

    # 已知的用户自定义配置键
    USER_CUSTOM_KEYS = [
        "windowsTerminal.defaults.font.face",
        "windowsTerminal.theme",
        "vscode.editor.fontFamily",
        "vscode.workbench.colorTheme",
        "vscode.workbench.iconTheme",
        "vscode.terminal.integrated.fontFamily",
        "theme.accentColor",
        "wallpaper.path",
        "cursor.scheme",
    ]

    # 已知的系统版本差异
    VERSION_DIFF_KEYS = {
        "Helv": ("MS Sans Serif", "Microsoft Sans Serif"),
        "Tms Rmn": ("MS Serif", "Times New Roman"),
    }

    # 系统默认字体（不视为用户自定义）
    SYSTEM_DEFAULT_FONTS = [
        "Cascadia Mono",
        "Cascadia Code",
        "Consolas",
        "Courier New",
        "Segoe UI",
        "Microsoft YaHei",
        "Microsoft JhengHei",
        "SimSun",
        "NSimSun",
        "SimHei",
    ]

    def __init__(self, scan_result: ScanResult, check_updates: bool = True) -> None:
        self.scan_result = scan_result
        self.check_updates = check_updates
        self.update_checker = UpdateChecker()
        self._font_db: list[OpenSourceFontInfo] = []
        self._version_diffs: dict[str, dict[str, str]] = {}
        self._load_font_db()

    def _load_font_db(self) -> None:
        """加载开源字体数据库 (优先远程，失败回退本地)"""
        data = None

        # 尝试远程获取
        if self.check_updates:
            data = self.update_checker.fetch_remote_db()

        # 回退到本地
        if not data:
            db_path = _winstyles_resource_path("data", "opensource_fonts.json")
            if db_path.exists():
                try:
                    with open(db_path, encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    pass

        if not data:
            return

        for font in data.get("fonts", []):
            self._font_db.append(
                OpenSourceFontInfo(
                    name=font["name"],
                    patterns=font.get("patterns", []),
                    homepage=font.get("homepage", ""),
                    download=font.get("download", ""),
                    license=font.get("license", ""),
                    description=font.get("description", ""),
                )
            )

        version_diffs = data.get("version_differences", {})
        self._version_diffs = version_diffs.get("font_substitutes", {})

    def _match_font(self, font_name: str) -> OpenSourceFontInfo | None:
        """匹配开源字体"""
        for font_info in self._font_db:
            for pattern in font_info.patterns:
                if fnmatch.fnmatch(font_name, pattern):
                    return font_info
        return None

    def _is_user_customization(self, item: ScannedItem) -> bool:
        """判断是否为用户自定义"""
        # 检查是否为已知的用户自定义键
        for key in self.USER_CUSTOM_KEYS:
            if key in item.key:
                # 检查是否为非系统默认值
                value = str(item.current_value)
                if not any(df in value for df in self.SYSTEM_DEFAULT_FONTS):
                    return True

        # 检查字体值是否匹配开源字体
        value = str(item.current_value)
        if self._match_font(value):
            return True

        return False

    def _is_version_difference(self, item: ScannedItem) -> bool:
        """判断是否为版本差异"""
        if item.key in self.VERSION_DIFF_KEYS:
            expected = self.VERSION_DIFF_KEYS[item.key]
            actual = str(item.current_value)
            default = str(item.default_value) if item.default_value else ""
            return actual in expected or default in expected

        # FontLink 条目通常是系统默认
        if "FontLink" in item.source_path:
            return True

        return False

    def classify_changes(self) -> ClassifiedChanges:
        """将变更分类"""
        result = ClassifiedChanges()

        for item in self.scan_result.items:
            # 检测开源字体
            value = str(item.current_value)
            font_info = self._match_font(value)
            if font_info:
                update_info = None
                if self.check_updates:
                    # 1. 查找本地文件路径
                    # 注意：value 是字体名称 (如 "Maple Mono SC NF")，需要解析为文件路径
                    font_path = find_font_path(value)
                    local_version = get_font_version(font_path) if font_path else None

                    # 2. 检查更新
                    update_info = self.update_checker.check_font_update(font_info, local_version)

                result.detected_fonts.append((item, font_info, update_info))

            # 分类
            if self._is_user_customization(item):
                result.user_customizations.append(item)
            elif self._is_version_difference(item):
                result.version_differences.append(item)
            else:
                # 如果有默认值且不同，视为修改
                if item.change_type == ChangeType.MODIFIED:
                    result.user_customizations.append(item)
                else:
                    result.system_defaults.append(item)

        return result

    def generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        classified = self.classify_changes()
        lines: list[str] = []

        # 标题
        lines.append("# WinstyleS 扫描报告\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**操作系统**: {self.scan_result.os_version}\n")

        # 摘要
        lines.append("\n## 📊 摘要\n")
        lines.append("| 类别 | 用户自定义 | 系统差异 | 系统标准 |")
        lines.append("|------|-----------|---------|---------|")

        # 按类别统计
        categories: dict[str, dict[str, int]] = {}
        for item in classified.user_customizations:
            cat = item.category
            if cat not in categories:
                categories[cat] = {"custom": 0, "diff": 0, "default": 0}
            categories[cat]["custom"] += 1

        for item in classified.version_differences:
            cat = item.category
            if cat not in categories:
                categories[cat] = {"custom": 0, "diff": 0, "default": 0}
            categories[cat]["diff"] += 1

        for item in classified.system_defaults:
            cat = item.category
            if cat not in categories:
                categories[cat] = {"custom": 0, "diff": 0, "default": 0}
            categories[cat]["default"] += 1

        for cat, counts in sorted(categories.items()):
            lines.append(f"| {cat} | {counts['custom']} | {counts['diff']} | {counts['default']} |")

        # 用户自定义配置
        if classified.user_customizations:
            lines.append("\n## 🎨 用户自定义配置\n")

            # 按类别分组
            by_category: dict[str, list[ScannedItem]] = {}
            for item in classified.user_customizations:
                if item.category not in by_category:
                    by_category[item.category] = []
                by_category[item.category].append(item)

            for category, items in sorted(by_category.items()):
                lines.append(f"\n### {category.title()}\n")
                for item in items:
                    default_str = f" (默认: {item.default_value})" if item.default_value else ""
                    lines.append(f"- **{item.key}**: `{item.current_value}`{default_str}")

        # 检测到的开源字体
        if classified.detected_fonts:
            lines.append("\n## 🔤 检测到的开源字体\n")
            lines.append("| 字体 | 版本 | 许可证 | 说明 | 链接 |")
            lines.append("|------|------|--------|------|------|")

            seen_fonts: set[str] = set()
            for item, font_info, update_info in classified.detected_fonts:
                if font_info.name in seen_fonts:
                    continue
                seen_fonts.add(font_info.name)

                version_str = "未知"
                if update_info:
                    local_ver = update_info.current_version or "Unknown"
                    if update_info.has_update:
                        version_str = f"{local_ver} → **{update_info.latest_version}** 🆕"
                    else:
                        version_str = f"{local_ver} (最新)"

                homepage_link = f"[主页]({font_info.homepage})" if font_info.homepage else "-"
                download_link = f"[下载]({font_info.download})" if font_info.download else "-"

                lines.append(
                    f"| {font_info.name} | {version_str} | {font_info.license} | "
                    f"{font_info.description} | {homepage_link} / {download_link} |"
                )

        # 系统版本差异
        version_diff_count = len(classified.version_differences)
        if version_diff_count > 0:
            lines.append("\n## ⚙️ 系统版本差异\n")
            lines.append("> 这些差异是 Windows 不同版本间的正常差异，不是您的自定义修改。\n")

            # 只显示真正的版本差异，不显示所有 FontLink
            real_diffs = [
                item
                for item in classified.version_differences
                if item.key in self.VERSION_DIFF_KEYS
            ]
            fontlink_count = version_diff_count - len(real_diffs)

            for item in real_diffs:
                default_str = f" (默认库: {item.default_value})" if item.default_value else ""
                lines.append(f"- `{item.key}`: {item.current_value}{default_str}")

            if fontlink_count > 0:
                lines.append(f"\n*另有 {fontlink_count} 项 FontLink 系统配置 (已隐藏)*")

        # 系统标准配置
        default_count = len(classified.system_defaults)
        if default_count > 0:
            lines.append("\n## 📦 系统标准配置\n")
            lines.append(f"*共 {default_count} 项系统标准配置 (已隐藏)*\n")

        return "\n".join(lines)

    def generate_html(self, embedded: bool = False) -> str:
        """生成 HTML 格式报告"""
        markdown_content = self.generate_markdown()

        # 简单的 Markdown 到 HTML 转换
        html_content = self._markdown_to_html(markdown_content)

        # Scoped CSS for embedded use
        css = """
            .winstyles-report {
                --bg-color: #0d1117;
                --text-color: #c9d1d9;
                --heading-color: #58a6ff;
                --border-color: #30363d;
                --table-bg: #161b22;
                --code-bg: #1f2428;
                --accent: #58a6ff;

                font-family: -apple-system, BlinkMacSystemFont, \
                    'Segoe UI', Helvetica, Arial, sans-serif;
                color: var(--text-color);
                line-height: 1.6;
            }

            .winstyles-report h1 {
                color: var(--heading-color);
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 0.5rem;
                margin-top: 0;
            }
            .winstyles-report h2 { color: var(--heading-color); margin-top: 2rem; }
            .winstyles-report h3 { color: var(--text-color); }
            .winstyles-report table {
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
                background-color: var(--table-bg);
            }
            .winstyles-report th, .winstyles-report td {
                border: 1px solid var(--border-color);
                padding: 0.75rem;
                text-align: left;
            }
            .winstyles-report th { background-color: var(--code-bg); }
            .winstyles-report code {
                background-color: var(--code-bg);
                padding: 0.2rem 0.4rem;
                border-radius: 3px;
                font-family: 'Cascadia Code', Consolas, monospace;
            }
            .winstyles-report a { color: var(--accent); text-decoration: none; }
            .winstyles-report a:hover { text-decoration: underline; }
            .winstyles-report blockquote {
                border-left: 3px solid var(--accent);
                margin: 1rem 0;
                padding-left: 1rem;
                color: #8b949e;
            }
            .winstyles-report ul { padding-left: 1.5rem; }
            .winstyles-report li { margin: 0.5rem 0; }
        """

        if embedded:
            return f"""<style>{css}</style><div class="winstyles-report">{html_content}</div>"""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WinstyleS 扫描报告</title>
    <style>
        :root {{
            --bg-color: #0d1117;
            --text-color: #c9d1d9;
            --heading-color: #58a6ff;
            --border-color: #30363d;
            --table-bg: #161b22;
            --code-bg: #1f2428;
            --accent: #58a6ff;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont,
                'Segoe UI', Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        h1 {{
            color: var(--heading-color);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }}
        h2 {{ color: var(--heading-color); margin-top: 2rem; }}
        h3 {{ color: var(--text-color); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background-color: var(--table-bg);
        }}
        th, td {{
            border: 1px solid var(--border-color);
            padding: 0.75rem;
            text-align: left;
        }}
        th {{ background-color: var(--code-bg); }}
        code {{
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Cascadia Code', Consolas, monospace;
        }}
        a {{ color: var(--accent); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        blockquote {{
            border-left: 3px solid var(--accent);
            margin: 1rem 0;
            padding-left: 1rem;
            color: #8b949e;
        }}
        ul {{ padding-left: 1.5rem; }}
        li {{ margin: 0.5rem 0; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

    def _markdown_to_html(self, md: str) -> str:
        """简单的 Markdown 到 HTML 转换"""

        lines = md.split("\n")
        html_lines: list[str] = []
        in_table = False
        in_list = False

        for line in lines:
            # 表格
            if line.startswith("|"):
                if not in_table:
                    html_lines.append("<table>")
                    in_table = True

                if "---" in line:
                    continue

                cells = [c.strip() for c in line.split("|")[1:-1]]
                tag = "th" if not any("<tr>" in ln for ln in html_lines[-5:]) else "td"
                row = "".join(f"<{tag}>{self._inline_md(c)}</{tag}>" for c in cells)
                html_lines.append(f"<tr>{row}</tr>")
                continue
            elif in_table:
                html_lines.append("</table>")
                in_table = False

            # 标题
            if line.startswith("# "):
                html_lines.append(f"<h1>{self._inline_md(line[2:])}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{self._inline_md(line[3:])}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{self._inline_md(line[4:])}</h3>")
            # 引用
            elif line.startswith("> "):
                html_lines.append(f"<blockquote>{self._inline_md(line[2:])}</blockquote>")
            # 列表
            elif line.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{self._inline_md(line[2:])}</li>")
            elif in_list and not line.startswith("- "):
                html_lines.append("</ul>")
                in_list = False
                if line.strip():
                    html_lines.append(f"<p>{self._inline_md(line)}</p>")
            # 普通段落
            elif line.strip():
                html_lines.append(f"<p>{self._inline_md(line)}</p>")

        if in_table:
            html_lines.append("</table>")
        if in_list:
            html_lines.append("</ul>")

        return "\n".join(html_lines)

    def _inline_md(self, text: str) -> str:
        """处理行内 Markdown"""
        text = html.escape(text, quote=True)

        # 链接
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", self._render_link, text)
        # 粗体
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        # 行内代码
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        # 斜体
        text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)

        return text

    @staticmethod
    def _render_link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = html.unescape(match.group(2)).strip()
        if not ReportGenerator._is_safe_href(href):
            return label

        escaped_href = html.escape(href, quote=True)
        return f'<a href="{escaped_href}">{label}</a>'

    @staticmethod
    def _is_safe_href(href: str) -> bool:
        if not href or href.startswith("//") or any(ord(char) < 32 for char in href):
            return False

        parsed = urlparse(href)
        if parsed.scheme and parsed.scheme.lower() not in _ALLOWED_HREF_SCHEMES:
            return False

        return True
