---
name: bilingual-commit
description: 生成中文在前的双语 Git commit message，遵循 Conventional Commits 规范
---

# 双语 Commit Message Skill

生成格式规范的中英双语 Git commit message，中文在前，英文在后。

## 📋 Commit Message 格式

```
<type>(<scope>): <中文描述>

<英文描述>

<可选的详细说明>
```

### 示例

```
feat(core): 添加用户认证模块

Add user authentication module

- 实现 JWT token 生成和验证
- 添加登录/注册 API
- 集成 Redis 会话存储
```

## 🏷️ Type 类型

| Type | 中文 | 使用场景 |
|------|------|----------|
| `feat` | 新功能 | 新增功能 |
| `fix` | 修复 | Bug 修复 |
| `docs` | 文档 | 文档变更 |
| `style` | 样式 | 代码格式（不影响逻辑） |
| `refactor` | 重构 | 重构代码 |
| `perf` | 性能 | 性能优化 |
| `test` | 测试 | 添加/修改测试 |
| `build` | 构建 | 构建系统或依赖变更 |
| `ci` | CI | CI 配置变更 |
| `chore` | 杂务 | 其他不修改 src/test 的变更 |
| `revert` | 回滚 | 回滚之前的提交 |

## 🔧 生成流程

### 第 1 步：分析变更

```bash
# 查看变更概览
git status

# 查看详细差异（用于理解变更内容）
git diff --stat
git diff --cached --stat  # 已暂存的
```

### 第 2 步：确定 Type 和 Scope

根据变更内容：

1. **Type**: 根据变更性质选择（见上表）
2. **Scope**: 变更涉及的模块（可选）
   - 如果只涉及一个模块：`feat(auth)`
   - 如果涉及多个模块：`feat` 或 `feat(core,api)`
   - 常见 scope: `core`, `api`, `ui`, `cli`, `docs`, `deps`

### 第 3 步：撰写描述

**中文描述规则：**
- 使用动词开头：添加、修复、更新、移除、重构
- 简洁明了，不超过 50 字
- 不加句号

**英文描述规则：**
- 使用动词原形开头：Add, Fix, Update, Remove, Refactor
- 首字母大写
- 不超过 50 字符
- 不加句号

**中英对照常用动词：**

| 中文 | 英文 |
|------|------|
| 添加 | Add |
| 实现 | Implement |
| 修复 | Fix |
| 更新 | Update |
| 移除/删除 | Remove |
| 重构 | Refactor |
| 优化 | Optimize |
| 改进 | Improve |
| 支持 | Support |
| 初始化 | Initialize |
| 配置 | Configure |
| 集成 | Integrate |

### 第 4 步：添加详细说明（可选）

如果变更较复杂，在空行后添加：
- 使用 `-` 列表格式
- 中英文可以只写一种
- 解释 WHY 而不只是 WHAT

### 第 5 步：执行提交

```bash
# 暂存所有变更
git add -A

# 提交（使用 -m 多行消息）
git commit -m "<第一行>" -m "<第二行>" -m "<详细说明>"
```

## 📝 完整示例

### 单文件小改动

```
fix(api): 修复用户列表分页错误

Fix pagination error in user list API
```

### 新功能

```
feat(auth): 添加 OAuth2 第三方登录支持

Add OAuth2 third-party login support

- 支持 Google、GitHub 登录
- 添加 OAuth 回调处理
- 更新用户模型以存储 OAuth 信息
```

### 项目初始化

```
init: 初始化项目结构

Initialize project structure

- 创建 src-layout 目录结构
- 添加 pyproject.toml 配置
- 添加开源标准文档 (README, LICENSE, CONTRIBUTING)
- 配置 GitHub Actions CI
```

### 文档更新

```
docs: 更新 README 安装说明

Update installation instructions in README
```

### 依赖更新

```
build(deps): 升级 pydantic 到 v2.5

Upgrade pydantic to v2.5
```

## ⚡ 快速模板

根据场景复制使用：

**初始化项目：**
```
init: 初始化项目结构

Initialize project structure
```

**添加新功能：**
```
feat(<scope>): 添加<功能>

Add <feature>
```

**修复 Bug：**
```
fix(<scope>): 修复<问题>

Fix <issue>
```

**重构代码：**
```
refactor(<scope>): 重构<模块>

Refactor <module>
```

**更新文档：**
```
docs: 更新<文档>

Update <document>
```
