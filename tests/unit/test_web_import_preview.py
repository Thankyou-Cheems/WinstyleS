import base64
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

import start_web_ui
from start_web_ui import ApiError, ApiHandler
from winstyles.core.engine import StyleEngine
from winstyles.domain.models import ScannedItem, ScanResult
from winstyles.domain.types import SourceType


@pytest.mark.parametrize("frozen", [False, True])
@pytest.mark.parametrize("upload", [False, True])
def test_web_preview_returns_plan_without_writes(tmp_path, monkeypatch, frozen, upload):
    monkeypatch.setattr(start_web_ui, "IS_FROZEN", frozen)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    engine = StyleEngine()
    monkeypatch.setattr(start_web_ui, "get_engine", lambda: engine)
    for scanner in engine._scanners:
        monkeypatch.setattr(scanner, "apply", lambda item: pytest.fail("preview called apply"))
    monkeypatch.setattr(
        engine, "_prepare_import_apply", lambda *a, **kw: pytest.fail("preview prepared apply")
    )
    scan = ScanResult(
        items=[
            ScannedItem(
                category="theme",
                key="theme.appsUseLightTheme",
                current_value=0,
                source_type=SourceType.REGISTRY,
                source_path=r"HKCU\Software\fixture",
            ),
            ScannedItem(
                category="fonts",
                key="installedFonts.fixture",
                current_value="Example Font",
                source_type=SourceType.FILE,
                source_path=r"C:\fixture\font.ttf",
                metadata={"readonly": True},
            ),
        ],
        os_version="fixture",
    )
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("scan.json", scan.model_dump_json())
        archive.writestr("assets/fonts/font.ttf", b"fixture")
    payload = {"dryRun": True}
    if upload:
        payload["fileBase64"] = base64.b64encode(stream.getvalue()).decode("ascii")
    else:
        package = tmp_path / "profile.zip"
        package.write_bytes(stream.getvalue())
        payload["path"] = str(package)
    handler = ApiHandler.__new__(ApiHandler)
    result = handler.dispatch_command("import_config", payload)
    assert isinstance(result, dict)
    assert len(result["dry_run_plan"]) == 2
    assert result["dry_run_plan"][1]["action"] == "skip"
    assert result["applied"] == 0
    assert not (tmp_path / "home").exists()
    assert not list(tmp_path.glob("assets/**"))


def test_web_preview_cleans_upload_after_engine_error(tmp_path, monkeypatch):
    upload = tmp_path / "upload.zip"
    upload.write_bytes(b"fixture")
    handler = ApiHandler.__new__(ApiHandler)
    monkeypatch.setattr(handler, "resolve_import_path", lambda payload: (str(upload), str(upload)))

    class Engine:
        def import_package(self, *args, **kwargs):
            return {"error_code": "unsafe_zip", "error": "unsafe fixture"}

    monkeypatch.setattr(start_web_ui, "get_engine", lambda: Engine())
    with pytest.raises(ApiError) as error:
        handler.dispatch_command("import_config", {"dryRun": True})
    assert error.value.code == "unsafe_zip"
    assert error.value.data["error_code"] == "unsafe_zip"
    assert not upload.exists()


@pytest.mark.parametrize("frozen", [False, True])
@pytest.mark.parametrize("command", ["review_import", "apply_reviewed_import"])
def test_review_commands_route_directly_and_clean_uploaded_snapshot(
    tmp_path, monkeypatch, frozen, command
):
    monkeypatch.setattr(start_web_ui, "IS_FROZEN", frozen)
    monkeypatch.setattr(start_web_ui.tempfile, "tempdir", str(tmp_path))
    calls = []

    class Engine:
        def preview_import(self, path):
            assert path.read_bytes() == b"fixture"
            calls.append(("preview", path))
            return {"dry_run_plan": [], "review_digest": "snapshot"}

        def apply_reviewed_import(self, path, selected, digest, create_restore_point):
            assert path.read_bytes() == b"fixture"
            calls.append((selected, digest, create_restore_point, path))
            return {
                "error_code": "reviewed_apply_failed",
                "error": "fixture failed",
                "journal_path": "fixture.json",
                "journal_digest": "receipt",
            }

    monkeypatch.setattr(start_web_ui, "get_engine", lambda: Engine())
    handler = ApiHandler.__new__(ApiHandler)
    payload = {
        "fileBase64": base64.b64encode(b"fixture").decode(),
        "selectedIds": ["one"],
        "reviewDigest": "snapshot",
        "skipRestore": True,
    }
    if command == "review_import":
        assert handler.dispatch_command(command, payload)["review_digest"] == "snapshot"
    else:
        with pytest.raises(ApiError) as error:
            handler.dispatch_command(command, payload)
        assert error.value.data["journal_digest"] == "receipt"
        assert calls[0][:3] == (["one"], "snapshot", False)
    assert calls and not calls[0][-1].exists()
    assert not list(tmp_path.iterdir())
