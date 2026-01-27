"""
基础设施层 - 与系统打交道的适配器
"""

from winstyles.infra.filesystem import (
    IFileSystemAdapter,
    MockFileSystemAdapter,
    WindowsFileSystemAdapter,
)
from winstyles.infra.registry import IRegistryAdapter, MockRegistryAdapter, WindowsRegistryAdapter

__all__ = [
    "IRegistryAdapter",
    "WindowsRegistryAdapter",
    "MockRegistryAdapter",
    "IFileSystemAdapter",
    "WindowsFileSystemAdapter",
    "MockFileSystemAdapter",
]
