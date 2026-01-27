---
name: opensource-python-init
description: 初始化一个标准的开源 Python 项目，包含现代化架构、文档结构和 CI/CD 配置
---

# 开源 Python 项目初始化 Skill

本 skill 指导如何从零初始化一个符合开源标准的 Python 项目。

## 📋 前置信息收集

在开始之前，向用户确认以下信息：

1. **项目名称** - 英文，用于包名（如 `wss`）
2. **项目描述** - 一句话描述项目功能
3. **Python 版本** - 推荐 3.11+
4. **项目类型** - CLI / GUI / 库 / Web
5. **许可证** - 推荐 MIT（开源友好）

## 🚀 初始化流程

### 第 1 步：创建目录结构

使用 `src-layout`（Python 社区推荐的最佳实践）：

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force -Path `
  ".github/workflows", `
  "docs", `
  "src/<package_name>/core", `
  "src/<package_name>/utils", `
  "tests/unit", `
  "tests/integration"
```

根据项目类型添加额外目录：
- **CLI 项目**: 无需额外目录
- **GUI 项目**: `src/<package_name>/gui/views`
- **有插件系统**: `src/<package_name>/plugins`
- **需要适配器模式**: `src/<package_name>/infra`
- **有数据模型**: `src/<package_name>/domain`
- **有静态数据**: `data/`
- **有资源文件**: `assets/`

### 第 2 步：创建必需文件

按以下顺序创建（优先级从高到低）：

#### 2.1 项目配置 (pyproject.toml)

```toml
[project]
name = "<package_name>"
version = "0.1.0"
description = "<项目描述>"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Your Name", email = "you@example.com" }]

dependencies = [
    # 根据项目类型添加
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.12.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[project.scripts]
<command_name> = "<package_name>.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

#### 2.2 开源必需文件

| 文件 | 说明 | 模板 |
|------|------|------|
| `LICENSE` | 许可证 | 见 `templates/LICENSE_MIT` |
| `README.md` | 项目首页 | 见 `templates/README.md` |
| `CONTRIBUTING.md` | 贡献指南 | 见 `templates/CONTRIBUTING.md` |
| `CHANGELOG.md` | 版本日志 | 见 `templates/CHANGELOG.md` |
| `.gitignore` | Git 忽略 | 见 `templates/.gitignore` |

#### 2.3 源代码骨架

```
src/<package_name>/
├── __init__.py         # 版本号
├── __main__.py         # python -m <package> 入口
├── main.py             # CLI/应用入口
└── ...                 # 其他模块
```

#### 2.4 CI 配置

创建 `.github/workflows/ci.yml`，参考 `templates/ci.yml`

### 第 3 步：架构设计

根据项目复杂度选择架构：

#### 简单项目（脚本/小工具）
```
src/<package>/
├── main.py
└── utils.py
```

#### 中等项目（CLI 工具）
```
src/<package>/
├── main.py          # CLI 入口
├── core/            # 核心逻辑
├── utils/           # 工具函数
└── config.py        # 配置
```

#### 复杂项目（六边形架构）
```
src/<package>/
├── main.py          # 入口
├── core/            # 核心业务逻辑（纯函数，无副作用）
│   ├── engine.py    # 主引擎/编排器
│   ├── analyzer.py  # 分析器
│   └── exceptions.py
├── domain/          # 数据模型（Pydantic）
│   ├── models.py
│   └── types.py     # 枚举
├── infra/           # 基础设施（与外部系统交互）
│   ├── registry.py  # 适配器（接口 + 实现 + Mock）
│   └── filesystem.py
├── plugins/         # 插件系统
│   └── base.py      # 抽象基类
├── gui/             # 可选：图形界面
└── utils/           # 通用工具
```

**架构原则：**
1. `core/` 不依赖 `infra/`，通过接口注入
2. `infra/` 每个适配器提供：接口 + 真实实现 + Mock 实现
3. `plugins/` 使用抽象基类定义接口
4. `domain/` 只有数据模型，无业务逻辑

### 第 4 步：文档结构

#### 开源标准文档（根目录）

| 文件 | 内容 | 受众 |
|------|------|------|
| `README.md` | 项目介绍、快速开始、功能列表 | 用户 |
| `CONTRIBUTING.md` | 开发环境、架构说明、代码规范 | 贡献者 |
| `CHANGELOG.md` | 版本变更记录 | 用户/贡献者 |
| `LICENSE` | 许可证 | 法律 |

#### 技术文档（docs/ 目录）

| 文件 | 内容 |
|------|------|
| `docs/design.md` | 详细技术设计（可选） |
| `docs/api/` | API 文档（自动生成） |

#### 不应公开的内容

以下内容**不应**放在仓库中：
- 个人工作笔记（如 starting.md、todo.md）
- 未完成的设计草稿
- 内部任务追踪

**替代方案：**
- 使用 **GitHub Issues** 追踪任务
- 使用 **GitHub Projects** 管理看板
- 使用 **GitHub Wiki** 放内部文档

### 第 5 步：验证

```bash
# 安装项目
pip install -e ".[dev]"

# 验证 CLI
<command_name> --version

# 运行测试
pytest

# 代码检查
ruff check src/
black --check src/
```

## 📁 最终目录结构示例

```
<project>/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── pyproject.toml
│
├── docs/
│   └── design.md           # 可选
│
├── src/
│   └── <package>/
│       ├── __init__.py
│       ├── __main__.py
│       ├── main.py
│       ├── core/
│       ├── domain/         # 可选
│       ├── infra/          # 可选
│       ├── plugins/        # 可选
│       ├── gui/            # 可选
│       └── utils/
│
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

## 🔗 相关资源

- [Python Packaging User Guide](https://packaging.python.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://conventionalcommits.org/)
