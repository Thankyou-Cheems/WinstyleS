"""
Windows 系统 API 封装

使用 ctypes/pywin32 调用原生 Windows API。
"""

import ctypes
from ctypes import wintypes

# Windows API 常量
HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002

# 系统还原相关常量
BEGIN_SYSTEM_CHANGE = 100
END_SYSTEM_CHANGE = 101
APPLICATION_INSTALL = 0x0001


class SystemAPI:
    """Windows 系统 API 封装类"""

    @staticmethod
    def refresh_explorer() -> bool:
        """
        刷新 Explorer，使设置变更立即生效

        Returns:
            是否成功
        """
        try:
            result = ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                ctypes.byref(wintypes.DWORD()),
            )
            return result != 0
        except Exception:
            return False

    @staticmethod
    def install_font(font_path: str) -> bool:
        """
        安装字体

        Args:
            font_path: 字体文件路径

        Returns:
            是否成功
        """
        try:
            # AddFontResourceW
            result = ctypes.windll.gdi32.AddFontResourceW(font_path)
            if result > 0:
                # 通知系统字体已更改
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    "fonts",
                    SMTO_ABORTIFHUNG,
                    5000,
                    ctypes.byref(wintypes.DWORD()),
                )
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def uninstall_font(font_path: str) -> bool:
        """
        卸载字体

        Args:
            font_path: 字体文件路径

        Returns:
            是否成功
        """
        try:
            result = ctypes.windll.gdi32.RemoveFontResourceW(font_path)
            if result:
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    "fonts",
                    SMTO_ABORTIFHUNG,
                    5000,
                    ctypes.byref(wintypes.DWORD()),
                )
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def is_admin() -> bool:
        """
        检查当前进程是否以管理员权限运行

        Returns:
            是否是管理员
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def request_admin_elevation(script_path: str | None = None) -> bool:
        """
        请求管理员权限提升

        Args:
            script_path: 要以管理员权限运行的脚本路径

        Returns:
            是否成功启动提升请求
        """
        try:
            import sys

            if script_path is None:
                script_path = sys.executable

            # 使用 ShellExecuteW 以 "runas" 动词运行
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                script_path,
                " ".join(sys.argv[1:]),
                None,
                1,  # SW_SHOWNORMAL
            )

            # 返回值大于 32 表示成功
            return result > 32
        except Exception:
            return False

    @staticmethod
    def get_windows_version() -> tuple[int, int, int]:
        """
        获取 Windows 版本号

        Returns:
            (major, minor, build) 元组
        """
        try:
            # 使用 RtlGetVersion 获取真实版本
            class OSVERSIONINFOEXW(ctypes.Structure):
                _fields_ = [
                    ("dwOSVersionInfoSize", wintypes.DWORD),
                    ("dwMajorVersion", wintypes.DWORD),
                    ("dwMinorVersion", wintypes.DWORD),
                    ("dwBuildNumber", wintypes.DWORD),
                    ("dwPlatformId", wintypes.DWORD),
                    ("szCSDVersion", wintypes.WCHAR * 128),
                    ("wServicePackMajor", wintypes.WORD),
                    ("wServicePackMinor", wintypes.WORD),
                    ("wSuiteMask", wintypes.WORD),
                    ("wProductType", wintypes.BYTE),
                    ("wReserved", wintypes.BYTE),
                ]

            os_info = OSVERSIONINFOEXW()
            os_info.dwOSVersionInfoSize = ctypes.sizeof(OSVERSIONINFOEXW)

            ntdll = ctypes.windll.ntdll
            ntdll.RtlGetVersion(ctypes.byref(os_info))

            return (
                os_info.dwMajorVersion,
                os_info.dwMinorVersion,
                os_info.dwBuildNumber,
            )
        except Exception:
            return (0, 0, 0)
