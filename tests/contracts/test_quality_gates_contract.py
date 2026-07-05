# enforces: docs/specs/quality-gates.md QG-01

from scripts.release_check import build_commands


def test_full_release_check_order_is_contractual() -> None:
    command_names = [name for name, _command in build_commands("3.12", quick=False)]

    assert command_names == ["black", "ruff", "mypy", "pytest", "version", "scan"]


def test_quick_release_check_keeps_cli_smoke_order() -> None:
    command_names = [name for name, _command in build_commands("3.12", quick=True)]

    assert command_names == ["version", "scan"]
