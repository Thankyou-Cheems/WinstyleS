# AGENTS.md

本文件约定如何同步维护项目文档与元信息。适用于所有贡献者。

## 同步维护规则

- **版本号**: 修改 `pyproject.toml` 的 `version` 时，必须同步更新 `CHANGELOG.md`。
- **新功能/行为变更**: 必须更新 `README.md`，必要时补充 `docs/`（如设计/用法）。
- **命令/CLI 变更**: 更新 `README.md` 的用法示例与 `docs/design.md`（若涉及）。
- **依赖变更**: 更新 `pyproject.toml` 中的 `dependencies`/`optional-dependencies`，并在 `CHANGELOG.md` 记录。
- **仓库信息变更**: 更新 `pyproject.toml` 的 `project.urls` 与 `README.md` 徽章/链接。

## 发布前检查清单（Release Checklist）

- `CHANGELOG.md` 已记录本次变更并标明版本
- `pyproject.toml` 版本与变更日志一致
- `README.md` 与 `docs/` 的用法/截图/示例已同步
- CI 全绿（ruff/black/mypy/pytest/coverage）
- 关键命令本地验证通过（至少 `winstyles --version` 与 `winstyles scan`）

## CI 失败处理原则

- 先看 **第一个失败步骤**，按顺序处理：`black` -> `ruff` -> `mypy` -> `pytest`
- 若出现“0 tests collected”，必须补最低限度的测试覆盖
- Windows 下输出编码报错时，避免 emoji 或设置控制台为 UTF-8

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
Use 'bd' for task tracking
