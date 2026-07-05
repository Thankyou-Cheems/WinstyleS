import json
from datetime import datetime

from winstyles import main as cli
from winstyles.domain.models import Manifest, ScanResult, SourceSystem


class _FakePackageEngine:
    def diff_packages(self, package_a, package_b) -> dict[str, object]:
        return {
            "package_a": str(package_a),
            "package_b": str(package_b),
            "items": [
                {
                    "category": "theme",
                    "key": "theme.appsUseLightTheme",
                    "change": "modified",
                    "before": 1,
                    "after": 0,
                }
            ],
        }

    def load_manifest(self, package_path) -> Manifest:
        return Manifest(
            **{"$schema": "1.0.0"},
            version="1.0.0",
            created_at=datetime(2026, 7, 5, 1, 2, 3),
            source_system=SourceSystem(
                os="Windows 11",
                version="23H2",
                build="22631",
                hostname="host",
                username="user",
            ),
        )

    def load_scan_result(self, package_path) -> ScanResult:
        return ScanResult(
            scan_id="20260705010203",
            scan_time=datetime(2026, 7, 5, 1, 2, 3),
            os_version="Windows 11 23H2",
            items=[],
            summary={"theme": 1},
        )


def test_diff_json_stdout_is_machine_readable(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(cli, "StyleEngine", _FakePackageEngine)

    cli.diff(tmp_path / "a.zip", tmp_path / "b.zip", format="json", output=None, show_all=True)

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["items"][0]["key"] == "theme.appsUseLightTheme"
    assert "对比配置包" not in output


def test_inspect_json_stdout_is_machine_readable(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(cli, "StyleEngine", _FakePackageEngine)

    cli.inspect(tmp_path / "style.zip", format="json", output=None)

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["schema_version"] == "1.0.0"
    assert payload["scan_summary"] == {"theme": 1}
    assert "检视配置包" not in output


def test_diff_table_stdout_keeps_human_banner(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setattr(cli, "StyleEngine", _FakePackageEngine)

    cli.diff(tmp_path / "a.zip", tmp_path / "b.zip", format="table", output=None, show_all=True)

    assert "对比配置包" in capsys.readouterr().out
