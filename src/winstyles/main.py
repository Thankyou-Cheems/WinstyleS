"""
WinstyleS CLI 主入口 - 使用 Typer 构建命令行界面
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from winstyles import __version__
from winstyles.core.engine import StyleEngine
from winstyles.domain.models import ScannedItem, ScanResult

# 创建 Typer 应用
app = typer.Typer(
    name="winstyles",
    help="WinstyleS (Windows Style Sync) - Windows 个性化设置同步工具",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


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
        items = [item for item in items if item.change_type.value != "default"]

    if format not in {"table", "json", "yaml"}:
        console.print(f"[red]不支持的输出格式: {format}[/red]")
        raise typer.Exit(code=1)

    if verbose:
        _print_scan_summary(result, items)

    if output:
        _write_scan_output(result, items, output, format)
        console.print(f"[green]扫描结果已写入: {output}[/green]")
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

    manifest = engine.export_package(result, output_path, include_assets=True)
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
) -> None:
    """
    🔄 对比两个配置包的差异
    """
    console.print(f"[bold blue]对比配置包: {package1} vs {package2}[/bold blue]")
    # TODO: 实现对比逻辑
    console.print("[yellow]对比功能正在开发中...[/yellow]")


@app.command()
def inspect(
    package_path: Path = typer.Argument(..., help="配置包路径"),
) -> None:
    """
    🔎 检视配置包内容
    """
    console.print(f"[bold blue]检视配置包: {package_path}[/bold blue]")
    # TODO: 实现检视逻辑
    console.print("[yellow]检视功能正在开发中...[/yellow]")


@app.command()
def restore() -> None:
    """
    ⏪ 回滚到之前的状态

    使用 WinstyleS 创建的备份进行恢复。
    """
    console.print("[bold blue]准备回滚...[/bold blue]")
    # TODO: 实现回滚逻辑
    console.print("[yellow]回滚功能正在开发中...[/yellow]")


def _print_scan_output(result: ScanResult, items: list[ScannedItem], fmt: str) -> None:
    if fmt == "json":
        console.print_json(data=_scan_result_payload(result, items))
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
    try:
        import yaml
    except ModuleNotFoundError:
        console.print("[red]YAML 输出需要安装 PyYAML: pip install pyyaml[/red]")
        raise typer.Exit(code=1)
    console.print(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))


def _write_yaml(output_path: Path, payload: dict[str, object]) -> None:
    try:
        import yaml
    except ModuleNotFoundError:
        console.print("[red]YAML 输出需要安装 PyYAML: pip install pyyaml[/red]")
        raise typer.Exit(code=1)
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
    filtered_items = [item for item in result.items if item.change_type.value != "default"]
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


if __name__ == "__main__":
    app()
