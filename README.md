# WinstyleS — Windows Style Sync

本地管理你的 Windows 个性化配置：扫描、查看差异、导出可移植配置包，
在另一台设备上先审阅计划，再导入支持的设置。

## 当前可用

| 类别 | 扫描与迁移范围 |
|---|---|
| 字体 | 替换规则、FontLink、已安装字体清单、ClearType；字体资源可选导出 |
| Windows 外观 | 深浅色、强调色、DWM、桌面壁纸和鼠标指针；部分锁屏信息只读 |
| 终端与 Shell | Windows Terminal、PowerShell Profile、Oh My Posh；可写范围依插件 |
| VS Code | 主要字体/主题用户设置；不是完整账号或工作区迁移 |

CLI 提供扫描、报告、导出、导入、包对比和包检视。Web GUI 提供本地操作界面。
Web 导入审阅对比本机当前值和包内目标值，显示本机写入路径、风险、权限和跳过原因。
勾选需要修改的设置，再点击“导入选中项”；引擎只处理这些项目。类别、风险与搜索
筛选只改变展示，不会改变已选范围。包或本机配置变化后必须重新预览。

此流程限于有旧值可恢复的设置；字体、图片、脚本、资源路径及新建设置会跳过。
导入前保存选中项的恢复记录；失败时尝试撤回已触及项，日志中的回执可供再次恢复。
同一次浏览器会话可点击“撤回上次导入”；若配置已被其他程序修改，恢复会拒绝覆盖。
PowerToys、独立漂移巡检和跨会话恢复管理是后续方向。
见[现代化方向与选择依据](docs/modernization.md)。

## 从源码运行

```powershell
git clone https://github.com/Thankyou-Cheems/WinstyleS.git
cd WinstyleS
python -m venv .venv-windows
.venv-windows\Scripts\python -m pip install -e .
.venv-windows\Scripts\python -m winstyles gui
```

Web GUI 在本机 `127.0.0.1` 运行。首页发放进程内临时会话 Cookie，API 要求该
Cookie、本机 Host 和 JSON 请求；浏览器 Origin 必须同源。不要将它暴露为远程管理服务。

```powershell
# 在已激活的环境内
winstyles scan -c fonts -c terminal -f json
winstyles report --no-check-updates
winstyles export ./my-style.zip --include-font-files
winstyles inspect ./my-style.zip -f json
winstyles diff ./old.zip ./new.zip -f json
winstyles import ./my-style.zip --dry-run
```

预览不会修改系统设置、复制资源或生成导入日志。浏览器选择 zip 时仅使用
临时上传文件，处理后删除。确认适合目标设备后，可手动执行：

```powershell
winstyles import ./my-style.zip
```

上述 CLI 导入仍保留整包及资源迁移行为；逐项选择与恢复回执由 Web 新流程提供。
实际导入依赖 Windows 权限，会检查管理员权限、还原点和导入前备份，并记录
审计日志。它可能改写注册表、用户配置和资源；失败后的恢复需要审阅，
不承诺所有插件写入都能原子回滚。解析失败时保留原 Terminal/VS Code 文件。

## 开发与边界

- [开发与验证](CONTRIBUTING.md)：独立环境和检查命令。
- [架构](docs/ARCHITECTURE.md)：现有插件扩展点。
- [行为与安全边界](docs/behavior.md)：包、导入、API 兼容性与对应回归测试。
- [现代化决策](docs/modernization.md)：本阶段交付、备选集成与文档清理原因。
- [历史变更](CHANGELOG.md)和[已知坑](docs/PITFALLS.md)。

项目不自动创建云同步账号、迁移凭据或安装应用/扩展。系统级 apply 需要独立
人工验证，CI 通过只能证明已测试的代码路径。MIT 许可证见 [LICENSE](LICENSE)。
