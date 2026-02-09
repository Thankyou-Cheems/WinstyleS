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

## 📋 支持的配置项

| 类别 | 配置项 |
|------|--------|
| 🔤 **字体** | 系统字体替换、FontLink、ClearType |
| 🎨 **主题** | 深色/浅色模式、强调色、窗口颜色 |
| 🖼️ **壁纸** | 桌面壁纸、锁屏壁纸 |
| 🖱️ **鼠标** | 自定义指针方案 |
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

# 导入配置包
winstyles import ./my-style.zip

# 生成报告但跳过联网更新检查
winstyles report --no-check-updates
```

跨设备迁移建议（最小可用）：
- 导出端使用：`winstyles export ./my-style.zip --include-font-files`
- 导入端先预览：`winstyles import ./my-style.zip --dry-run`
- 确认后执行：`winstyles import ./my-style.zip`

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
pytest

# 运行代码检查
ruff check src/
black --check src/
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
