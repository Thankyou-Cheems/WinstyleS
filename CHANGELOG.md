# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

### Added
- 项目初始化骨架
- CLI 命令框架 (scan, export, import, diff, inspect, restore)
- 核心数据模型 (ScannedItem, ScanResult, Manifest)
- 扫描器插件系统
- 字体扫描器骨架 (FontSubstitutes, FontLink)
- 终端扫描器骨架 (Windows Terminal, PowerShell)
- 注册表适配器 (真实 + Mock)
- 文件系统适配器 (真实 + Mock)
- Windows API 封装 (字体安装、权限检查)
- 系统还原点管理
- GUI 主窗口骨架 (CustomTkinter)
- Windows 11 23H2 默认值基准库

### Changed
- N/A

### Fixed
- N/A

---

## 版本说明

- **Major**: 不兼容的 API 变更
- **Minor**: 向后兼容的功能新增
- **Patch**: 向后兼容的 Bug 修复
