"""
WinstyleSApp - 主应用窗口

使用 CustomTkinter 构建现代化的 GUI 界面。
新增功能：
- 字体更新检查
- 一键打开下载页面
- 报告生成（支持浏览器打开）
"""

from __future__ import annotations

import subprocess
import threading
import tempfile
import webbrowser
import sys
from pathlib import Path

import customtkinter as ctk  # type: ignore[import-untyped]

from winstyles.core.engine import StyleEngine
from winstyles.core.report import ReportGenerator
from winstyles.core.update_checker import UpdateChecker
from winstyles.utils.font_utils import find_font_path, get_font_version


class WinstyleSApp(ctk.CTk):  # type: ignore[misc]
    """
    WinstyleS 主应用窗口

    使用 CustomTkinter 构建现代化的 GUI 界面。
    """

    # Windows 11 Fluent Design 调色板
    COLOR_BG = "#F3F3F3"
    COLOR_PANEL = "#FFFFFF"
    COLOR_BORDER = "#E5E5E5"
    COLOR_DIVIDER = "#EBEBEB"
    COLOR_TEXT = "#1A1A1A"
    COLOR_MUTED = "#5C5C5C"
    COLOR_ACCENT = "#0078D4"
    COLOR_ACCENT_HOVER = "#429CE3"
    COLOR_ACCENT_PRESSED = "#005A9E"
    COLOR_SUCCESS = "#107C10"
    COLOR_WARNING = "#FF8C00"
    COLOR_DANGER = "#D13438"

    def __init__(self) -> None:
        super().__init__()

        # 窗口配置
        self.title("WinstyleS")
        self.geometry("1100x750")
        self.minsize(960, 640)
        self.configure(fg_color=self.COLOR_BG)

        # 设置主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 字体
        self.font_title = ctk.CTkFont(family="Segoe UI Variable", size=26, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Segoe UI Variable", size=13)
        self.font_heading = ctk.CTkFont(family="Segoe UI Variable", size=18, weight="bold")
        self.font_button = ctk.CTkFont(family="Segoe UI Variable", size=14, weight="bold")
        self.font_body = ctk.CTkFont(family="Segoe UI Variable", size=13)
        self.font_small = ctk.CTkFont(family="Segoe UI Variable", size=11)
        self.font_mono = ctk.CTkFont(family="Cascadia Code", size=12)

        # 状态
        self.active_page = "scan"
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.pages: dict[str, ctk.CTkFrame] = {}
        
        # 数据
        self._scan_result = None
        self._font_updates: list = []

        # 创建界面
        self._create_widgets()
        self._create_layout()
        self._set_active_page("scan")

    def _create_widgets(self) -> None:
        # 侧边栏
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=self.COLOR_PANEL,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="WinstyleS",
            font=self.font_title,
            text_color=self.COLOR_ACCENT,
        )
        self.logo_sub = ctk.CTkLabel(
            self.sidebar,
            text="Windows Style Sync",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )

        # 导航按钮
        self.nav_buttons = {}
        nav_items = [
            ("🔍 扫描", "scan"),
            ("📊 分析报告", "report"),
            ("⬇️ 字体更新", "updates"),
            ("───────────", None),  # 分隔符
            ("📤 导出", "export"),
            ("📥 导入", "import"),
            ("⚙️ 设置", "settings"),
        ]

        for text, name in nav_items:
            if name is None:
                # 分隔符
                label = ctk.CTkLabel(
                    self.sidebar,
                    text=text,
                    font=self.font_small,
                    text_color=self.COLOR_BORDER,
                )
                self.nav_buttons[f"_sep_{text}"] = label
            else:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=text,
                    font=self.font_button,
                    height=44,
                    corner_radius=8,
                    fg_color=self.COLOR_PANEL,
                    text_color=self.COLOR_TEXT,
                    hover_color=self.COLOR_DIVIDER,
                    border_width=0,
                    anchor="w",
                    command=lambda n=name: self._set_active_page(n),
                )
                self.nav_buttons[name] = btn

        # 顶部标题区
        self.header = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=self.COLOR_BG,
            border_width=0,
        )
        self.header_title = ctk.CTkLabel(
            self.header,
            text="扫描",
            font=self.font_title,
            text_color=self.COLOR_TEXT,
        )
        self.header_desc = ctk.CTkLabel(
            self.header,
            text="扫描系统个性化配置并生成报告",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )

        # 主内容区
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.COLOR_BG)

        # 页面容器
        self.pages = {
            "scan": self._build_scan_page(),
            "report": self._build_report_page(),
            "updates": self._build_updates_page(),
            "export": self._build_export_page(),
            "import": self._build_import_page(),
            "settings": self._build_settings_page(),
        }

        # 状态栏
        self.status_bar = ctk.CTkFrame(
            self,
            height=36,
            corner_radius=0,
            fg_color=self.COLOR_PANEL,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="● 就绪",
            font=self.font_body,
            text_color=self.COLOR_SUCCESS,
        )

    def _create_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nswe")
        self.sidebar.grid_rowconfigure(20, weight=1)

        self.logo_label.grid(row=0, column=0, padx=20, pady=(28, 4), sticky="w")
        self.logo_sub.grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        row = 2
        for key, widget in self.nav_buttons.items():
            if key.startswith("_sep_"):
                widget.grid(row=row, column=0, padx=20, pady=8, sticky="w")
            else:
                widget.grid(row=row, column=0, padx=16, pady=4, sticky="ew")
            row += 1

        self.header.grid(row=0, column=1, sticky="ew", padx=32, pady=24)
        self.header.grid_columnconfigure(0, weight=1)
        self.header_title.grid(row=0, column=0, sticky="w")
        self.header_desc.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=32, pady=(0, 16))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_label.pack(side="left", padx=20)

    def _set_active_page(self, name: str) -> None:
        self.active_page = name
        for page in self.pages.values():
            page.grid_forget()

        self.pages[name].grid(row=0, column=0, sticky="nsew")
        self._update_nav_style(name)
        self._update_header(name)

    def _update_nav_style(self, active: str) -> None:
        for name, btn in self.nav_buttons.items():
            if name.startswith("_sep_"):
                continue
            if name == active:
                btn.configure(
                    fg_color=self.COLOR_ACCENT,
                    text_color="white",
                    hover_color=self.COLOR_ACCENT_HOVER,
                )
            else:
                btn.configure(
                    fg_color=self.COLOR_PANEL,
                    text_color=self.COLOR_TEXT,
                    hover_color=self.COLOR_DIVIDER,
                )

    def _update_header(self, name: str) -> None:
        title_map = {
            "scan": "扫描",
            "report": "分析报告",
            "updates": "字体更新",
            "export": "导出",
            "import": "导入",
            "settings": "设置",
        }
        desc_map = {
            "scan": "扫描系统个性化配置并生成差异数据",
            "report": "智能分析配置变更，识别开源字体",
            "updates": "检查已安装开源字体的最新版本",
            "export": "导出配置包，便于迁移与备份",
            "import": "从配置包恢复个性化设置",
            "settings": "管理默认路径与显示选项",
        }
        self.header_title.configure(text=title_map.get(name, ""))
        self.header_desc.configure(text=desc_map.get(name, ""))

    # ======== Scan Page ========

    def _build_scan_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # 卡片头
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=24, pady=(24, 16), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header_frame, text="快速扫描", font=self.font_heading, text_color=self.COLOR_TEXT)
        title.grid(row=0, column=0, sticky="w")
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="扫描字体与终端配置，生成差异报告",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.scan_btn = ctk.CTkButton(
            header_frame,
            text="▶ 开始扫描",
            font=self.font_button,
            height=44,
            width=140,
            corner_radius=8,
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            command=self._on_scan_click,
        )
        self.scan_btn.grid(row=0, column=1, rowspan=2, padx=(16, 0))

        # 扫描摘要
        self.scan_summary = ctk.CTkLabel(
            frame,
            text="最近一次扫描：暂无",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )
        self.scan_summary.grid(row=1, column=0, padx=24, sticky="w")

        # 输出区
        self.scan_output = ctk.CTkTextbox(
            frame,
            corner_radius=8,
            fg_color="#1E1E1E",
            text_color="#D4D4D4",
            border_width=0,
            font=self.font_mono,
        )
        self.scan_output.insert("end", "扫描结果将在此显示...\n")
        self.scan_output.configure(state="disabled")
        self.scan_output.grid(row=2, column=0, padx=24, pady=(16, 24), sticky="nsew")

        return frame

    def _on_scan_click(self) -> None:
        self.scan_btn.configure(state="disabled")
        self.set_status("正在扫描...", "yellow")
        self._append_scan_output("开始扫描...\n", clear=True)

        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self) -> None:
        try:
            engine = StyleEngine()
            result = engine.scan_all(categories=None)
            self._scan_result = result
            
            summary = result.summary
            lines = [
                f"Scan ID: {result.scan_id}",
                f"OS: {result.os_version or 'Unknown'}",
                f"Total Items: {len(result.items)}",
                "",
            ]
            for category, count in sorted(summary.items()):
                lines.append(f"  {category}: {count}")

            output = "\n".join(lines) + "\n"
            self.after(0, lambda: self._append_scan_output(output, clear=True))
            self.after(0, lambda: self.scan_summary.configure(text=f"最近一次扫描：{result.scan_time}"))
            self.after(0, lambda: self.set_status("扫描完成", "green"))
        except Exception as exc:
            message = f"扫描失败: {exc}\n"
            self.after(0, lambda: self._append_scan_output(message, clear=True))
            self.after(0, lambda: self.set_status("扫描失败", "red"))
        finally:
            self.after(0, lambda: self.scan_btn.configure(state="normal"))

    def _append_scan_output(self, text: str, clear: bool = False) -> None:
        self.scan_output.configure(state="normal")
        if clear:
            self.scan_output.delete("1.0", "end")
        self.scan_output.insert("end", text)
        self.scan_output.configure(state="disabled")

    # ======== Report Page ========

    def _build_report_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # 卡片头
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=24, pady=(24, 16), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header_frame, text="系统分析报告", font=self.font_heading, text_color=self.COLOR_TEXT)
        title.grid(row=0, column=0, sticky="w")
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="智能分析配置变更，识别开源字体，生成可读性高的报告",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # 按钮组
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, rowspan=2, padx=(16, 0))

        self.open_browser_btn = ctk.CTkButton(
            btn_frame,
            text="🌐 浏览器打开",
            font=self.font_button,
            height=44,
            width=140,
            corner_radius=8,
            fg_color=self.COLOR_PANEL,
            text_color=self.COLOR_TEXT,
            border_width=1,
            border_color=self.COLOR_BORDER,
            hover_color=self.COLOR_DIVIDER,
            command=self._on_open_report_browser,
        )
        self.open_browser_btn.pack(side="left", padx=(0, 8))

        self.report_btn = ctk.CTkButton(
            btn_frame,
            text="📄 生成报告",
            font=self.font_button,
            height=44,
            width=140,
            corner_radius=8,
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            command=self._on_report_click,
        )
        self.report_btn.pack(side="left")

        # 选项
        options_frame = ctk.CTkFrame(frame, fg_color="transparent")
        options_frame.grid(row=1, column=0, padx=24, sticky="w")

        self.check_updates_var = ctk.BooleanVar(value=True)
        self.check_updates_check = ctk.CTkCheckBox(
            options_frame,
            text="检查字体更新",
            font=self.font_body,
            variable=self.check_updates_var,
        )
        self.check_updates_check.pack(side="left")

        # 报告显示区域
        self.report_output = ctk.CTkTextbox(
            frame,
            corner_radius=8,
            fg_color="#1E1E1E",
            text_color="#D4D4D4",
            border_width=0,
            font=self.font_mono,
        )
        self.report_output.insert("end", "点击「生成报告」开始分析系统配置...\n")
        self.report_output.configure(state="disabled")
        self.report_output.grid(row=2, column=0, padx=24, pady=(16, 24), sticky="nsew")

        return frame

    def _on_report_click(self) -> None:
        self.report_btn.configure(state="disabled")
        self.set_status("正在分析系统配置...", "yellow")
        self.report_output.configure(state="normal")
        self.report_output.delete("1.0", "end")
        self.report_output.insert("end", "正在扫描中，请稍候...\n")
        self.report_output.configure(state="disabled")

        thread = threading.Thread(target=self._run_report_generation, daemon=True)
        thread.start()

    def _run_report_generation(self) -> None:
        try:
            engine = StyleEngine()
            result = engine.scan_all(categories=None)
            self._scan_result = result
            
            check_updates = self.check_updates_var.get()
            generator = ReportGenerator(result, check_updates=check_updates)
            report_content = generator.generate_markdown()

            self.after(0, lambda: self._show_report(report_content))
            self.after(0, lambda: self.set_status("报告生成完成", "green"))
        except Exception as exc:
            message = f"生成失败: {exc}\n"
            self.after(0, lambda: self._show_report(message))
            self.after(0, lambda: self.set_status("生成失败", "red"))
        finally:
            self.after(0, lambda: self.report_btn.configure(state="normal"))

    def _on_open_report_browser(self) -> None:
        self.open_browser_btn.configure(state="disabled")
        self.set_status("正在生成 HTML 报告...", "yellow")

        thread = threading.Thread(target=self._run_open_browser_report, daemon=True)
        thread.start()

    def _run_open_browser_report(self) -> None:
        try:
            engine = StyleEngine()
            result = engine.scan_all(categories=None)
            
            check_updates = self.check_updates_var.get()
            generator = ReportGenerator(result, check_updates=check_updates)
            html_content = generator.generate_html()

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as f:
                f.write(html_content)
                temp_path = f.name

            # 在浏览器中打开
            webbrowser.open(f"file://{temp_path}")
            
            self.after(0, lambda: self.set_status("已在浏览器中打开报告", "green"))
        except Exception as exc:
            self.after(0, lambda: self.set_status(f"打开失败: {exc}", "red"))
        finally:
            self.after(0, lambda: self.open_browser_btn.configure(state="normal"))

    def _show_report(self, content: str) -> None:
        self.report_output.configure(state="normal")
        self.report_output.delete("1.0", "end")
        self.report_output.insert("end", content)
        self.report_output.configure(state="disabled")

    # ======== Font Updates Page ========

    def _build_updates_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # 卡片头
        header_frame = ctk.CTkFrame(frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=24, pady=(24, 16), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header_frame, text="字体更新检查", font=self.font_heading, text_color=self.COLOR_TEXT)
        title.grid(row=0, column=0, sticky="w")
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="检查已安装的开源字体是否有新版本可用",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.check_updates_btn = ctk.CTkButton(
            header_frame,
            text="🔄 检查更新",
            font=self.font_button,
            height=44,
            width=140,
            corner_radius=8,
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            command=self._on_check_updates_click,
        )
        self.check_updates_btn.grid(row=0, column=1, rowspan=2, padx=(16, 0))

        # 更新列表容器 (使用 Scrollable Frame)
        self.updates_container = ctk.CTkScrollableFrame(
            frame,
            corner_radius=8,
            fg_color=self.COLOR_BG,
        )
        self.updates_container.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="nsew")
        self.updates_container.grid_columnconfigure(0, weight=1)

        # 初始状态提示
        self.updates_placeholder = ctk.CTkLabel(
            self.updates_container,
            text="点击「检查更新」扫描已安装的开源字体\n并检查是否有新版本可用",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
            justify="center",
        )
        self.updates_placeholder.grid(row=0, column=0, pady=60)

        return frame

    def _on_check_updates_click(self) -> None:
        self.check_updates_btn.configure(state="disabled")
        self.set_status("正在检查字体更新...", "yellow")
        
        # 清空列表
        for widget in self.updates_container.winfo_children():
            widget.destroy()
        
        loading_label = ctk.CTkLabel(
            self.updates_container,
            text="⏳ 正在扫描字体并检查更新...\n这可能需要几秒钟",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
            justify="center",
        )
        loading_label.grid(row=0, column=0, pady=60)

        thread = threading.Thread(target=self._run_check_updates, daemon=True)
        thread.start()

    def _run_check_updates(self) -> None:
        try:
            engine = StyleEngine()
            result = engine.scan_all(categories=["fonts"])
            
            checker = UpdateChecker()
            db = checker.fetch_remote_db()
            
            if not db:
                self.after(0, lambda: self._show_updates_result([]))
                self.after(0, lambda: self.set_status("无法获取字体数据库", "red"))
                return

            updates = []
            fonts_info = db.get("fonts", [])
            
            # 匹配已安装字体
            for item in result.items:
                if item.category != "fonts":
                    continue
                    
                font_name = str(item.current)
                
                # 在数据库中查找匹配
                for font_info in fonts_info:
                    patterns = font_info.get("patterns", [])
                    name = font_info.get("name", "")
                    
                    matched = False
                    for pattern in patterns:
                        pattern_lower = pattern.lower().replace("*", "")
                        if pattern_lower in font_name.lower():
                            matched = True
                            break
                    
                    if matched:
                        # 获取本地版本
                        font_path = find_font_path(font_name)
                        local_version = None
                        if font_path:
                            local_version = get_font_version(font_path)
                        
                        # 构造 FontInfo 对象用于检查更新
                        from winstyles.domain.models import FontInfo
                        fi = FontInfo(
                            name=name,
                            patterns=patterns,
                            homepage=font_info.get("homepage", ""),
                            download=font_info.get("download", ""),
                        )
                        
                        update_info = checker.check_font_update(fi, local_version)
                        if update_info:
                            updates.append({
                                "name": name,
                                "current_version": update_info.current_version,
                                "latest_version": update_info.latest_version,
                                "download_url": update_info.download_url,
                                "has_update": update_info.has_update,
                            })
                        break

            self._font_updates = updates
            self.after(0, lambda: self._show_updates_result(updates))
            self.after(0, lambda: self.set_status("更新检查完成", "green"))
            
        except Exception as exc:
            self.after(0, lambda: self._show_updates_error(str(exc)))
            self.after(0, lambda: self.set_status("检查失败", "red"))
        finally:
            self.after(0, lambda: self.check_updates_btn.configure(state="normal"))

    def _show_updates_result(self, updates: list) -> None:
        # 清空容器
        for widget in self.updates_container.winfo_children():
            widget.destroy()

        if not updates:
            label = ctk.CTkLabel(
                self.updates_container,
                text="未检测到已安装的开源字体\n或所有字体都是最新版本",
                font=self.font_body,
                text_color=self.COLOR_MUTED,
                justify="center",
            )
            label.grid(row=0, column=0, pady=60)
            return

        # 按是否有更新分组
        has_updates = [u for u in updates if u["has_update"]]
        no_updates = [u for u in updates if not u["has_update"]]

        row = 0

        if has_updates:
            section_label = ctk.CTkLabel(
                self.updates_container,
                text=f"可更新 ({len(has_updates)})",
                font=self.font_body,
                text_color=self.COLOR_WARNING,
            )
            section_label.grid(row=row, column=0, sticky="w", pady=(8, 8))
            row += 1

            for update in has_updates:
                card = self._create_update_card(update, has_update=True)
                card.grid(row=row, column=0, sticky="ew", pady=4)
                row += 1

        if no_updates:
            section_label = ctk.CTkLabel(
                self.updates_container,
                text=f"已是最新 ({len(no_updates)})",
                font=self.font_body,
                text_color=self.COLOR_SUCCESS,
            )
            section_label.grid(row=row, column=0, sticky="w", pady=(16, 8))
            row += 1

            for update in no_updates:
                card = self._create_update_card(update, has_update=False)
                card.grid(row=row, column=0, sticky="ew", pady=4)
                row += 1

    def _create_update_card(self, update: dict, has_update: bool) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self.updates_container,
            corner_radius=8,
            fg_color=self.COLOR_PANEL,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )
        card.grid_columnconfigure(1, weight=1)

        # 图标
        icon_label = ctk.CTkLabel(
            card,
            text="🔤",
            font=ctk.CTkFont(size=24),
            width=48,
        )
        icon_label.grid(row=0, column=0, rowspan=2, padx=16, pady=16)

        # 名称
        name_label = ctk.CTkLabel(
            card,
            text=update["name"],
            font=self.font_button,
            text_color=self.COLOR_TEXT,
        )
        name_label.grid(row=0, column=1, sticky="w", pady=(16, 0))

        # 版本
        if has_update:
            version_text = f"{update['current_version']} → {update['latest_version']}"
            version_color = self.COLOR_WARNING
        else:
            version_text = update.get("current_version") or update.get("latest_version") or "已安装"
            version_color = self.COLOR_MUTED
            
        version_label = ctk.CTkLabel(
            card,
            text=version_text,
            font=self.font_small,
            text_color=version_color,
        )
        version_label.grid(row=1, column=1, sticky="w", pady=(0, 16))

        # 下载按钮
        if has_update and update.get("download_url"):
            download_btn = ctk.CTkButton(
                card,
                text="⬇ 下载",
                font=self.font_body,
                height=32,
                width=80,
                corner_radius=6,
                fg_color=self.COLOR_ACCENT,
                hover_color=self.COLOR_ACCENT_HOVER,
                command=lambda url=update["download_url"]: webbrowser.open(url),
            )
            download_btn.grid(row=0, column=2, rowspan=2, padx=16, pady=16)

        return card

    def _show_updates_error(self, error: str) -> None:
        for widget in self.updates_container.winfo_children():
            widget.destroy()

        label = ctk.CTkLabel(
            self.updates_container,
            text=f"检查失败: {error}",
            font=self.font_body,
            text_color=self.COLOR_DANGER,
            justify="center",
        )
        label.grid(row=0, column=0, pady=60)

    # ======== Export Page ========

    def _build_export_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="导出配置包", font=self.font_heading, text_color=self.COLOR_TEXT)
        subtitle = ctk.CTkLabel(
            frame,
            text="将扫描结果打包导出为 .zip 文件，便于迁移与分享",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        hint = ctk.CTkLabel(
            frame,
            text="💡 CLI 命令: winstyles export <path> -c terminal",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )

        title.grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")
        hint.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="w")
        return frame

    # ======== Import Page ========

    def _build_import_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="导入配置包", font=self.font_heading, text_color=self.COLOR_TEXT)
        subtitle = ctk.CTkLabel(
            frame,
            text="从配置包恢复个性化设置，建议先使用 dry-run 预览",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        hint = ctk.CTkLabel(
            frame,
            text="💡 CLI 命令: winstyles import <path> --dry-run",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )

        title.grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")
        hint.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="w")
        return frame

    # ======== Settings Page ========

    def _build_settings_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="设置", font=self.font_heading, text_color=self.COLOR_TEXT)
        subtitle = ctk.CTkLabel(
            frame,
            text="管理应用偏好设置",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )

        title.grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        # 关于信息
        about_frame = ctk.CTkFrame(frame, fg_color="transparent")
        about_frame.grid(row=2, column=0, padx=24, pady=(16, 24), sticky="w")

        about_text = ctk.CTkLabel(
            about_frame,
            text="WinstyleS - Windows Style Sync\n版本 0.1.0\n\n自动扫描、导出、同步你的 Windows 美化配置",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
            justify="left",
        )
        about_text.pack(anchor="w")

        github_btn = ctk.CTkButton(
            about_frame,
            text="🔗 GitHub",
            font=self.font_body,
            height=32,
            width=100,
            corner_radius=6,
            fg_color=self.COLOR_PANEL,
            text_color=self.COLOR_TEXT,
            border_width=1,
            border_color=self.COLOR_BORDER,
            hover_color=self.COLOR_DIVIDER,
            command=lambda: webbrowser.open("https://github.com/Thankyou-Cheems/WinstyleS"),
        )
        github_btn.pack(anchor="w", pady=(16, 0))

        return frame

    # ======== Status Bar ========

    def set_status(self, message: str, color: str = "green") -> None:
        color_map = {
            "green": self.COLOR_SUCCESS,
            "yellow": self.COLOR_WARNING,
            "red": self.COLOR_DANGER,
        }
        dot_color = color_map.get(color, self.COLOR_SUCCESS)
        self.status_label.configure(text=f"● {message}", text_color=dot_color)


# 兼容旧名称
WSSApp = WinstyleSApp


def run_gui() -> None:
    """启动 Web GUI 应用"""
    from winstyles.main import console
    
    project_root = Path(__file__).resolve().parents[3]
    web_ui_script = project_root / "start_web_ui.py"
    
    if not web_ui_script.exists():
        console.print("[red]错误: 未找到 Web UI 启动脚本 start_web_ui.py[/red]")
        return

    console.print(f"[bold blue]正在启动 Web 界面...[/bold blue]")
    console.print(f"[dim]脚本路径: {web_ui_script}[/dim]")
    
    try:
        # 使用当前 Python 解释器运行脚本
        subprocess.run([sys.executable, str(web_ui_script)], check=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Web UI 启动失败: {e}[/red]")

if __name__ == "__main__":
    run_gui()
