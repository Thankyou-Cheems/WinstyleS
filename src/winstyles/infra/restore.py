"""
系统还原点管理
"""

import ctypes
from ctypes import wintypes
from datetime import datetime

# 还原点类型
APPLICATION_INSTALL = 0
APPLICATION_UNINSTALL = 1
DEVICE_DRIVER_INSTALL = 10
MODIFY_SETTINGS = 12
CANCELLED_OPERATION = 13

# 还原点事件类型
BEGIN_SYSTEM_CHANGE = 100
END_SYSTEM_CHANGE = 101
BEGIN_NESTED_SYSTEM_CHANGE = 102
END_NESTED_SYSTEM_CHANGE = 103


class RESTOREPOINTINFO(ctypes.Structure):
    """还原点信息结构"""

    _fields_ = [
        ("dwEventType", wintypes.DWORD),
        ("dwRestorePtType", wintypes.DWORD),
        ("llSequenceNumber", ctypes.c_int64),
        ("szDescription", wintypes.WCHAR * 256),
    ]


class STATEMGRSTATUS(ctypes.Structure):
    """状态管理器状态结构"""

    _fields_ = [
        ("nStatus", wintypes.DWORD),
        ("llSequenceNumber", ctypes.c_int64),
    ]


class RestorePointManager:
    """
    系统还原点管理器

    提供创建和管理 Windows 系统还原点的功能。
    """

    def __init__(self) -> None:
        self._srclient = None
        self._load_library()

    def _load_library(self) -> None:
        """加载 srclient.dll"""
        try:
            self._srclient = ctypes.windll.LoadLibrary("srclient.dll")
        except OSError:
            self._srclient = None

    @property
    def is_available(self) -> bool:
        """检查系统还原功能是否可用"""
        return self._srclient is not None

    def create_restore_point(
        self,
        description: str | None = None,
        restore_type: int = MODIFY_SETTINGS,
    ) -> tuple[bool, int]:
        """
        创建系统还原点

        Args:
            description: 还原点描述
            restore_type: 还原点类型

        Returns:
            (是否成功, 序列号) 的元组
        """
        if not self.is_available:
            return False, 0

        if description is None:
            description = f"WinstyleS Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # 确保描述不超过 256 字符
        if len(description) > 255:
            description = description[:255]

        try:
            # 开始创建还原点
            restore_info = RESTOREPOINTINFO()
            restore_info.dwEventType = BEGIN_SYSTEM_CHANGE
            restore_info.dwRestorePtType = restore_type
            restore_info.llSequenceNumber = 0
            restore_info.szDescription = description

            status = STATEMGRSTATUS()

            result = self._srclient.SRSetRestorePointW(
                ctypes.byref(restore_info),
                ctypes.byref(status),
            )

            if not result:
                return False, 0

            # 结束还原点创建
            restore_info.dwEventType = END_SYSTEM_CHANGE
            restore_info.llSequenceNumber = status.llSequenceNumber

            result = self._srclient.SRSetRestorePointW(
                ctypes.byref(restore_info),
                ctypes.byref(status),
            )

            return result != 0, status.llSequenceNumber

        except Exception:
            return False, 0

    def cancel_restore_point(self, sequence_number: int) -> bool:
        """
        取消还原点创建

        Args:
            sequence_number: 还原点序列号

        Returns:
            是否成功
        """
        if not self.is_available:
            return False

        try:
            restore_info = RESTOREPOINTINFO()
            restore_info.dwEventType = END_SYSTEM_CHANGE
            restore_info.dwRestorePtType = CANCELLED_OPERATION
            restore_info.llSequenceNumber = sequence_number

            status = STATEMGRSTATUS()

            result = self._srclient.SRSetRestorePointW(
                ctypes.byref(restore_info),
                ctypes.byref(status),
            )

            return result != 0

        except Exception:
            return False
