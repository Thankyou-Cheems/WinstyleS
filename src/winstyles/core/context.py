"""
AppContext - 运行时上下文，管理全局配置和服务
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppConfig:
    """应用配置"""

    # 数据目录
    data_dir: Path = field(default_factory=lambda: Path.home() / ".wss")

    # 默认值数据库路径
    defaults_db_path: Path | None = None

    # 日志级别
    log_level: str = "INFO"

    # 是否启用详细输出
    verbose: bool = False

    def __post_init__(self) -> None:
        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)


class AppContext:
    """
    应用运行时上下文 - 单例模式

    管理:
    - 全局配置
    - 日志记录器
    - 共享服务
    """

    _instance: Optional["AppContext"] = None

    def __new__(cls, config: AppConfig | None = None) -> "AppContext":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: AppConfig | None = None) -> None:
        if self._initialized:
            return

        self._config = config or AppConfig()
        self._logger = self._setup_logger()
        self._initialized = True

    @property
    def config(self) -> AppConfig:
        """获取应用配置"""
        return self._config

    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        return self._logger

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""
        logger = logging.getLogger("wss")
        logger.setLevel(getattr(logging, self._config.log_level.upper()))

        # 控制台处理器
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

        return logger

    @classmethod
    def reset(cls) -> None:
        """重置上下文（主要用于测试）"""
        cls._instance = None
