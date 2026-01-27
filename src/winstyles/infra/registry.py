"""
注册表操作适配器

提供统一的注册表操作接口，并支持 Mock 测试。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import winreg


class IRegistryAdapter(ABC):
    """注册表适配器接口"""
    
    @abstractmethod
    def get_value(
        self,
        key_path: str,
        value_name: str,
    ) -> Tuple[Any, int]:
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
        value_type: Optional[int] = None,
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
    def get_all_values(self, key_path: str) -> Dict[str, Any]:
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
    HKEY_MAP = {
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKCR": winreg.HKEY_CLASSES_ROOT,
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKU": winreg.HKEY_USERS,
        "HKEY_USERS": winreg.HKEY_USERS,
    }
    
    def _parse_key_path(self, key_path: str) -> Tuple[int, str]:
        """
        解析键路径
        
        Args:
            key_path: 如 "HKLM\\SOFTWARE\\Microsoft"
            
        Returns:
            (根键句柄, 子键路径) 的元组
        """
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
    ) -> Tuple[Any, int]:
        """获取注册表值"""
        root_key, sub_key = self._parse_key_path(key_path)
        
        with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ) as key:
            value, value_type = winreg.QueryValueEx(key, value_name)
            return value, value_type
    
    def set_value(
        self,
        key_path: str,
        value_name: str,
        value: Any,
        value_type: Optional[int] = None,
    ) -> None:
        """设置注册表值"""
        root_key, sub_key = self._parse_key_path(key_path)
        
        # 如果未指定类型，尝试推断
        if value_type is None:
            if isinstance(value, str):
                value_type = winreg.REG_SZ
            elif isinstance(value, int):
                value_type = winreg.REG_DWORD
            elif isinstance(value, bytes):
                value_type = winreg.REG_BINARY
            else:
                value_type = winreg.REG_SZ
                value = str(value)
        
        with winreg.OpenKey(
            root_key, sub_key, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, value_name, 0, value_type, value)
    
    def get_all_values(self, key_path: str) -> Dict[str, Any]:
        """获取键下的所有值"""
        root_key, sub_key = self._parse_key_path(key_path)
        values: Dict[str, Any] = {}
        
        try:
            with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
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
            root_key, sub_key = self._parse_key_path(key_path)
            with winreg.OpenKey(root_key, sub_key, 0, winreg.KEY_READ):
                return True
        except FileNotFoundError:
            return False


class MockRegistryAdapter(IRegistryAdapter):
    """
    模拟注册表适配器 - 用于测试
    
    使用内存中的字典模拟注册表操作。
    """
    
    def __init__(self, data: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        """
        Args:
            data: 初始数据，格式为 {key_path: {value_name: value}}
        """
        self._data: Dict[str, Dict[str, Any]] = data or {}
    
    def get_value(
        self,
        key_path: str,
        value_name: str,
    ) -> Tuple[Any, int]:
        """获取模拟的注册表值"""
        key_data = self._data.get(key_path, {})
        if value_name not in key_data:
            raise FileNotFoundError(f"Value not found: {key_path}\\{value_name}")
        
        value = key_data[value_name]
        # 简单推断类型
        if isinstance(value, int):
            return value, winreg.REG_DWORD
        return value, winreg.REG_SZ
    
    def set_value(
        self,
        key_path: str,
        value_name: str,
        value: Any,
        value_type: Optional[int] = None,
    ) -> None:
        """设置模拟的注册表值"""
        if key_path not in self._data:
            self._data[key_path] = {}
        self._data[key_path][value_name] = value
    
    def get_all_values(self, key_path: str) -> Dict[str, Any]:
        """获取键下的所有模拟值"""
        return self._data.get(key_path, {}).copy()
    
    def key_exists(self, key_path: str) -> bool:
        """检查键是否存在"""
        return key_path in self._data
