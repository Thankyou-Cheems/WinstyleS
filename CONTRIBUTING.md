# 贡献指南

感谢你对 WinstyleS 项目的关注！欢迎提交 Issue 和 Pull Request。

## 🚀 开发环境设置

### 前置要求

- Python 3.11+
- Windows 10/11
- Git

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/yourname/winstyles.git
cd winstyles

# 创建虚拟环境 (推荐)
python -m venv .venv
.venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 验证安装
winstyles --version
```

## 📁 项目结构

```
src/winstyles/
├── core/           # 核心业务逻辑 (StyleEngine, DiffAnalyzer)
├── domain/         # Pydantic 数据模型
├── infra/          # 基础设施 (注册表、文件系统、Windows API)
├── plugins/        # 扫描器插件
├── gui/            # CustomTkinter 图形界面
├── utils/          # 通用工具
└── main.py         # CLI 入口
```

### 架构概述

项目采用**六边形架构**变体，核心原则：

1. **核心层 (`core/`)** 不依赖具体 UI 或系统 API
2. **基础设施层 (`infra/`)** 使用适配器模式，便于 Mock 测试
3. **插件系统 (`plugins/`)** 所有扫描器继承 `BaseScanner`

```
┌─────────────┐
│   CLI/GUI   │  ← 接入层
└──────┬──────┘
       │
┌──────▼──────┐
│ StyleEngine │  ← 核心层 (编排)
└──────┬──────┘
       │
┌──────▼──────┐
│   Plugins   │  ← 扫描器插件
└──────┬──────┘
       │
┌──────▼──────┐
│    Infra    │  ← 基础设施 (Registry/FileSystem)
└─────────────┘
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=src/winstyles --cov-report=term-missing

# 仅运行单元测试
pytest tests/unit/
```

## 📝 代码规范

我们使用以下工具保证代码质量：

```bash
# 格式化代码
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/winstyles
```

### 提交前检查清单

- [ ] 代码已格式化 (`black`)
- [ ] 通过 lint 检查 (`ruff`)
- [ ] 测试通过 (`pytest`)
- [ ] 添加/更新了相关测试
- [ ] 更新了文档（如有需要）

## 🔌 添加新扫描器

1. 在 `src/winstyles/plugins/` 创建新文件
2. 继承 `BaseScanner` 类
3. 实现必需方法：`id`, `name`, `category`, `scan()`, `apply()`

```python
from winstyles.plugins.base import BaseScanner
from winstyles.domain.models import ScannedItem

class MyScanner(BaseScanner):
    @property
    def id(self) -> str:
        return "my_scanner"
    
    @property
    def name(self) -> str:
        return "My Scanner"
    
    @property
    def category(self) -> str:
        return "my_category"
    
    def scan(self) -> list[ScannedItem]:
        # 实现扫描逻辑
        pass
    
    def apply(self, item: ScannedItem) -> bool:
        # 实现应用逻辑
        pass
```

## 📋 Issue 和 PR 规范

### Issue

- 🐛 Bug: 请提供复现步骤、系统版本、错误信息
- ✨ Feature: 请描述使用场景和预期行为

### Pull Request

- 关联相关 Issue
- 描述改动内容和原因
- 确保 CI 通过

## 💬 获取帮助

- 提交 Issue
- 在 Discussions 中讨论

感谢你的贡献！🎉
