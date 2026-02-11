# WinstyleS 实际完成度审计与修订开发框架（2026-02-10）

> 这是对旧版分析文档的修订版。目标：明确“哪些已经做完、哪些还没做、下一步怎么做”。

## 0. 审计范围与证据

本次结论基于仓库现状与本地实测，不是推测：

- 代码与结构：`src/winstyles/**`、`frontend/**`、`start_web_ui.py`
- 文档与元信息：`README.md`、`docs/design.md`、`pyproject.toml`、`CHANGELOG.md`
- 质量门禁实测：
  - `ruff check src`：通过
  - `black --check src`：失败（`src/winstyles/gui/app.py` 未格式化）
  - `mypy src/winstyles`：失败（18 个类型错误）
  - `pytest`：16/16 通过（已支持仓库根目录直接运行）
  - `winstyles --version`：可用（0.2.0）
  - `winstyles scan -f json`：可用（可扫描并输出真实结果）

---

## 1. 架构纠偏（旧文档的核心偏差）

旧文档将项目假设为 `scanners/*.py + exporter.py + importer.py + rollback.py` 结构，这与当前代码不一致。

当前真实架构：

- **CLI 层**：`src/winstyles/main.py`（Typer）
- **编排层**：`src/winstyles/core/engine.py`（扫描、导出、导入、diff、inspect）
- **插件层**：`src/winstyles/plugins/*.py`（按类别扫描/应用）
- **基础设施层**：`src/winstyles/infra/*.py`（registry/filesystem/system/restore）
- **报告与更新**：`src/winstyles/core/report.py`、`src/winstyles/core/update_checker.py`
- **Web GUI**：`start_web_ui.py` + `frontend/`

结论：后续开发应继续沿用 **plugin + engine** 体系，而不是新建并平移到 `scanners/` 目录。

---

## 2. 完成度清单（已完成 / 部分完成 / 未完成）

### 2.1 基础工程与质量

| 项目 | 状态 | 说明 |
|------|------|------|
| 项目结构与打包（src layout） | ✅ 已完成 | 结构清晰，`pyproject.toml` 可编辑安装 |
| CLI 主命令（scan/export/import/diff/inspect/restore/report/gui） | ✅ 已完成 | 命令齐全，主流程可跑 |
| Ruff | ✅ 已完成 | `ruff check src` 通过 |
| Black | ⚠️ 部分完成 | `src/winstyles/gui/app.py` 未满足格式化 |
| Mypy | ❌ 未完成 | 当前 18 个错误；CI 也设置了 `continue-on-error` |
| 单元测试 | ✅ 已完成（覆盖有限） | 16 条测试通过，覆盖关键路径但总体覆盖率偏低 |

### 2.2 六大扫描能力

| 类别 | 状态 | 现状 | 主要缺口 |
|------|------|------|---------|
| 字体（FontSubstitutes/FontLink） | ⚠️ 部分完成 | 已能读替换规则、FontLink、关联字体文件 | 缺“已安装字体全量清单 / ClearType / 开源识别独立 API” |
| 主题 | ⚠️ 部分完成 | 已读深浅色、透明、强调色、调色板 | DWM 颜色项/更多系统主题细节缺失 |
| 壁纸 | ⚠️ 部分完成 | 已读 Wallpaper/Style/Tile/TranscodedWallpaper | 锁屏壁纸（策略/Spotlight）缺失 |
| 鼠标指针 | ⚠️ 部分完成 | 已读方案与多数 cursor 路径 | CursorSize、路径归一化、应用后系统广播不足 |
| 终端 | ⚠️ 部分完成 | 已支持 Windows Terminal + PowerShell Profile | Oh My Posh 检测与配置归档不完整 |
| 编辑器（VS Code） | ✅ 基本完成 | 已支持 settings.json/jsonc、字体主题提取与回写 | Insiders 与稳定版并行处理策略可继续增强 |

### 2.3 核心流程（导出/导入/回滚）

| 功能 | 状态 | 现状 | 主要缺口 |
|------|------|------|---------|
| 扫描编排 | ✅ 已完成 | `StyleEngine.scan_all()` 可用 | 异常处理仍以 `print` 为主，缺统一日志 |
| 导出 | ✅ 基本完成 | manifest + scan + assets + zip，支持 `--include-font-files` | 缺资产大小限制、缺更细粒度清单统计 |
| 导入（dry-run） | ⚠️ 部分完成 | 可给出总数摘要 | 缺“逐项计划 + 风险等级 + 详细日志” |
| 导入（apply） | ⚠️ 部分完成 | 能按项调用 scanner.apply，支持资产重定位 | 管理员校验、失败回滚策略、原子性不足 |
| 系统回滚点 | ⚠️ 部分完成 | 已有 `RestorePointManager` 可创建还原点 | 未形成“导入前备份包 + 一键回退”双保险闭环 |
| 包差异与检视（diff/inspect） | ✅ 已完成 | CLI 已可用 | 可进一步增强展示体验 |

### 2.4 报告与 Web GUI

