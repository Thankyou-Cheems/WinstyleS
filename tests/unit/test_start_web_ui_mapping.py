from datetime import datetime

import pytest

from start_web_ui import ApiError, ApiHandler, _resolve_src_dir
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


def test_resolve_src_dir_falls_back_for_installed_layout(tmp_path) -> None:
    assert _resolve_src_dir(tmp_path) == tmp_path

    source_dir = tmp_path / "src"
    source_dir.mkdir()

    assert _resolve_src_dir(tmp_path) == source_dir


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


def test_filter_scan_result_keeps_only_modified_items() -> None:
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
            ScannedItem(
                category="fonts",
                key="c",
                current_value="z",
                default_value=None,
                change_type=ChangeType.ADDED,
                source_type=SourceType.REGISTRY,
                source_path="HKLM\\c",
            ),
        ],
        summary={"fonts": 2, "terminal": 1},
    )

    filtered = handler._filter_scan_result(scan_result, keep_defaults=False)
    assert len(filtered.items) == 1
    assert filtered.items[0].key == "b"
    assert filtered.summary == {"terminal": 1}


def test_status_payload_has_ok_status_and_mode() -> None:
    handler = ApiHandler.__new__(ApiHandler)

    status = handler.dispatch_command("status", {})

    assert status["status"] == "ok"
    assert status["mode"] in {"development", "frozen"}
    assert "frontend_dir" in status
    assert "src_dir" in status


def test_unknown_command_raises_structured_api_error() -> None:
    handler = ApiHandler.__new__(ApiHandler)

    with pytest.raises(ApiError) as exc_info:
        handler.dispatch_command("missing_command", {})

    assert exc_info.value.code == "unknown_command"
    assert exc_info.value.status_code == 404


def test_api_error_payload_shape() -> None:
    handler = ApiHandler.__new__(ApiHandler)

    payload = handler._api_error("bad_request", "Bad request", data={"field": "path"})

    assert payload == {
        "ok": False,
        "data": {"field": "path"},
        "error": "Bad request",
        "code": "bad_request",
        "message": "Bad request",
    }


def test_run_subprocess_failure_raises_structured_api_error(monkeypatch) -> None:
    handler = ApiHandler.__new__(ApiHandler)

    class _Result:
        returncode = 2
        stdout = "stdout details"
        stderr = "stderr details"

    monkeypatch.setattr("start_web_ui.subprocess.run", lambda *args, **kwargs: _Result())

    with pytest.raises(ApiError) as exc_info:
        handler.run_subprocess(["python", "-m", "winstyles", "scan"])

    assert exc_info.value.code == "command_failed"
    assert exc_info.value.status_code == 500
    assert exc_info.value.message == "stderr details"
    assert exc_info.value.data == {
        "returncode": 2,
        "stdout": "stdout details",
        "stderr": "stderr details",
    }
