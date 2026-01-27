# 贡献指南

感谢你对本项目的关注！欢迎提交 Issue 和 Pull Request。

## 🚀 开发环境设置

### 前置要求

- Python 3.11+
- Git

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/{{GITHUB_USER}}/{{REPO_NAME}}.git
cd {{REPO_NAME}}

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"

# 验证安装
{{COMMAND_NAME}} --version
```

## 📁 项目结构

```
src/{{PACKAGE_NAME}}/
├── core/           # 核心业务逻辑
├── utils/          # 通用工具
└── main.py         # 入口
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 显示覆盖率
pytest --cov=src/{{PACKAGE_NAME}}
```

## 📝 代码规范

```bash
# 格式化
black src/ tests/

# Lint
ruff check src/ tests/

# 类型检查
mypy src/{{PACKAGE_NAME}}
```

### 提交前检查

- [ ] 代码已格式化
- [ ] 通过 lint 检查
- [ ] 测试通过
- [ ] 更新了文档（如需要）

## 📋 Issue 和 PR

### Issue

- 🐛 Bug: 请提供复现步骤
- ✨ Feature: 请描述使用场景

### Pull Request

- 关联相关 Issue
- 确保 CI 通过

感谢你的贡献！🎉
