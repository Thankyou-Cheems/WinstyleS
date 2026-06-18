# WinstyleS (Windows Style Sync)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Thankyou-Cheems/WinstyleS/actions/workflows/ci.yml/badge.svg)](https://github.com/Thankyou-Cheems/WinstyleS/actions)

> 🎨 **WinstyleS (Windows Style Sync)** - 自动探测、导出、同步你的 Windows 美化配置

## ✨ 功能特性

- 🔍 **智能扫描** - 自动检测系统字体、主题、终端配置等个性化设置
- 📄 **分析报告** - 生成可视化报告，智能区分用户自定义项与系统差异，自动识别开源字体
- 📊 **差异对比** - 与 Windows 默认值对比，精确识别你的自定义修改
- 📦 **一键导出** - 打包配置文件和资源文件（字体、壁纸等）
- 🚀 **快速导入** - 在新设备上一键还原所有设置
- 🛡️ **安全回滚** - 修改前自动创建系统还原点

## 能力状态

已完成并有测试覆盖：
- 扫描/报告/导出基础链路，以及字体、终端、主题、壁纸、鼠标指针、VS Code 主要配置项
- zip 配置包路径安全校验、dry-run 逐项计划、导入前系统还原点检查
- 导入前备份包、`import_log.json` 审计日志、需要提升权限时的统一中止提示
- Web GUI 的扫描、报告、导出、导入、字体更新检查与统一 API 错误结构

实验性或受环境限制：
- 写回 Windows Terminal / PowerShell Profile / VS Code 配置已实现，但仍建议先执行 `--dry-run`
- 系统级注册表和字体相关项依赖 Windows 权限；需要管理员权限的包会在 apply 前中止
- Web GUI 是本地服务模式，不提供远程访问或多用户隔离

## 📋 支持的配置项

| 类别 | 配置项 |
|------|--------|
| 🔤 **字体** | 系统字体替换、FontLink、已安装字体清单、ClearType 参数、开源字体识别 |
| 🎨 **主题** | 深色/浅色模式、强调色、DWM Colorization 颜色项 |
| 🖼️ **壁纸** | 桌面壁纸、锁屏策略项、Spotlight 基础识别 |
| 🖱️ **鼠标** | 自定义指针方案、CursorSize、路径归一化 |
| 💻 **终端** | Windows Terminal、PowerShell Profile、Oh My Posh |
| 📝 **编辑器** | VS Code 字体和主题设置 |

## 🚀 快速开始

### 安装

```bash
pip install winstyles
```

### 基本用法

```bash
# 扫描当前系统配置
winstyles scan

# 仅扫描字体和终端
winstyles scan -c fonts -c terminal

# 生成系统分析报告
winstyles report

# 导出配置包
winstyles export ./my-style.zip

# 导出时包含字体文件
winstyles export ./my-style.zip --include-font-files

# 预览导入（不实际应用）
winstyles import ./my-style.zip --dry-run
# dry-run 会输出逐项计划（action/target/risk），且不会复制资源或写入设置

# 导入配置包
winstyles import ./my-style.zip
# 默认会先检查权限、创建系统还原点、生成导入前备份和 import_log.json；
# 如需显式跳过系统还原点可使用 --skip-restore-point

# 生成报告但跳过联网更新检查
winstyles report --no-check-updates
```

跨设备迁移建议（最小可用）：
- 导出端使用：`winstyles export ./my-style.zip --include-font-files`
- 导入端先预览：`winstyles import ./my-style.zip --dry-run`
- 确认后执行：`winstyles import ./my-style.zip`
- zip 包会在导入前做路径安全校验；系统还原点创建失败时默认中止导入
- 需要管理员权限的配置项会在 apply 前统一检查；权限不足时不会执行部分导入
- 实际导入会生成 `~/.winstyles/backups/pre_import_*.zip` 和 `~/.winstyles/import_logs/*/import_log.json`
- Windows Terminal / VS Code 设置写回会先解析现有 JSONC，解析失败时不会覆盖原文件

报告说明：
- CLI 模式下 `winstyles report` 直接输出 Markdown；HTML 报告会转义扫描值并过滤不安全链接
- YAML 输出依赖已包含在默认安装中

### 启动 Web GUI
```bash
python -m winstyles gui
```

这将自动启动简单的本地 Web 服务器并在默认浏览器中打开用户界面。
界面支持扫描、报告生成、导出导入等所有核心功能。

Web 导入说明：
- 支持直接输入本地路径（`D:\path\to\my-style.zip`）
- 支持拖拽或点选 `.zip` 文件，浏览器会将文件上传到本地服务端后执行导入

## 🛠️ 从源码安装

```bash
# 克隆仓库
git clone https://github.com/Thankyou-Cheems/WinstyleS.git
cd WinstyleS

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
uv run --python 3.12 --extra dev pytest tests -v --cov=src/winstyles --cov-report=term-missing --capture=no

# 运行代码检查
uv run --python 3.12 --extra dev ruff check src tests
uv run --python 3.12 --extra dev black --check src tests
uv run --python 3.12 --extra dev mypy src/winstyles

# 发布前检查（完整质量门 + 关键命令）
uv run --python 3.12 --extra dev python scripts/release_check.py

# 快速检查（仅 winstyles --version 与 winstyles scan -f json）
uv run --python 3.12 --extra dev python scripts/release_check.py --quick
```

## 📖 文档

- [贡献指南](CONTRIBUTING.md) - 开发环境设置、架构说明、代码规范
- [技术设计](docs/design.md) - 详细的功能规格和数据结构
- [更新日志](CHANGELOG.md) - 版本变更记录
- [协作约定](AGENTS.md) - 文档同步与发布检查清单

## 🤝 贡献

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解：

- 开发环境设置
- 项目架构
- 如何添加新的扫描器
- 代码规范和提交流程

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。

## ⚠️ 免责声明

本工具会修改 Windows 系统设置和注册表。虽然我们会在修改前创建系统还原点，但仍建议：

- 在使用前备份重要数据
- 仔细预览将要应用的变更
- 如遇问题，使用系统还原功能恢复

---

**Made with ❤️ for Windows customization enthusiasts**
