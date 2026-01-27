"""
测试配置和 fixtures
"""

import pytest


@pytest.fixture
def sample_data() -> dict:
    """示例 fixture"""
    return {"key": "value"}
