from datetime import datetime

from winstyles import main as cli
from winstyles.domain.models import ScanResult


class _FakeEngine:
    def scan_all(self, categories: list[str] | None = None) -> ScanResult:
        return ScanResult(
            scan_id="20260618000200",
            scan_time=datetime(2026, 6, 18, 0, 2),
            os_version="Windows 11 23H2",
            items=[],
            summary={},
        )


def test_report_default_stdout_is_plain_markdown(monkeypatch, capsys) -> None:
    monkeypatch.delenv("WINSTYLES_WEB_MODE", raising=False)
    monkeypatch.setattr(cli, "StyleEngine", _FakeEngine)

    cli.report(
        output=None,
        format="markdown",
        categories=None,
        open_browser=False,
        check_updates=False,
    )

    output = capsys.readouterr().out
    assert "# WinstyleS 扫描报告" in output
    assert '"# WinstyleS' not in output
    assert "\\n" not in output
