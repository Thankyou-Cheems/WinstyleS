"""
自定义异常类
"""


class WSSError(Exception):
    """WSS 基础异常类"""
    pass


class ScanError(WSSError):
    """扫描过程中的错误"""
    pass


class ExportError(WSSError):
    """导出过程中的错误"""
    pass


class ImportError(WSSError):
    """导入过程中的错误"""
    pass


class RegistryError(WSSError):
    """注册表操作错误"""
    pass


class PermissionError(WSSError):
    """权限不足错误"""
    pass


class ValidationError(WSSError):
    """数据验证错误"""
    pass


class PackageError(WSSError):
    """配置包格式或完整性错误"""
    pass
