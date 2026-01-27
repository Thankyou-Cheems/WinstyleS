"""
WinstyleS CLI 主入口 - 使用 Typer 构建命令行界面
"""

from pathlib import Path

import typer
from rich.console import Console

from winstyles import __version__

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
    console.print("[bold blue]🔍 开始扫描系统配置...[/bold blue]")
    # TODO: 实现扫描逻辑
    console.print("[yellow]⚠️ 扫描功能正在开发中...[/yellow]")


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
    console.print(f"[bold blue]📤 导出配置到: {output_path}[/bold blue]")
    # TODO: 实现导出逻辑
    console.print("[yellow]⚠️ 导出功能正在开发中...[/yellow]")


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
    console.print(f"[bold blue]📥 导入配置从: {input_path}[/bold blue]")
    # TODO: 实现导入逻辑
    console.print("[yellow]⚠️ 导入功能正在开发中...[/yellow]")


@app.command()
def diff(
    package1: Path = typer.Argument(..., help="第一个配置包"),
    package2: Path = typer.Argument(..., help="第二个配置包"),
) -> None:
    """
    🔄 对比两个配置包的差异
    """
    console.print(f"[bold blue]🔄 对比配置包: {package1} vs {package2}[/bold blue]")
    # TODO: 实现对比逻辑
    console.print("[yellow]⚠️ 对比功能正在开发中...[/yellow]")


@app.command()
def inspect(
    package_path: Path = typer.Argument(..., help="配置包路径"),
) -> None:
    """
    🔎 检视配置包内容
    """
    console.print(f"[bold blue]🔎 检视配置包: {package_path}[/bold blue]")
    # TODO: 实现检视逻辑
    console.print("[yellow]⚠️ 检视功能正在开发中...[/yellow]")


@app.command()
def restore() -> None:
    """
    ⏪ 回滚到之前的状态

    使用 WinstyleS 创建的备份进行恢复。
    """
    console.print("[bold blue]⏪ 准备回滚...[/bold blue]")
    # TODO: 实现回滚逻辑
    console.print("[yellow]⚠️ 回滚功能正在开发中...[/yellow]")


if __name__ == "__main__":
    app()
