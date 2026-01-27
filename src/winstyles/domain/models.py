"""
Pydantic 数据模型 - 定义核心数据结构
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from winstyles.domain.types import AssetType, ChangeType, SourceType


class AssociatedFile(BaseModel):
    """关联的资源文件"""

    type: AssetType = Field(..., description="资源类型")
    name: str = Field(..., description="资源名称")
    path: str = Field(..., description="文件路径")
    exists: bool = Field(True, description="文件是否存在")
    size_bytes: int | None = Field(None, description="文件大小（字节）")
    sha256: str | None = Field(None, description="文件哈希值")


class ScannedItem(BaseModel):
    """扫描结果项 - 单个配置项"""

    category: str = Field(..., description="配置类别: fonts, terminal, theme...")
    key: str = Field(..., description="配置键名")
    current_value: Any = Field(..., description="当前值")
    default_value: Any | None = Field(None, description="默认值")
    change_type: ChangeType = Field(ChangeType.MODIFIED, description="变更类型")
    source_type: SourceType = Field(..., description="数据来源类型")
    source_path: str = Field(..., description="数据来源路径")
    associated_files: list[AssociatedFile] = Field(
        default_factory=list, description="关联的资源文件"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class ScanResult(BaseModel):
    """完整扫描结果"""

    scan_id: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"), description="扫描ID"
    )
    scan_time: datetime = Field(default_factory=datetime.now, description="扫描时间")
    os_version: str = Field("", description="操作系统版本")
    items: list[ScannedItem] = Field(default_factory=list, description="扫描到的配置项")
    summary: dict[str, int] = Field(default_factory=dict, description="各类别统计")
    duration_ms: int | None = Field(None, description="扫描耗时（毫秒）")

    @property
    def modified_items(self) -> list[ScannedItem]:
        """获取所有修改过的配置项"""
        return [item for item in self.items if item.change_type != ChangeType.DEFAULT]

    @property
    def total_count(self) -> int:
        """配置项总数"""
        return len(self.items)

    @property
    def modified_count(self) -> int:
        """修改过的配置项数量"""
        return len(self.modified_items)


class SourceSystem(BaseModel):
    """来源系统信息"""

    os: str = Field("Windows 11", description="操作系统")
    version: str = Field(..., description="系统版本，如 23H2")
    build: str = Field(..., description="构建号")
    hostname: str = Field(..., description="主机名")
    username: str = Field(..., description="用户名")


class FontInfo(BaseModel):
    """字体信息"""

    name: str = Field(..., description="字体名称")
    file: str = Field(..., description="字体文件相对路径")
    family: str | None = Field(None, description="字体家族")
    style: str | None = Field(None, description="字体样式")
    usage: list[str] = Field(default_factory=list, description="使用场景")
    sha256: str | None = Field(None, description="文件哈希")


class RegistryEntry(BaseModel):
    """注册表条目"""

    file: str = Field(..., description="reg 文件相对路径")
    description: str = Field(..., description="描述")
    keys_count: int = Field(..., description="包含的键数量")
    requires_restart: bool = Field(False, description="是否需要重启")
    requires_admin: bool = Field(True, description="是否需要管理员权限")


class ExportOptions(BaseModel):
    """导出选项"""

    include_fonts: bool = Field(True, description="包含字体")
    include_wallpapers: bool = Field(True, description="包含壁纸")
    include_cursors: bool = Field(True, description="包含鼠标指针")
    include_terminal: bool = Field(True, description="包含终端配置")
    include_vscode: bool = Field(True, description="包含 VS Code 配置")
    include_browser: bool = Field(False, description="包含浏览器配置")


class ImportInstructions(BaseModel):
    """导入说明"""

    order: list[str] = Field(default_factory=list, description="应用顺序")
    warnings: list[str] = Field(default_factory=list, description="警告信息")
    requires_admin: bool = Field(False, description="需要管理员权限")
    requires_restart: bool = Field(False, description="需要重启应用")
    requires_reboot: bool = Field(False, description="需要重启系统")


class Manifest(BaseModel):
    """
    配置包清单 - manifest.json 的完整结构
    """

    schema_version: str = Field("1.0.0", alias="$schema", description="Schema 版本")
    version: str = Field("1.0.0", description="包版本")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    created_by: str = Field("WinstyleS", description="创建工具")

    source_system: SourceSystem = Field(..., description="来源系统信息")
    export_options: ExportOptions = Field(
        default_factory=ExportOptions.model_construct, description="导出选项"
    )

    fonts: list[FontInfo] = Field(default_factory=list, description="字体列表")
    registry_entries: list[RegistryEntry] = Field(default_factory=list, description="注册表条目")

    import_instructions: ImportInstructions = Field(
        default_factory=ImportInstructions.model_construct, description="导入说明"
    )

    class Config:
        populate_by_name = True
