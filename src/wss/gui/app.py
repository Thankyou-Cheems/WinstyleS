"""
WSSApp - 主应用窗口
"""

import customtkinter as ctk
from typing import Optional


class WSSApp(ctk.CTk):
    """
    WSS 主应用窗口
    
    使用 CustomTkinter 构建现代化的 GUI 界面。
    """
    
    def __init__(self) -> None:
        super().__init__()
        
        # 窗口配置
        self.title("Windows Style Sync")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # 设置主题
        ctk.set_appearance_mode("system")  # 跟随系统
        ctk.set_default_color_theme("blue")
        
        # 创建界面
        self._create_widgets()
        self._create_layout()
    
    def _create_widgets(self) -> None:
        """创建控件"""
        # 侧边栏
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        
        # Logo/标题
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🎨 WSS",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        
        # 导航按钮
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("🔍 扫描", "scan"),
            ("📤 导出", "export"),
            ("📥 导入", "import"),
            ("⚙️ 设置", "settings"),
        ]
        
        for text, name in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=ctk.CTkFont(size=14),
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda n=name: self._on_nav_click(n),
            )
            self.nav_buttons[name] = btn
        
        # 主内容区
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        
        # 欢迎页面
        self.welcome_label = ctk.CTkLabel(
            self.main_frame,
            text="欢迎使用 Windows Style Sync",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        
        self.welcome_desc = ctk.CTkLabel(
            self.main_frame,
            text="自动探测、导出、同步你的 Windows 美化配置",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        
        # 快速操作按钮
        self.quick_scan_btn = ctk.CTkButton(
            self.main_frame,
            text="🔍 开始扫描",
            font=ctk.CTkFont(size=16),
            height=50,
            width=200,
            command=self._on_scan_click,
        )
        
        # 状态栏
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="就绪",
            font=ctk.CTkFont(size=12),
        )
    
    def _create_layout(self) -> None:
        """创建布局"""
        # 配置网格
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 侧边栏布局
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nswe")
        self.sidebar.grid_rowconfigure(10, weight=1)  # 弹性空间
        
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 40))
        
        for i, (name, btn) in enumerate(self.nav_buttons.items()):
            btn.grid(row=i + 1, column=0, padx=10, pady=5, sticky="ew")
        
        # 主内容区布局
        self.main_frame.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)
        
        self.welcome_label.grid(row=0, column=0, pady=(80, 10))
        self.welcome_desc.grid(row=1, column=0, pady=(0, 40))
        self.quick_scan_btn.grid(row=2, column=0)
        
        # 状态栏
        self.status_bar.grid(row=1, column=1, sticky="swe")
        self.status_label.pack(side="left", padx=10)
    
    def _on_nav_click(self, name: str) -> None:
        """导航按钮点击事件"""
        self.set_status(f"切换到: {name}")
        # TODO: 实现页面切换
    
    def _on_scan_click(self) -> None:
        """扫描按钮点击事件"""
        self.set_status("正在扫描...")
        # TODO: 实现扫描功能
    
    def set_status(self, message: str) -> None:
        """设置状态栏消息"""
        self.status_label.configure(text=message)


def run_gui() -> None:
    """启动 GUI 应用"""
    app = WSSApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
