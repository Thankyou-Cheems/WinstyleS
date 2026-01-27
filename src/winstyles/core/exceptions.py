"""
自定义异常类
"""


class WinstyleSError(Exception):
    """WinstyleS 基础异常类"""
    pass


class ScanError(WinstyleSError):
    """扫描过程中的错误"""
    pass


class ExportError(WinstyleSError):
    """导出过程中的错误"""
    pass


class ImportError(WinstyleSError):
    """导入过程中的错误"""
    pass


class RegistryError(WinstyleSError):
    """注册表操作错误"""
    pass


class PermissionError(WinstyleSError):
    """权限不足错误"""
    pass


class ValidationError(WinstyleSError):
    """数据验证错误"""
    pass


class PackageError(WinstyleSError):
    """配置包格式或完整性错误"""
    pass


# 兼容旧名称
WSSError = WinstyleSError
