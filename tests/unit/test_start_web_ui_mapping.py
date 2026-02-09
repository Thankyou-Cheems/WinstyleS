from datetime import datetime

from start_web_ui import ApiHandler
from winstyles.domain.models import ScannedItem, ScanResult
from winstyles.domain.types import ChangeType, SourceType


def test_map_scan_args_uses_json_for_table_and_supports_modified_only() -> None:
    handler = ApiHandler.__new__(ApiHandler)
    args = handler.map_scan_args(
        {
            "categories": ["fonts", "terminal"],
            "format": "table",
            "modifiedOnly": True,
        }
    )
    assert args == ["-c", "fonts", "-c", "terminal", "-f", "json", "--modified-only"]


def test_map_export_args_supports_include_font_files() -> None:
    handler = ApiHandler.__new__(ApiHandler)
    args = handler.map_export_args(
        {
            "path": r"D:\tmp\style.zip",
            "categories": "fonts,terminal",
            "includeDefaults": True,
            "includeFontFiles": True,
        }
    )
    assert args == [
        r"D:\tmp\style.zip",
        "-c",
        "fonts",
        "-c",
        "terminal",
        "--include-defaults",
        "--include-font-files",
    ]


def test_filter_scan_result_keeps_only_non_default_items() -> None:
    handler = ApiHandler.__new__(ApiHandler)
    scan_result = ScanResult(
        scan_id="20260209190000",
        scan_time=datetime.now(),
        os_version="Windows 11 23H2",
        items=[
            ScannedItem(
                category="fonts",
                key="a",
                current_value="x",
                default_value="x",
                change_type=ChangeType.DEFAULT,
                source_type=SourceType.REGISTRY,
                source_path="HKLM\\a",
            ),
            ScannedItem(
                category="terminal",
                key="b",
                current_value="x",
                default_value="y",
                change_type=ChangeType.MODIFIED,
                source_type=SourceType.FILE,
                source_path=r"C:\b",
            ),
        ],
        summary={"fonts": 1, "terminal": 1},
    )

    filtered = handler._filter_scan_result(scan_result, keep_defaults=False)
    assert len(filtered.items) == 1
    assert filtered.items[0].key == "b"
    assert filtered.summary == {"terminal": 1}
