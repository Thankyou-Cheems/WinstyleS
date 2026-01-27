"""
基础设施层 - 与系统打交道的适配器
"""

from winstyles.infra.registry import IRegistryAdapter, WindowsRegistryAdapter, MockRegistryAdapter
from winstyles.infra.filesystem import IFileSystemAdapter, WindowsFileSystemAdapter, MockFileSystemAdapter

__all__ = [
    "IRegistryAdapter",
    "WindowsRegistryAdapter",
    "MockRegistryAdapter",
    "IFileSystemAdapter",
    "WindowsFileSystemAdapter",
    "MockFileSystemAdapter",
]
