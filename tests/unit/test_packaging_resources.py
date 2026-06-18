import tomllib
from pathlib import Path

from winstyles.core.engine import _winstyles_resource_path as engine_resource_path
from winstyles.core.report import _winstyles_resource_path as report_resource_path

ROOT_DIR = Path(__file__).resolve().parents[2]


def test_wheel_declares_runtime_resources() -> None:
    config = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    project = config["project"]
    force_include = config["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]

    assert "PyYAML>=6.0.1" in project["dependencies"]
    assert force_include["data/defaults"] == "winstyles/data/defaults"
    assert force_include["data/opensource_fonts.json"] == "winstyles/data/opensource_fonts.json"
    assert force_include["frontend"] == "frontend"
    assert force_include["start_web_ui.py"] == "start_web_ui.py"


def test_pyinstaller_spec_declares_runtime_resources() -> None:
    spec = (ROOT_DIR / "winstyles.spec").read_text(encoding="utf-8")

    assert "os.path.join(project_root, 'data', 'defaults')" in spec
    assert "os.path.join('winstyles', 'data', 'defaults')" in spec
    assert "os.path.join(project_root, 'data', 'opensource_fonts.json')" in spec
    assert "os.path.join(project_root, 'frontend')" in spec
    assert "os.path.join(project_root, 'start_web_ui.py')" in spec
    assert "'yaml'," in spec


def test_resource_paths_resolve_in_source_tree() -> None:
    assert engine_resource_path("data", "defaults").is_dir()
    assert report_resource_path("data", "opensource_fonts.json").is_file()
