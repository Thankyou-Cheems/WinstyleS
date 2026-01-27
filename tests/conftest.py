"""
测试配置和 fixtures
"""

import pytest
from typing import Generator

from winstyles.infra.registry import MockRegistryAdapter
from winstyles.infra.filesystem import MockFileSystemAdapter


@pytest.fixture
def mock_registry() -> MockRegistryAdapter:
    """提供模拟注册表适配器"""
    return MockRegistryAdapter({
        # 字体替换测试数据
        "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes": {
            "MS Shell Dlg": "Microsoft Sans Serif",
            "MS Shell Dlg 2": "Tahoma",
        },
    })


@pytest.fixture
def mock_filesystem() -> MockFileSystemAdapter:
    """提供模拟文件系统适配器"""
    return MockFileSystemAdapter({
        # 测试配置文件
        "C:\\Users\\Test\\test.json": '{"key": "value"}',
    })


@pytest.fixture
def temp_dir(tmp_path) -> Generator[str, None, None]:
    """提供临时目录"""
    yield str(tmp_path)
