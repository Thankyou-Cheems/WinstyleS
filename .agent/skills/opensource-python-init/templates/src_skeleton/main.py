"""
CLI 主入口 - 使用 Typer 构建命令行界面

如果不需要 CLI，可以替换为其他入口逻辑。
"""

import typer
from typing import Optional

from {{PACKAGE_NAME}} import __version__

app = typer.Typer(
    name="{{COMMAND_NAME}}",
    help="{{PROJECT_DESCRIPTION}}",
    add_completion=True,
)


def version_callback(value: bool) -> None:
    if value:
        print(f"{{COMMAND_NAME}} version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    {{PROJECT_DESCRIPTION}}
    """
    pass


@app.command()
def hello(name: str = "World") -> None:
    """示例命令"""
    print(f"Hello, {name}!")


if __name__ == "__main__":
    app()
