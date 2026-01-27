"""
BaseScanner - 扫描器插件基类

所有扫描器都应继承此基类，实现统一的接口。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from winstyles.domain.models import ScannedItem
    from winstyles.infra.filesystem import IFileSystemAdapter
    from winstyles.infra.registry import IRegistryAdapter


class BaseScanner(ABC):
    """
    扫描器基类 - 插件化设计

    每个扫描器负责扫描特定类型的配置，例如：
    - FontScanner: 扫描系统字体
    - TerminalScanner: 扫描终端配置
    - ThemeScanner: 扫描主题设置

    扫描器通过依赖注入接收基础设施适配器，
    这样可以在测试时轻松替换为 Mock 对象。
    """

    def __init__(
        self,
        registry_adapter: "IRegistryAdapter",
        fs_adapter: "IFileSystemAdapter",
    ) -> None:
        """
        Args:
            registry_adapter: 注册表适配器
            fs_adapter: 文件系统适配器
        """
        self._registry = registry_adapter
        self._fs = fs_adapter

    @property
    @abstractmethod
    def id(self) -> str:
        """
        扫描器唯一标识符

        用于配置和日志记录。
        示例: "font_substitutes", "windows_terminal"
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """
        扫描器显示名称

        用于 UI 展示。
        示例: "系统字体替换", "Windows Terminal"
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def category(self) -> str:
        """
        所属类别

        示例: "fonts", "terminal", "theme"
        """
        raise NotImplementedError

    @property
    def description(self) -> str:
        """扫描器描述"""
        return ""

    @abstractmethod
    def scan(self) -> list["ScannedItem"]:
        """
        执行扫描

        Returns:
            扫描到的配置项列表
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, item: "ScannedItem") -> bool:
        """
        应用单个配置项

        在导入时使用。

        Args:
            item: 要应用的配置项

        Returns:
            是否成功应用
        """
        raise NotImplementedError

    def get_default_values(self) -> dict[str, Any]:
        """
        获取此扫描器相关的默认值

        子类可以覆盖此方法提供硬编码的默认值，
        也可以返回空字典让引擎从默认值数据库加载。

        Returns:
            默认值字典
        """
        return {}

    def validate(self) -> bool:
        """
        验证扫描器是否可用

        检查必要的依赖和权限。

        Returns:
            扫描器是否可用
        """
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
