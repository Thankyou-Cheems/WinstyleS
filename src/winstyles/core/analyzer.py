"""
DiffAnalyzer - 差异分析器，对比当前配置与默认值
"""

from typing import Any

from winstyles.domain.models import ScannedItem
from winstyles.domain.types import ChangeType


class DiffAnalyzer:
    """
    差异分析器

    负责将扫描到的配置项与默认值进行对比，
    标记每个配置项的变更类型。
    """

    def __init__(self, defaults_db: dict[str, Any]) -> None:
        """
        Args:
            defaults_db: 默认值数据库
        """
        self._defaults = defaults_db

    @classmethod
    def compare(
        cls,
        items: list[ScannedItem],
        defaults_db: dict[str, Any],
    ) -> list[ScannedItem]:
        """
        批量对比扫描项与默认值

        Args:
            items: 扫描到的配置项列表
            defaults_db: 默认值数据库

        Returns:
            标记了变更类型的配置项列表
        """
        analyzer = cls(defaults_db)
        return [analyzer.analyze_item(item) for item in items]

    def analyze_item(self, item: ScannedItem) -> ScannedItem:
        """
        分析单个配置项的变更状态

        Args:
            item: 扫描到的配置项

        Returns:
            更新了 change_type 的配置项
        """
        default_value = self._get_default_value(item.category, item.key)

        if default_value is None:
            # 默认值库中不存在此项，视为新增
            change_type = ChangeType.ADDED
        elif item.current_value == default_value:
            # 与默认值相同
            change_type = ChangeType.DEFAULT
        else:
            # 已修改
            change_type = ChangeType.MODIFIED

        # 创建更新后的项（Pydantic model 是不可变的，需要 copy）
        return item.model_copy(
            update={
                "default_value": default_value,
                "change_type": change_type,
            }
        )

    def _get_default_value(self, category: str, key: str) -> Any:
        """
        从默认值库获取对应的默认值

        Args:
            category: 配置类别
            key: 配置键名

        Returns:
            默认值，如果不存在则返回 None
        """
        category_defaults = self._defaults.get(category, {})
        return category_defaults.get(key)
