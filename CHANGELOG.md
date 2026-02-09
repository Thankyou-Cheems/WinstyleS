# Changelog

本项目遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

### Fixed
- 修复字体更新页面运行时异常：使用 `ScannedItem.current_value`，避免访问不存在字段
- 修复开源字体模型与配置包字体模型重名冲突：新增 `OpenSourceFontInfo` 并替换相关引用
- 修复 `winstyles report --open` 重复打开浏览器的问题
- 修复 Web 模式 `check_font_updates` 固定返回空结果的问题，改为真实检查流程
- 修复 Web 模式导入在浏览器仅有文件对象时无法导入的问题，新增 zip 上传导入通道
- 修复版本显示不一致：`__version__` 与 `pyproject.toml` 版本对齐为 `0.2.0`
- 修复 Web 扫描“仅显示修改项”在打包模式不生效的问题
- 修复导出“包含字体文件”选项未透传到后端的问题，新增 `--include-font-files`
- 修复报告“检查字体更新”开关始终生效的问题，新增 `--check-updates/--no-check-updates`
- 修复 Web 前端未绑定功能：字体数据库刷新、导出预览、导出日志复制、扫描格式选择
- 修复 Windows 非 UTF-8 控制台执行 `winstyles report` 时的编码异常（改为 ASCII 转义输出）
- 修复跨设备导入时资产路径失效问题：导入会将包内 assets 重定位到 `~/.winstyles/imported_assets/<scan_id>`
- 修复 Windows Terminal 导入未实现问题：支持将扫描项写回本机 `settings.json`
- 修复 PowerShell Profile 跨用户路径问题：导入时写入当前用户 Profile 路径
- 修复注册表写入 `REG_MULTI_SZ` 推断，确保 FontLink 多字符串值可正确导入

### Changed
- 调整 `build.yml` 触发策略：移除 `pull_request` 触发，仅保留手动触发和 tag 触发
- 增强字体扫描器：为 FontSubstitutes / FontLink 补充字体文件关联，便于导出字体资产
- 打包模式（frozen）新增直接导出实现，不再返回 `Export not yet supported in packaged mode`

## [0.3.0] - 2026-01-27

### Added
- **字体更新检查功能**:
  - 新增「字体更新」页面，检查已安装开源字体的最新版本
  - 集成 `UpdateChecker` 模块，支持从 GitHub Releases 获取版本信息
  - 一键打开下载页面，方便用户更新字体
  - 整合 braver/programmingfonts 社区字体数据库
- **报告增强**:
  - 新增「浏览器打开」按钮，支持生成 HTML 报告并在默认浏览器中打开
  - 报告中显示字体版本信息和更新状态
- **前端 UI 重新设计**:
  - 采用微软 Fluent Design System 亚克力风格
  - 新增 SVG 图标，提升视觉效果
  - 优化暗色模式支持
  - 新增加载状态和动画效果
  - 新增键盘快捷键支持（Ctrl+1-6 快速切换页面）
- **CustomTkinter GUI 增强**:
  - 新增「字体更新」页面
  - 新增「浏览器打开报告」功能
  - 优化导航和状态栏样式

### Changed
- 前端导航新增「报告」和「字体更新」入口
- CustomTkinter GUI 导航新增「字体更新」入口
- 统一采用 Windows 11 Fluent Design 调色板

### Fixed
- 修复 GUI 中缺失报告和字体更新功能入口的问题

## [0.2.0] - 2026-01-27

### Added
- **扫描报告功能**:
  - 新增 `winstyles report` 命令，支持生成 Markdown/HTML 报告
  - GUI 集成：主界面新增 "报告" 标签页，支持应用内查看
  - 智能分类：区分用户自定义配置、系统版本差异、系统标准配置
  - 开源字体识别：自动检测 Maple Mono, JetBrains Mono 等字体并提供下载链接
- **新扫描器插件**:
  - `ThemeScanner`: 扫描深色模式、强调色、透明度设置
  - `WallpaperScanner`: 扫描桌面壁纸路径、样式、TranscodedWallpaper 文件
  - `CursorScanner`: 扫描鼠标指针方案及光标文件
  - `VSCodeScanner`: 扫描 VS Code 字体、主题、终端配置
- **增强还原功能**:
  - `restore` 命令支持 `--system-restore` 调用 Windows 系统还原 UI
  - 备份列表显示更详细的信息（时间、大小）
- **数据更新**:
  - 更新 Windows 11 23H2 默认值数据库
  - 新增 `data/opensource_fonts.json` 字体数据库

### Changed
- CLI: 优化 `restore` 命令的交互提示
- Core: 优化扫描器加载机制

### Fixed
- 修复了版本间字体替换映射导致的误报（如 `Helv` -> `MS Sans Serif`）

## [0.1.0] - 2026-01-27

### Added
- 项目初始化骨架
- CLI 命令框架 (scan, export, import, diff, inspect, restore)
- 扫描 MVP：支持 scan 输出与默认值对比
- 导出/导入 MVP：生成配置包并支持 dry-run 导入
- diff/inspect：支持配置包对比与检视
- GUI 重做：扁平现代风格与扫描交互
- Tauri GUI：前端亚克力风格界面（实验性）
- GUI 入口：优先启动 Tauri，失败回退到内置 GUI
- GUI 入口：检测到预编译 exe 时直接启动
- 核心数据模型 (ScannedItem, ScanResult, Manifest)
- **Patch**: 向后兼容的 Bug 修复