| 功能 | 状态 | 现状 | 主要缺口 |
|------|------|------|---------|
| Markdown/HTML 报告 | ✅ 基本完成 | 可生成报告并分类变化，含开源字体识别 | 规则仍偏启发式，误报控制可提升 |
| 字体更新检查 | ✅ 已完成（基础） | 可拉取远程库并检查 GitHub release | 版本比较尚非严格 semver |
| Web API | ⚠️ 部分完成 | 扫描/导出/导入/报告/字体更新可用 | 路由规范未统一（多为 POST，缺 `status` 等） |
| 前端页面 | ⚠️ 部分完成 | 扫描、报告、字体更新、导出、导入页都已存在 | 有交互细节缺口（例如部分按钮/文案/状态一致性） |

### 2.5 数据与 CI

| 项目 | 状态 | 说明 |
|------|------|------|
| 默认值数据库 | ⚠️ 部分完成 | 目前主要是 `data/defaults/win11_23h2.json` 单文件 |
| 开源字体数据库 | ✅ 已完成（可用） | `data/opensource_fonts.json` 有较完整条目 |
| CI（Windows） | ✅ 已完成 | ruff/black/mypy/pytest/coverage 已接入 |
| CI 严格性 | ❌ 未完成 | mypy 未阻塞、black 当前不通过，离“全绿门禁”仍有距离 |

---

## 3. 本次已落地的修正（针对稳定性）

1. `tests/conftest.py`
- 增加 `src` 路径注入，`pytest` 在仓库根目录可直接运行（不依赖先 `pip install -e`）。

2. `src/winstyles/infra/registry.py`
- 增加 `winreg` 的非 Windows 导入保护，避免在 Linux/WSL 环境 import 即崩溃。
- `MockRegistryAdapter` 改为使用兼容常量，不再硬依赖 `winreg` 模块存在。

3. `frontend/main.js`
- 修复扫描结果复制按钮目标元素错误（从不存在的 `scanOutput` 改为 `scanResults`）。

---

## 4. 修订后的开发框架（按优先级）

## Phase A：质量门禁收敛（最高优先级）

目标：先把“可持续迭代能力”补齐。

- A1. 修复 `black --check src`（先处理 `src/winstyles/gui/app.py`）
- A2. 清理 mypy 错误（至少核心路径 `core/`, `plugins/`, `infra/registry.py` 先归零）
- A3. 将 mypy 从 `continue-on-error` 改为强门禁（分阶段启用）

完成标准（DoD）：
- `ruff check src` 通过
- `black --check src` 通过
- `mypy src/winstyles` 通过（或有明确、最小化豁免清单）
- `pytest` 全通过

## Phase B：扫描深度补齐（核心能力）

目标：把“可用”提升到“准确”。

- B1. 字体：补 `installed fonts`、ClearType、开源识别 API（`identify_opensource`）
- B2. 主题：补 DWM 色彩相关项（`Colorization*`）
- B3. 壁纸：补锁屏检测（策略项 + Spotlight 基础识别）
- B4. 终端：补 Oh My Posh 检测与配置定位
- B5. 鼠标：补 CursorSize、路径归一化与边界处理

完成标准：
- 每个类别至少新增 1 组单元测试和 1 组边界测试
- 导出包 `scan.json` 能体现新增字段

## Phase C：导入安全闭环（高优先级）

目标：导入从“能用”变“可审计、可回退”。

- C1. dry-run 输出逐项计划（操作、目标、风险等级）
- C2. apply 前统一权限检查（管理员能力提示）
- C3. 导入日志 `import_log.json`（步骤、成功/失败、错误详情）
- C4. “导入前自动备份当前配置包”并提供快速回退入口

完成标准：
- 导入失败时可定位到具体步骤
- 用户可用一次命令回退到导入前状态

## Phase D：Web API 规范化与前端对齐（中优先级）

目标：减少前后端协议漂移。

- D1. 增补 `GET /api/status`（OS、管理员、最近扫描时间）
- D2. 统一错误返回结构 `{ error, code, message }`
- D3. 对外保留现有端点兼容层，内部统一调用协议
- D4. 前端 loading/error/success 状态统一组件化

完成标准：
- API 文档与实现一致
- 前端关键流程（扫描/导出/导入/报告）状态反馈一致

## Phase E：文档与发布治理（中优先级）

目标：让外部认知和仓库真实状态一致。

- E1. 重写 `docs/design.md`（当前文档明显残缺）
- E2. README 功能表按“已完成/实验性”分层标注
- E3. 发布前检查脚本化（本地一键执行质量门禁）

---

## 5. 推荐执行顺序（现实可落地）

1. A1 -> A2 -> A3（先把门禁拉齐）
2. B1 -> B4 -> B3 -> B2 -> B5（先用户感知最强的字体/终端）
3. C1 -> C2 -> C3 -> C4（再做导入安全）
4. D1 -> D2 -> D3 -> D4（最后收敛 Web 协议）
5. E1 -> E2 -> E3（收口文档与发布）

---

## 6. 结论

- 旧文档低估了项目成熟度，也误判了架构方向。
- 当前项目不是“骨架阶段”，而是**功能已成型、质量门禁和安全闭环待补强**的阶段。
- 下一步不应推倒重来，而应在现有 `plugin + engine` 架构上做“质量收敛 + 深度补齐 + 安全治理”。
