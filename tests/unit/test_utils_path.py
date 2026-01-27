from __future__ import annotations

from pathlib import Path

from winstyles.utils.path import collapse_vars, expand_vars, is_under_user_profile


def test_expand_vars_returns_absolute_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TESTVAR", str(tmp_path))

    expanded = expand_vars(r"%TESTVAR%\Foo\bar.txt")

    assert Path(expanded).is_absolute()
    assert expanded.lower().endswith(str(Path("Foo") / "bar.txt").lower())


def test_collapse_vars_prefers_env_var(monkeypatch, tmp_path: Path) -> None:
    appdata_path = tmp_path / "AppData" / "Roaming"
    appdata_path.mkdir(parents=True)
    monkeypatch.setenv("APPDATA", str(appdata_path))

    collapsed = collapse_vars(str(appdata_path))
    assert collapsed == "%APPDATA%"


def test_is_under_user_profile(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    assert is_under_user_profile(str(tmp_path / "Desktop")) is True
    assert is_under_user_profile(str(tmp_path.parent / "Other")) is False
