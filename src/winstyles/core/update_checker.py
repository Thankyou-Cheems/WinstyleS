"""
UpdateChecker - 资源更新检查器

负责检查:
1. 开源字体库的更新 (opensource_fonts.json)
2. 已安装开源字体的版本更新
"""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

from winstyles.domain.models import FontInfo


@dataclass
class UpdateInfo:
    """更新信息"""
    current_version: str
    latest_version: str
    download_url: str
    has_update: bool


class UpdateChecker:
    """更新检查器"""

    # 远程字体数据库 URL (指向 GitHub Main 分支)
    # 远程字体数据库 URL (使用 JsDelivr CDN 加速)
    REMOTE_DB_URL = "https://cdn.jsdelivr.net/gh/Thankyou-Cheems/WinstyleS@main/data/opensource_fonts.json"
    
    # 社区维护的字体数据库 (Source: braver/programmingfonts)
    COMMUNITY_DB_URL = "https://cdn.jsdelivr.net/gh/braver/programmingfonts@master/fonts.json"

    def __init__(self) -> None:
        self._font_db_cache: dict[str, Any] | None = None

    def fetch_remote_db(self) -> dict[str, Any] | None:
        """获取远程字体数据库 (合并官方库与社区库)"""
        if self._font_db_cache:
            return self._font_db_cache

        main_data = self._fetch_json(self.REMOTE_DB_URL)
        community_data = self._fetch_json(self.COMMUNITY_DB_URL)
        
        if not main_data and not community_data:
            return None
            
        result = main_data if main_data else {"fonts": [], "version_differences": {}}
        
        if community_data:
            community_fonts = self._adapt_community_db(community_data)
            # 合并策略：保留 main_data 中的条目 (因为有经过调优的 patterns)，追加新的
            existing_names = {f["name"].lower() for f in result["fonts"]}
            
            for font in community_fonts:
                if font["name"].lower() not in existing_names:
                    result["fonts"].append(font)
                    
        self._font_db_cache = result
        return result

    def _fetch_json(self, url: str) -> dict[str, Any] | None:
        """通用 JSON 获取方法"""
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except Exception:
            pass
        return None

    def _adapt_community_db(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """将 programmingfonts 格式转换为 FontInfo 字典格式"""
        fonts = []
        for key, info in data.items():
            name = info.get("name", key)
            website = info.get("website", "")
            # 简单的启发式生成 patterns
            patterns = [
                f"{name}*",
                f"{name.replace(' ', '')}*",
            ]
            
            fonts.append({
                "name": name,
                "patterns": patterns,
                "homepage": website,
                "download": website, # 假设官网包含下载
                "license": info.get("license", ""),
                "description": info.get("description", ""),
            })
        return fonts

    def check_font_update(self, font_info: FontInfo, current_version: str | None) -> UpdateInfo | None:
        """
        检查字体更新
        
        Args:
            font_info: 字体信息
            current_version: 当前本地版本字符串 (如 "Version 6.4")
        
        Returns:
            UpdateInfo: 更新信息，如果检查失败返回 None
        """
        repo_slug = self._extract_github_repo(font_info)
        if not repo_slug:
            return None

        # 如果无法获取本地版本，仍然可以返回最新版本供参考
        curr_ver_clean = self._clean_version(current_version) if current_version else "Unknown"

        try:
            latest_tag, download_url = self._fetch_github_latest(repo_slug)
            latest_ver_clean = self._clean_version(latest_tag)

            # 简单的版本比较 (如果不相等且不为Unknown，则认为有更新)
            # TODO: 实现语义化版本比较 (semver)
            has_update = (
                curr_ver_clean != "Unknown"
                and latest_ver_clean != "Unknown"
                and curr_ver_clean != latest_ver_clean
            )

            # 如果本地是 v6.4，远程是 v6.4.1，简单的字符串不等可能会误报，但暂且接受
            # 改进：如果 latest 包含 current，可能只是 tag 写法不同？
            # 比如 local 6.4, remote v6.4 -> clean后都是 6.4 -> 相等 -> 无更新

            return UpdateInfo(
                current_version=current_version or "Unknown",
                latest_version=latest_tag,
                download_url=download_url,
                has_update=has_update
            )

        except Exception:
            pass

        return None

    def _extract_github_repo(self, font_info: FontInfo) -> str | None:
        """从 URL 提取 Owner/Repo"""
        urls = [font_info.homepage, font_info.download]

        for url in urls:
            if not url:
                continue
            # 匹配 https://github.com/Owner/Repo
            match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        return None

    def _fetch_github_latest(self, repo_slug: str) -> tuple[str, str]:
        """调用 GitHub API 获取最新 Release"""
        api_url = f"https://api.github.com/repos/{repo_slug}/releases/latest"
        req = urllib.request.Request(api_url)
        # 添加 User-Agent 避免被 GitHub 拒绝
        req.add_header("User-Agent", "WinstyleS-Updater")

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                html_url = data.get("html_url", "")
                return tag_name, html_url

        raise ValueError("Failed to fetch GitHub release")

    def _clean_version(self, version: str) -> str:
        """清洗版本号，移除 'Version ', 'v' 等前缀"""
        if not version:
            return ""

        # 移除常见前缀
        v = version.lower()
        v = v.replace("version", "").replace("v", "").replace(" ", "").strip()
        return v
