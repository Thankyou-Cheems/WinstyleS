# WinstyleS 技术设计文档

WinstyleS (Windows Style Sync) - Windows 个性化设置同步工具

## GUI 方案

- Web GUI (本地服务器 + 浏览器前端，默认入口)
- 内置 CustomTkinter GUI (可选)

> 本文档记录项目的详细技术设计，供开发者参考。

## 目录

1. [功能规格](#功能规格)
2. [扫描维度](#扫描维度)
3. [数据结构](#数据结构)
4. [CLI 接口](#cli-接口)
5. [Web API 约定](#web-api-约定)

---
# 扫描所有配置
winstyles scan

# 仅扫描字体和终端，输出 JSON
winstyles scan -c fonts -c terminal -f json

# 导出配置包
winstyles export ./my-style.zip

# 预览导入（不实际应用）
winstyles import ./my-style.zip --dry-run

# 导入并跳过还原点
winstyles import ./my-style.zip --skip-restore-point
```

---

## 相关文档

- [README.md](../README.md) - 项目概述
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南和架构说明

---

## Web API 约定

Web GUI 通过 `start_web_ui.py` 提供的本地 API 调用后端能力。

- `POST /api/scan`
  - 输入：`{ "categories": ["fonts","terminal"], "format": "table|json|yaml", "modifiedOnly": true }`
  - 行为：`format=table` 时后端仍返回 JSON 数据（供前端渲染表格）；`modifiedOnly` 在脚本模式与打包模式都生效

- `POST /api/export_config`
  - 输入：`{ "path": "D:\\...\\my-style.zip", "categories": "fonts,terminal", "includeDefaults": false, "includeFontFiles": true }`
  - 行为：支持将 `includeFontFiles` 透传到导出流程，仅在开启时打包字体文件资产

- `POST /api/generate_report`
  - 输入：`{ "format": "markdown|html", "checkUpdates": true }`
  - 行为：`checkUpdates=false` 时跳过字体更新检查（减少联网请求）

- `POST /api/check_font_updates`
  - 行为：执行真实字体扫描与更新检查，返回更新列表（不再返回固定空数组）

- `POST /api/refresh_font_db`
  - 行为：主动拉取远程字体数据库并返回条目数量

- `POST /api/import_config`
  - 输入方式 A：`{ "path": "C:\\...\\my-style.zip", "dryRun": true, "skipRestore": true }`
  - 输入方式 B：`{ "fileName": "my-style.zip", "fileBase64": "<base64/data-url>", "dryRun": true, "skipRestore": true }`
  - 行为：当传入 `fileBase64` 时，后端会写入临时 zip 再执行导入
