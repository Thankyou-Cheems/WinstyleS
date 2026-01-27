"""
WinstyleSApp - 主应用窗口
"""

from __future__ import annotations

import threading

import customtkinter as ctk  # type: ignore[import-untyped]

from winstyles.core.engine import StyleEngine


class WinstyleSApp(ctk.CTk):  # type: ignore[misc]
    """
    WinstyleS 主应用窗口

    使用 CustomTkinter 构建现代化的 GUI 界面。
    """

    COLOR_BG = "#F2F2F2"
    COLOR_PANEL = "#FFFFFF"
    COLOR_BORDER = "#E5E5E5"
    COLOR_TEXT = "#0B0B0B"
    COLOR_MUTED = "#5C5C5C"
    COLOR_ACCENT = "#007AFF"
    COLOR_ACCENT_HOVER = "#0062CC"

    def __init__(self) -> None:
        super().__init__()

        # 窗口配置
        self.title("WinstyleS")
        self.geometry("1000x640")
        self.minsize(920, 600)
        self.configure(fg_color=self.COLOR_BG)

        # 设置主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 字体
        self.font_title = ctk.CTkFont(family="Segoe UI Variable", size=24, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Segoe UI Variable", size=13)
        self.font_button = ctk.CTkFont(family="Segoe UI Variable", size=14, weight="bold")
        self.font_body = ctk.CTkFont(family="Segoe UI Variable", size=12)

        # 状态
        self.active_page = "scan"
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.pages: dict[str, ctk.CTkFrame] = {}

        # 创建界面
        self._create_widgets()
        self._create_layout()
        self._set_active_page("scan")

    def _create_widgets(self) -> None:
        # 侧边栏
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color=self.COLOR_PANEL,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="WinstyleS",
            font=self.font_title,
            text_color=self.COLOR_TEXT,
        )
        self.logo_sub = ctk.CTkLabel(
            self.sidebar,
            text="Windows Style Sync",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )

        self.nav_buttons = {}
        nav_items = [
            ("扫描", "scan"),
            ("导出", "export"),
            ("导入", "import"),
            ("设置", "settings"),
        ]

        for text, name in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=self.font_button,
                height=40,
                corner_radius=10,
                fg_color=self.COLOR_PANEL,
                text_color=self.COLOR_TEXT,
                hover_color=self.COLOR_BORDER,
                border_width=1,
                border_color=self.COLOR_BORDER,
                command=lambda n=name: self._set_active_page(n),
            )
            self.nav_buttons[name] = btn

        # 顶部标题区
        self.header = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=self.COLOR_PANEL,
            border_width=1,
            border_color=self.COLOR_BORDER,
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
            "export": self._build_export_page(),
            "import": self._build_import_page(),
            "settings": self._build_settings_page(),
        }

        # 状态栏
        self.status_bar = ctk.CTkFrame(
            self,
            height=32,
            corner_radius=0,
            fg_color=self.COLOR_PANEL,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="就绪",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )

    def _create_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nswe")
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo_label.grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")
        self.logo_sub.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        for i, btn in enumerate(self.nav_buttons.values(), start=2):
            btn.grid(row=i, column=0, padx=16, pady=8, sticky="ew")

        self.header.grid(row=0, column=1, sticky="ew", padx=16, pady=16)
        self.header.grid_columnconfigure(0, weight=1)
        self.header_title.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")
        self.header_desc.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=16, pady=(0, 0))
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_label.pack(side="left", padx=16)

    def _set_active_page(self, name: str) -> None:
        self.active_page = name
        for page in self.pages.values():
            page.grid_forget()

        self.pages[name].grid(row=0, column=0, sticky="nsew")
        self._update_nav_style(name)
        self._update_header(name)

    def _update_nav_style(self, active: str) -> None:
        for name, btn in self.nav_buttons.items():
            if name == active:
                btn.configure(
                    fg_color=self.COLOR_ACCENT,
                    text_color="white",
                    hover_color=self.COLOR_ACCENT_HOVER,
                    border_color=self.COLOR_ACCENT,
                )
            else:
                btn.configure(
                    fg_color=self.COLOR_PANEL,
                    text_color=self.COLOR_TEXT,
                    hover_color=self.COLOR_BORDER,
                    border_color=self.COLOR_BORDER,
                )

    def _update_header(self, name: str) -> None:
        title_map = {
            "scan": "扫描",
            "export": "导出",
            "import": "导入",
            "settings": "设置",
        }
        desc_map = {
            "scan": "扫描系统个性化配置并生成报告",
            "export": "导出配置包，便于迁移与备份",
            "import": "从配置包恢复个性化设置",
            "settings": "管理默认路径与显示选项",
        }
        self.header_title.configure(text=title_map.get(name, ""))
        self.header_desc.configure(text=desc_map.get(name, ""))

    def _build_scan_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=14, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="快速扫描",
            font=self.font_title,
            text_color=self.COLOR_TEXT,
        )
        subtitle = ctk.CTkLabel(
            frame,
            text="扫描字体与终端配置，生成差异报告",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )

        self.scan_btn = ctk.CTkButton(
            frame,
            text="开始扫描",
            font=self.font_button,
            height=44,
            corner_radius=12,
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            command=self._on_scan_click,
        )

        self.scan_summary = ctk.CTkLabel(
            frame,
            text="最近一次：暂无",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )

        self.scan_output = ctk.CTkTextbox(
            frame,
            height=280,
            corner_radius=12,
            fg_color="#FAFAFA",
            text_color=self.COLOR_TEXT,
            border_width=1,
            border_color=self.COLOR_BORDER,
        )
        self.scan_output.insert("end", "扫描结果将在此显示...\n")
        self.scan_output.configure(state="disabled")

        title.grid(row=0, column=0, padx=24, pady=(20, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")
        self.scan_btn.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="w")
        self.scan_summary.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="e")
        self.scan_output.grid(row=3, column=0, padx=24, pady=(0, 24), sticky="nsew")

        return frame

    def _build_export_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=14, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="导出配置包",
            font=self.font_title,
            text_color=self.COLOR_TEXT,
        )
        subtitle = ctk.CTkLabel(
            frame,
            text="导出 scan.json 与 manifest.json，可用于迁移与分享",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        hint = ctk.CTkLabel(
            frame,
            text="CLI 已支持：winstyles export <path> -c terminal",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )

        title.grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")
        hint.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="w")
        return frame

    def _build_import_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=14, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            frame,
            text="导入配置包",
            font=self.font_title,
            text_color=self.COLOR_TEXT,
        )
        subtitle = ctk.CTkLabel(
            frame,
            text="导入配置包以恢复设置。建议先执行 dry-run",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )
        hint = ctk.CTkLabel(
            frame,
            text="CLI 已支持：winstyles import <path> --dry-run",
            font=self.font_body,
            text_color=self.COLOR_MUTED,
        )

        title.grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="w")
        hint.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="w")
        return frame

    def _build_settings_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.main_frame, corner_radius=14, fg_color=self.COLOR_PANEL)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text="设置", font=self.font_title, text_color=self.COLOR_TEXT)
        subtitle = ctk.CTkLabel(
            frame,
            text="设置默认导出路径与扫描偏好（待完善）",
            font=self.font_subtitle,
            text_color=self.COLOR_MUTED,
        )

        title.grid(row=0, column=0, padx=24, pady=(24, 4), sticky="w")
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 24), sticky="w")
        return frame

    def _on_scan_click(self) -> None:
        self.scan_btn.configure(state="disabled")
        self.set_status("正在扫描...")
        self._append_scan_output("开始扫描...\n", clear=True)

        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self) -> None:
        try:
            engine = StyleEngine()
            result = engine.scan_all(categories=None)
            summary = result.summary
            lines = [
                f"Scan ID: {result.scan_id}",
                f"OS: {result.os_version or 'Unknown'}",
                f"Total Items: {len(result.items)}",
                "",
            ]
            for category, count in sorted(summary.items()):
                lines.append(f"{category}: {count}")

            output = "\n".join(lines) + "\n"
            self.after(0, lambda: self._append_scan_output(output, clear=True))
            self.after(0, lambda: self.scan_summary.configure(text=f"最近一次：{result.scan_time}"))
            self.after(0, lambda: self.set_status("扫描完成"))
        except Exception as exc:
            message = f"扫描失败: {exc}\n"
            self.after(0, lambda: self._append_scan_output(message, clear=True))
            self.after(0, lambda: self.set_status("扫描失败"))
        finally:
            self.after(0, lambda: self.scan_btn.configure(state="normal"))

    def _append_scan_output(self, text: str, clear: bool = False) -> None:
        self.scan_output.configure(state="normal")
        if clear:
            self.scan_output.delete("1.0", "end")
        self.scan_output.insert("end", text)
        self.scan_output.configure(state="disabled")

    def set_status(self, message: str) -> None:
        self.status_label.configure(text=message)


# 兼容旧名称
WSSApp = WinstyleSApp


def run_gui() -> None:
    """启动 GUI 应用"""
    app = WinstyleSApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
