"""
注册表操作适配器

提供统一的注册表操作接口，并支持 Mock 测试。
"""

from abc import ABC, abstractmethod
from typing import Any

try:
    import winreg as _winreg
except ModuleNotFoundError:  # pragma: no cover - only hit on non-Windows platforms
    _winreg = None  # type: ignore[assignment]

REG_DWORD = getattr(_winreg, "REG_DWORD", 4)
REG_SZ = getattr(_winreg, "REG_SZ", 1)


class IRegistryAdapter(ABC):
    """注册表适配器接口"""

    @abstractmethod
    def get_value(
        self,
        key_path: str,
        value_name: str,
    ) -> tuple[Any, int]:
        """
        获取注册表值

        Args:
            key_path: 键路径，如 "HKLM\\SOFTWARE\\Microsoft"
            value_name: 值名称

        Returns:
            (值, 值类型) 的元组
        """
        pass

    @abstractmethod
    def set_value(
        self,
        key_path: str,
        value_name: str,
        value: Any,
        value_type: int | None = None,
    ) -> None:
        """
        设置注册表值

        Args:
            key_path: 键路径
            value_name: 值名称
            value: 值
            value_type: 值类型，如 REG_SZ
        """
        pass

    @abstractmethod
    def get_all_values(self, key_path: str) -> dict[str, Any]:
        """
        获取键下的所有值

        Args:
            key_path: 键路径

        Returns:
            {值名称: 值} 的字典
        """
        pass

    @abstractmethod
    def key_exists(self, key_path: str) -> bool:
        """检查键是否存在"""
        pass


class WindowsRegistryAdapter(IRegistryAdapter):
    """真实的 Windows 注册表适配器"""

    # 根键映射
    HKEY_MAP: dict[str, int] = {}
    if _winreg is not None:
        HKEY_MAP = {
            "HKLM": _winreg.HKEY_LOCAL_MACHINE,
            "HKEY_LOCAL_MACHINE": _winreg.HKEY_LOCAL_MACHINE,
            "HKCU": _winreg.HKEY_CURRENT_USER,
            "HKEY_CURRENT_USER": _winreg.HKEY_CURRENT_USER,
            "HKCR": _winreg.HKEY_CLASSES_ROOT,
            "HKEY_CLASSES_ROOT": _winreg.HKEY_CLASSES_ROOT,
            "HKU": _winreg.HKEY_USERS,
            "HKEY_USERS": _winreg.HKEY_USERS,
        }

    def _ensure_available(self) -> None:
        if _winreg is None:
            raise OSError("winreg is not available on this platform")

    def _parse_key_path(self, key_path: str) -> tuple[int, str]:
        """
        解析键路径

        Args:
            key_path: 如 "HKLM\\SOFTWARE\\Microsoft"

        Returns:
            (根键句柄, 子键路径) 的元组
        """
        self._ensure_available()
        parts = key_path.split("\\", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid registry path: {key_path}")

        root_name, sub_key = parts
        root_key = self.HKEY_MAP.get(root_name.upper())

        if root_key is None:
            raise ValueError(f"Unknown root key: {root_name}")

        return root_key, sub_key

    def get_value(
        self,
        key_path: str,
        value_name: str,
    ) -> tuple[Any, int]:
        """获取注册表值"""
        self._ensure_available()
        assert _winreg is not None
        root_key, sub_key = self._parse_key_path(key_path)

        with _winreg.OpenKey(root_key, sub_key, 0, _winreg.KEY_READ) as key:
            value, value_type = _winreg.QueryValueEx(key, value_name)
            return value, value_type

    def set_value(
        self,
        key_path: str,
        value_name: str,
        value: Any,
        value_type: int | None = None,
    ) -> None:
        """设置注册表值"""
        self._ensure_available()
        assert _winreg is not None
        root_key, sub_key = self._parse_key_path(key_path)

        # 如果未指定类型，尝试推断
        if value_type is None:
            if isinstance(value, str):
                value_type = _winreg.REG_SZ
            elif isinstance(value, int):
                value_type = _winreg.REG_DWORD
            elif isinstance(value, bytes):
                value_type = _winreg.REG_BINARY
            elif isinstance(value, list) and all(isinstance(v, str) for v in value):
                value_type = _winreg.REG_MULTI_SZ
            else:
                value_type = _winreg.REG_SZ
                value = str(value)

        with _winreg.OpenKey(root_key, sub_key, 0, _winreg.KEY_SET_VALUE) as key:
            _winreg.SetValueEx(key, value_name, 0, value_type, value)

    def get_all_values(self, key_path: str) -> dict[str, Any]:
        """获取键下的所有值"""
        self._ensure_available()
        assert _winreg is not None
        root_key, sub_key = self._parse_key_path(key_path)
        values: dict[str, Any] = {}

        try:
            with _winreg.OpenKey(root_key, sub_key, 0, _winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = _winreg.EnumValue(key, i)
                        values[name] = value
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            pass

        return values

    def key_exists(self, key_path: str) -> bool:
        """检查键是否存在"""
        try:
            self._ensure_available()
            assert _winreg is not None
            root_key, sub_key = self._parse_key_path(key_path)
            with _winreg.OpenKey(root_key, sub_key, 0, _winreg.KEY_READ):
                return True
        except FileNotFoundError:
            return False
        except OSError:
            return False


class MockRegistryAdapter(IRegistryAdapter):
    """
    模拟注册表适配器 - 用于测试

    使用内存中的字典模拟注册表操作。
    """

    def __init__(self, data: dict[str, dict[str, Any]] | None = None) -> None:
        """
        Args:
            data: 初始数据，格式为 {key_path: {value_name: value}}
        """
        self._data: dict[str, dict[str, Any]] = data or {}

    def get_value(
        self,
        key_path: str,
        value_name: str,
    ) -> tuple[Any, int]:
        """获取模拟的注册表值"""
        key_data = self._data.get(key_path, {})
        if value_name not in key_data:
            raise FileNotFoundError(f"Value not found: {key_path}\\{value_name}")

        value = key_data[value_name]
        # 简单推断类型
        if isinstance(value, int):
            return value, REG_DWORD
        return value, REG_SZ

    def set_value(
        self,
        key_path: str,
        value_name: str,
        value: Any,
        value_type: int | None = None,
    ) -> None:
        """设置模拟的注册表值"""
        if key_path not in self._data:
            self._data[key_path] = {}
        self._data[key_path][value_name] = value

    def get_all_values(self, key_path: str) -> dict[str, Any]:
        """获取键下的所有模拟值"""
        return self._data.get(key_path, {}).copy()

    def key_exists(self, key_path: str) -> bool:
        """检查键是否存在"""
        return key_path in self._data
