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
# 输出摘要 + Dry-run Plan（逐项 action/target/risk/reason）
# 不创建 ~/.winstyles/imported_assets，不复制资源，不写注册表/配置文件

# 导入并跳过还原点
winstyles import ./my-style.zip --skip-restore-point
```

导入安全约定：
- 默认 apply 会先创建系统还原点；创建失败返回 `aborted=true`、`error_code=restore_point_failed`，并且不会执行扫描器写入。
- `--skip-restore-point` 是唯一跳过还原点失败中止的显式覆盖。
- apply 前统一执行管理员权限检查；HKLM/HKCR 注册表、系统 API、Windows 系统目录文件等需要提升权限的项会在权限不足时返回 `error_code=admin_required`，不会执行部分导入。
- apply 前会自动扫描当前系统并导出导入前备份包到 `~/.winstyles/backups/pre_import_*.zip`；备份失败返回 `error_code=pre_import_backup_failed`，不会继续写入。
- 每次实际导入会生成 `~/.winstyles/import_logs/<timestamp>_<scan_id>/import_log.json`，记录加载、权限、还原点、备份、资源重定位和逐项 apply 结果。
- zip 导入必须先校验成员路径，拒绝绝对路径、盘符路径和 `..` 路径穿越。
- `scan.json` 缺失或无效时返回结构化错误，不执行部分导入。
- Windows Terminal / VS Code 写回前必须解析现有 JSONC；解析失败时返回失败并保持原文件不变。
- 包内 `assets` 仅在实际 apply 时重定位，dry-run 只基于原始扫描项生成预览。

---

## 字体扫描输出约定（Phase B/B1）

- `fonts` 类别新增 `installed.*` 项，用于记录 HKLM/HKCU 已安装字体清单。
- `installed.*` 的 `metadata` 包含：
  - `scope`（`machine`/`user`）
  - `readonly`（导入时跳过写回）
  - `is_opensource` 与 `opensource`（命中开源字体数据库时）
- `fonts` 类别新增 `cleartype.*` 项，覆盖 `enabled/mode/gamma/orientation/contrast`。
- 开源字体识别统一通过 `winstyles.utils.font_utils.identify_opensource()`。

## 终端扫描输出约定（Phase B/B2）

- `terminal` 类别新增 `ohMyPosh.installed`：
  - `current_value` 为是否检测到 Oh My Posh 可执行文件
  - `metadata.executable_path` 为命中路径（若有）
- `terminal` 类别新增 `ohMyPosh.theme.*`：
  - 从 PowerShell Profile 中解析 `oh-my-posh init ... --config ...`
  - 若主题文件存在，会记录到 `associated_files`
- `ohMyPosh.*` 项属于观察型数据，`metadata.readonly=true`，导入时跳过写回。

## 壁纸扫描输出约定（Phase B/B3）

- `wallpaper.path/style/tile/transcoded` 归类为 `surface=desktop`。
- 锁屏相关新增 `wallpaper.lockscreen.*`：
  - `path`（策略项 LockScreenImage）
  - `spotlightEnabled`、`spotlightOverlayEnabled`
  - `spotlightAssetCount`（基础可用资产数量）
- 锁屏与 Spotlight 观测项标记为 `metadata.readonly=true`，导入时跳过写回。

## 主题扫描输出约定（Phase B/B4）

- 主题新增 DWM 字段：
  - `theme.dwm.colorizationColor`
  - `theme.dwm.colorizationAfterglow`
  - `theme.dwm.colorizationColorBalance`
  - `theme.dwm.colorizationAfterglowBalance`
  - `theme.dwm.colorizationBlurBalance`
  - `theme.dwm.accentColorInactive`
- 颜色类值会同时保留 `metadata.raw_value`，写回时优先使用原始 DWORD。

## 鼠标扫描输出约定（Phase B/B5）

- 新增 `cursor.size`（读取 `CursorBaseSize/CursorSize`）。
- `cursor.*` 路径统一归一化为可解析路径，原始注册表值保存在 `metadata.raw_value`。
- 导出导入流程使用归一化路径，便于跨设备资产重定位。

## 相关文档

- [README.md](../README.md) - 项目概述
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南和架构说明

---

## Web API 约定

Web GUI 通过 `start_web_ui.py` 提供的本地 API 调用后端能力。

- `GET /api/status` 或 `POST /api/status`
  - 返回本地服务状态、运行模式和资源目录，用于前端启动时连通性检查。

所有 API 返回统一 envelope：

```json
{
  "ok": true,
  "data": {},
  "error": null,
  "code": "ok",
  "message": "OK"
}
```

错误返回使用同一结构，`ok=false`，并提供稳定 `code` 与可读 `message`：

```json
{
  "ok": false,
  "data": null,
  "error": "Invalid JSON body",
  "code": "invalid_json",
  "message": "Invalid JSON body"
}
```

- `POST /api/scan`
  - 输入：`{ "categories": ["fonts","terminal"], "format": "table|json|yaml", "modifiedOnly": true }`
  - 行为：`format=table` 时后端仍返回 JSON 数据（供前端渲染表格）；`modifiedOnly` 在脚本模式与打包模式都生效

- `POST /api/export_config`
  - 输入：`{ "path": "D:\\...\\my-style.zip", "categories": "fonts,terminal", "includeDefaults": false, "includeFontFiles": true }`
  - 行为：支持将 `includeFontFiles` 透传到导出流程，仅在开启时打包字体文件资产

- `POST /api/generate_report`
  - 输入：`{ "format": "markdown|html", "checkUpdates": true }`
  - 行为：`checkUpdates=false` 时跳过字体更新检查（减少联网请求）；HTML 输出会转义扫描值并过滤不安全链接协议

- `POST /api/check_font_updates`
  - 行为：执行真实字体扫描与更新检查，返回更新列表（不再返回固定空数组）

- `POST /api/refresh_font_db`
  - 行为：主动拉取远程字体数据库并返回条目数量

- `POST /api/import_config`
  - 输入方式 A：`{ "path": "C:\\...\\my-style.zip", "dryRun": true, "skipRestore": true }`
  - 输入方式 B：`{ "fileName": "my-style.zip", "fileBase64": "<base64/data-url>", "dryRun": true, "skipRestore": true }`
  - 行为：当传入 `fileBase64` 时，后端会写入临时 zip 再执行导入；导入时会将包内 `assets` 重定位到 `~/.winstyles/imported_assets/<scan_id>` 再应用，避免跨设备路径失效
  - dry-run 返回除计数外还包含 `dry_run_plan`（逐项预览）与 `risk_summary`，且不会触发资源重定位
  - 导入中止时，核心导入摘要会放入错误 envelope 的 `data`，保留 `aborted`、`error_code`、`error`、`applied=0`、`import_log_path` 等字段

## 发布治理

- 发布前检查脚本：`uv run --python 3.12 --extra dev python scripts/release_check.py`
- 快速检查脚本：`uv run --python 3.12 --extra dev python scripts/release_check.py --quick`
- 完整检查顺序：`black --check` -> `ruff check` -> `mypy` -> `pytest` -> `winstyles --version` -> `winstyles scan -f json`
- 版本号、依赖、CLI 行为、仓库链接变更必须同步更新 `CHANGELOG.md`、`README.md` 和本设计文档中对应段落。
