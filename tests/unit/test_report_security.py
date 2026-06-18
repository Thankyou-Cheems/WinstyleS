from datetime import datetime

from winstyles.core.report import ReportGenerator
from winstyles.domain.models import OpenSourceFontInfo, ScannedItem, ScanResult
from winstyles.domain.types import ChangeType, SourceType


def _scan_result(item: ScannedItem) -> ScanResult:
    return ScanResult(
        scan_id="20260618000100",
        scan_time=datetime(2026, 6, 18, 0, 1),
        os_version="Windows 11 23H2",
        items=[item],
        summary={item.category: 1},
    )


def test_generate_html_escapes_scanned_values() -> None:
    item = ScannedItem(
        category="terminal<script>",
        key='windowsTerminal.theme"><img src=x onerror=alert(1)>',
        current_value='<script>alert("x")</script>',
        default_value="<img src=x onerror=alert(1)>",
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path="settings.json",
        metadata={"note": "<b>metadata</b>"},
    )

    content = ReportGenerator(_scan_result(item), check_updates=False).generate_html()

    assert '<script>alert("x")</script>' not in content
    assert "<img src=x onerror=alert(1)>" not in content
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in content
    assert "&lt;img src=x onerror=alert(1)&gt;" in content


def test_generate_html_filters_unsafe_font_links_and_escapes_font_metadata() -> None:
    item = ScannedItem(
        category="terminal",
        key="windowsTerminal.defaults.font.face",
        current_value="Unsafe Mono",
        default_value="Consolas",
        change_type=ChangeType.MODIFIED,
        source_type=SourceType.FILE,
        source_path="settings.json",
    )
    generator = ReportGenerator(_scan_result(item), check_updates=False)
    generator._font_db = [
        OpenSourceFontInfo(
            name="Unsafe Mono",
            patterns=["Unsafe Mono"],
            homepage="javascript:alert(1)",
            download="https://example.com/font?a=1&b=2",
            license="MIT",
            description="safe <b>desc</b>",
        )
    ]

    content = generator.generate_html()

    assert "javascript:" not in content
    assert '<a href="https://example.com/font?a=1&amp;b=2">下载</a>' in content
    assert "safe &lt;b&gt;desc&lt;/b&gt;" in content
