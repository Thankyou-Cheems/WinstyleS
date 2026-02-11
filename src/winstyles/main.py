"""
WinstyleS CLI 主入口 - 使用 Typer 构建命令行界面
"""

import importlib
import json
import os
from pathlib import Path
from typing import Protocol, cast

import typer
from rich.console import Console
from rich.table import Table

from winstyles import __version__
from winstyles.core.engine import StyleEngine
from winstyles.domain.models import Manifest, ScannedItem, ScanResult

# 创建 Typer 应用
app = typer.Typer(
    name="winstyles",
    help="WinstyleS (Windows Style Sync) - Windows 个性化设置同步工具",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


class _YamlModule(Protocol):
    def safe_dump(self, data: object, **kwargs: object) -> str: ...


def _load_yaml_module() -> _YamlModule:
    try:
        module = importlib.import_module("yaml")
    except ModuleNotFoundError:
        console.print("[red]YAML 输出需要安装 PyYAML: pip install pyyaml[/red]")
        raise typer.Exit(code=1)
    return cast(_YamlModule, module)


def version_callback(value: bool) -> None:
    """显示版本信息"""
    if value:
        console.print(
            f"[bold blue]WinstyleS (Windows Style Sync)[/bold blue] version "
            f"[green]{__version__}[/green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    WinstyleS (Windows Style Sync) - Windows 个性化设置同步工具

    自动扫描、导出、同步你的 Windows 美化配置。
    """
    pass


@app.command()
def scan(
    category: list[str] | None = typer.Option(
        None,
        "--category",
        "-c",
        help="指定扫描类别 (可多选): fonts, terminal, theme, vscode, browser, all",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="输出扫描结果到文件 (JSON格式)",
    ),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="输出格式: table, json, yaml",
    ),
    modified_only: bool = typer.Option(
        False,
        "--modified-only",
        help="仅显示修改过的配置项",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="显示详细信息",
    ),
) -> None:
    """
    🔍 扫描当前系统的个性化配置

    与 Windows 默认值对比后输出报告。
    """
    if format != "json":
        console.print("[bold blue]开始扫描系统配置...[/bold blue]")

    normalized_categories: list[str] | None = None
    if category:
        normalized = [c.strip().lower() for c in category if c.strip()]
        if "all" not in normalized:
            normalized_categories = normalized

    engine = StyleEngine()
    result = engine.scan_all(categories=normalized_categories)

    items = result.items
    if modified_only:
        items = [item for item in items if item.change_type.value == "modified"]

    if format not in {"table", "json", "yaml"}:
        console.print(f"[red]不支持的输出格式: {format}[/red]")
        raise typer.Exit(code=1)

    if verbose:
        _print_scan_summary(result, items)

    if output:
        _write_scan_output(result, items, output, format)
        console.print(f"[green]扫描结果已写入: {output}[/green]")
        return

    if format == "json" and not verbose:
        _print_scan_output(result, items, format)
        return

    _print_scan_output(result, items, format)


@app.command()
def export(
    output_path: Path = typer.Argument(
        ...,
        help="输出路径 (目录或.zip文件)",
    ),
    category: list[str] | None = typer.Option(
        None,
        "--category",
        "-c",
        help="指定导出类别 (可多选)",
    ),
    include_defaults: bool = typer.Option(
        False,
        "--include-defaults",
        help="是否包含未修改的默认配置",
    ),
    include_font_files: bool = typer.Option(
        False,
        "--include-font-files",
        help="是否包含字体文件资产（.ttf/.otf/.ttc 等）",
    ),
) -> None:
    """
    📤 导出配置包

    将扫描到的配置和资源文件打包导出。
    """
    console.print(f"[bold blue]导出配置到: {output_path}[/bold blue]")

    normalized_categories: list[str] | None = None
    if category:
        normalized = [c.strip().lower() for c in category if c.strip()]
        if "all" not in normalized:
            normalized_categories = normalized

    engine = StyleEngine()
    result = engine.scan_all(categories=normalized_categories)
    if not include_defaults:
        result = _filter_scan_result(result, keep_defaults=False)

    manifest = engine.export_package(
        result,
        output_path,
        include_assets=True,
        include_font_files=include_font_files,
    )
    console.print(f"[green]导出完成: {output_path}[/green]")
    console.print(f"[green]清单: {manifest.schema_version}[/green]")


@app.command("import")
def import_config(
    input_path: Path = typer.Argument(
        ...,
        help="配置包路径 (.zip文件或目录)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="仅预览变更，不实际应用",
    ),
    skip_restore_point: bool = typer.Option(
        False,
        "--skip-restore-point",
        help="跳过创建系统还原点",
    ),
) -> None:
    """
    📥 导入配置包

    从配置包还原个性化设置。
    """
    console.print(f"[bold blue]导入配置从: {input_path}[/bold blue]")

    engine = StyleEngine()
    summary = engine.import_package(
        input_path,
        dry_run=dry_run,
        create_restore_point=not skip_restore_point,
    )

    table = Table(title="Import Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    for key in ["total", "applied", "failed", "skipped"]:
        table.add_row(key, str(summary.get(key, 0)))
    console.print(table)

    if dry_run:
        console.print("[yellow]Dry-run: 未应用任何更改[/yellow]")


@app.command()
def diff(
    package1: Path = typer.Argument(..., help="第一个配置包"),
    package2: Path = typer.Argument(..., help="第二个配置包"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="输出格式: table, json, yaml",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="输出结果到文件",
    ),
    show_all: bool = typer.Option(
        False,
        "--all",
        help="显示未变化项",
    ),
) -> None:
    """
    🔄 对比两个配置包的差异
    """
    console.print(f"[bold blue]对比配置包: {package1} vs {package2}[/bold blue]")

    if format not in {"table", "json", "yaml"}:
        console.print(f"[red]不支持的输出格式: {format}[/red]")
        raise typer.Exit(code=1)

    engine = StyleEngine()
    diff_result = engine.diff_packages(package1, package2)

    if "error" in diff_result:
        console.print(f"[red]{diff_result['error']}[/red]")
        raise typer.Exit(code=1)

    items = diff_result.get("items", [])
    if not show_all:
        items = [item for item in items if item.get("change") != "unchanged"]
        diff_result = {**diff_result, "items": items}

    if output:
        _write_payload(output, diff_result, format)
        console.print(f"[green]结果已写入: {output}[/green]")
        return

    _print_diff_output(diff_result, format)


@app.command()
def inspect(
    package_path: Path = typer.Argument(..., help="配置包路径"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="输出格式: table, json, yaml",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="输出结果到文件",
    ),
) -> None:
    """
    🔎 检视配置包内容
    """
    console.print(f"[bold blue]检视配置包: {package_path}[/bold blue]")

    if format not in {"table", "json", "yaml"}:
        console.print(f"[red]不支持的输出格式: {format}[/red]")
        raise typer.Exit(code=1)

    engine = StyleEngine()
    manifest = engine.load_manifest(package_path)
    scan = engine.load_scan_result(package_path)
    if manifest is None:
        console.print("[red]manifest.json not found[/red]")
        raise typer.Exit(code=1)

    payload = _inspect_payload(manifest, scan)
    if output:
        _write_payload(output, payload, format)
        console.print(f"[green]结果已写入: {output}[/green]")
        return

    _print_inspect_output(payload, format)


@app.command()
def restore(
    use_system_restore: bool = typer.Option(
        False,
        "--system-restore",
        "-s",
        help="打开系统还原界面",
    ),
) -> None:
    """
    ⏪ 回滚到之前的状态

    使用 WinstyleS 创建的备份或系统还原点进行恢复。
    """
    console.print("[bold blue]准备回滚...[/bold blue]")

    if use_system_restore:
        console.print("[yellow]正在打开系统还原界面...[/yellow]")
        import subprocess

        try:
            # 打开系统还原界面
            subprocess.Popen(
                ["rstrui.exe"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            console.print("[green]系统还原界面已打开[/green]")
            console.print("[dim]请在系统还原界面中选择由 WinstyleS 创建的还原点进行恢复[/dim]")
        except Exception as e:
            console.print(f"[red]无法打开系统还原: {e}[/red]")
            raise typer.Exit(code=1)
        return

    # 列出可用的备份包
    backup_dir = Path.home() / ".winstyles" / "backups"
    if not backup_dir.exists():
        console.print("[yellow]没有找到备份文件[/yellow]")
        console.print("[dim]使用 --system-restore 参数打开系统还原界面[/dim]")
        return

    backups = sorted(backup_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not backups:
        console.print("[yellow]没有找到备份文件[/yellow]")
        console.print("[dim]使用 --system-restore 参数打开系统还原界面[/dim]")
        return

    table = Table(title="可用备份")
    table.add_column("#", style="cyan")
    table.add_column("文件名", style="white")
    table.add_column("创建时间", style="green")
    table.add_column("大小", style="yellow")

    for i, backup in enumerate(backups[:10], 1):
        stat = backup.stat()
        size_kb = stat.st_size / 1024
        from datetime import datetime

        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(str(i), backup.name, mtime, f"{size_kb:.1f} KB")

    console.print(table)
    console.print("\n[dim]使用 winstyles import <备份路径> 来恢复配置[/dim]")
    console.print("[dim]使用 --system-restore 参数打开系统还原界面[/dim]")


@app.command()
def report(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径 (.md 或 .html)",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="输出格式: markdown, html",
    ),
    categories: list[str] | None = typer.Option(
        None,
        "--category",
        "-c",
        help="要扫描的类别，可多次指定",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open",
        help="生成后在浏览器中打开",
    ),
    check_updates: bool = typer.Option(
        True,
        "--check-updates/--no-check-updates",
        help="是否检查字体更新（禁用可避免联网并提升速度）",
    ),
) -> None:
    """
    📊 生成扫描报告

    分析系统配置并生成人类可读的报告，包括:
    - 用户自定义配置识别
    - 系统版本差异区分
    - 开源字体来源信息
    """
    from winstyles.core.report import ReportGenerator

    is_web_request = os.environ.get("WINSTYLES_WEB_MODE") == "1"
    if not is_web_request:
        console.print("[bold blue]正在扫描并生成报告...[/bold blue]")

    engine = StyleEngine()
    scan_result = engine.scan_all(categories)

    generator = ReportGenerator(scan_result, check_updates=check_updates)

    if format.lower() == "html":
        content = generator.generate_html(embedded=is_web_request)
        default_ext = ".html"
    else:
        content = generator.generate_markdown()
        default_ext = ".md"

    if output:
        output.write_text(content, encoding="utf-8")
        if not is_web_request:
            console.print(f"[green]报告已保存至: {output}[/green]")

        if open_browser:
            import webbrowser

            webbrowser.open(str(output.resolve()))
    else:
        if not open_browser:
            if is_web_request:
                # Web mode expects a JSON string payload.
                print(json.dumps(content, ensure_ascii=False))
                return
            # In CLI mode, avoid non-UTF8 console encoding issues by escaping non-ASCII.
            print(json.dumps(content, ensure_ascii=True))
            return

        # 默认保存到临时文件并显示
        if open_browser:
            import tempfile
            import webbrowser

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=default_ext,
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(content)
                temp_path = f.name

            console.print(f"[green]报告临时文件: {temp_path}[/green]")
            webbrowser.open(temp_path)
            console.print("[green]报告已在浏览器中打开[/green]")
        else:
            # 直接打印 Markdown
            from rich.markdown import Markdown

            console.print(Markdown(content))


@app.command()
def gui() -> None:
    """
    🖥️ 启动 Web 图形用户界面

    启动本地 Web 服务器并在浏览器中打开操作界面。
    """
    from winstyles.gui.app import run_gui

    console.print("[bold blue]正在启动图形界面...[/bold blue]")
    run_gui()


def _print_scan_output(result: ScanResult, items: list[ScannedItem], fmt: str) -> None:
    if fmt == "json":
        import json

        # Direct print for pipes
        print(json.dumps(_scan_result_payload(result, items), ensure_ascii=False))
        return
    if fmt == "yaml":
        _print_yaml(_scan_result_payload(result, items))
        return

    table = Table(title="WinstyleS Scan Result")
    table.add_column("Category", style="cyan")
    table.add_column("Key", style="white")
    table.add_column("Current", style="green")
    table.add_column("Default", style="yellow")
    table.add_column("Change", style="magenta")
    table.add_column("Source", style="blue")

    for item in items:
        table.add_row(
            item.category,
            item.key,
            _shorten_value(item.current_value),
            _shorten_value(item.default_value),
            item.change_type.value,
            item.source_path,
        )

    console.print(table)


def _write_scan_output(
    result: ScanResult,
    items: list[ScannedItem],
    output_path: Path,
    fmt: str,
) -> None:
    payload = _scan_result_payload(result, items)
    if fmt == "yaml":
        _write_yaml(output_path, payload)
        return
    if fmt == "table":
        output_path.write_text(_scan_table_text(items), encoding="utf-8")
        return

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _scan_result_payload(result: ScanResult, items: list[ScannedItem]) -> dict[str, object]:
    return {
        "scan_id": result.scan_id,
        "scan_time": result.scan_time.isoformat(),
        "os_version": result.os_version,
        "summary": result.summary,
        "items": [item.model_dump(mode="json") for item in items],
    }


def _scan_table_text(items: list[ScannedItem]) -> str:
    lines = ["Category\tKey\tCurrent\tDefault\tChange\tSource"]
    for item in items:
        lines.append(
            "\t".join(
                [
                    item.category,
                    item.key,
                    _shorten_value(item.current_value),
                    _shorten_value(item.default_value),
                    item.change_type.value,
                    item.source_path,
                ]
            )
        )
    return "\n".join(lines)


def _shorten_value(value: object, max_len: int = 80) -> str:
    if value is None:
        return ""
    text = str(value)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _print_yaml(payload: dict[str, object]) -> None:
    yaml = _load_yaml_module()
    console.print(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))


def _write_yaml(output_path: Path, payload: dict[str, object]) -> None:
    yaml = _load_yaml_module()
    output_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def _print_scan_summary(result: ScanResult, items: list[ScannedItem]) -> None:
    console.print(f"[bold]Scan ID:[/bold] {result.scan_id} | [bold]Time:[/bold] {result.scan_time}")
    if result.os_version:
        console.print(f"[bold]OS:[/bold] {result.os_version}")

    if result.summary:
        table = Table(title="Category Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        for category, count in sorted(result.summary.items()):
            table.add_row(category, str(count))
        console.print(table)

    change_counts: dict[str, int] = {}
    for item in items:
        change_counts[item.change_type.value] = change_counts.get(item.change_type.value, 0) + 1

    if change_counts:
        table = Table(title="Change Summary")
        table.add_column("Change", style="magenta")
        table.add_column("Count", style="green")
        for change, count in sorted(change_counts.items()):
            table.add_row(change, str(count))
        console.print(table)


def _filter_scan_result(result: ScanResult, keep_defaults: bool) -> ScanResult:
    if keep_defaults:
        return result
    filtered_items = [item for item in result.items if item.change_type.value == "modified"]
    summary: dict[str, int] = {}
    for item in filtered_items:
        summary[item.category] = summary.get(item.category, 0) + 1
    return ScanResult(
        scan_id=result.scan_id,
        scan_time=result.scan_time,
        os_version=result.os_version,
        items=filtered_items,
        summary=summary,
        duration_ms=result.duration_ms,
    )


def _print_diff_output(payload: dict[str, object], fmt: str) -> None:
    if fmt == "json":
        import json

        print(json.dumps(payload, ensure_ascii=False))
        return
    if fmt == "yaml":
        _print_yaml(payload)
        return

    table = Table(title="Package Diff")
    table.add_column("Category", style="cyan")
    table.add_column("Key", style="white")
    table.add_column("Change", style="magenta")
    table.add_column("Before", style="yellow")
    table.add_column("After", style="green")

    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        table.add_row(
            str(item.get("category", "")),
            str(item.get("key", "")),
            str(item.get("change", "")),
            _shorten_value(item.get("before")),
            _shorten_value(item.get("after")),
        )

    console.print(table)


def _print_inspect_output(payload: dict[str, object], fmt: str) -> None:
    if fmt == "json":
        import json

        print(json.dumps(payload, ensure_ascii=False))
        return
    if fmt == "yaml":
        _print_yaml(payload)
        return

    meta = Table(title="Package Info")
    meta.add_column("Field", style="cyan")
    meta.add_column("Value", style="green")
    for key in [
        "schema_version",
        "version",
        "created_at",
        "created_by",
        "source_os",
        "source_version",
        "source_build",
        "source_hostname",
        "source_username",
    ]:
        if key in payload:
            meta.add_row(key, str(payload[key]))
    console.print(meta)

    options = payload.get("export_options", {})
    if isinstance(options, dict) and options:
        table = Table(title="Export Options")
        table.add_column("Option", style="cyan")
        table.add_column("Enabled", style="green")
        for key, value in options.items():
            table.add_row(str(key), str(value))
        console.print(table)

    summary = payload.get("scan_summary", {})
    if isinstance(summary, dict) and summary:
        table = Table(title="Scan Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        for key, value in sorted(summary.items()):
            table.add_row(str(key), str(value))
        console.print(table)


def _inspect_payload(manifest: "Manifest", scan: ScanResult | None) -> dict[str, object]:
    return {
        "schema_version": manifest.schema_version,
        "version": manifest.version,
        "created_at": manifest.created_at.isoformat(),
        "created_by": manifest.created_by,
        "source_os": manifest.source_system.os,
        "source_version": manifest.source_system.version,
        "source_build": manifest.source_system.build,
        "source_hostname": manifest.source_system.hostname,
        "source_username": manifest.source_system.username,
        "export_options": manifest.export_options.model_dump(mode="json"),
        "scan_summary": scan.summary if scan else {},
        "scan_count": len(scan.items) if scan else 0,
    }


def _write_payload(output_path: Path, payload: dict[str, object], fmt: str) -> None:
    if fmt == "yaml":
        _write_yaml(output_path, payload)
        return
    if fmt == "table":
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    app()
