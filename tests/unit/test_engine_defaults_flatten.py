from winstyles.core.engine import StyleEngine


def test_flatten_defaults_maps_theme_cursor_and_wallpaper(monkeypatch) -> None:
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    engine = StyleEngine.__new__(StyleEngine)
    raw = {
        "theme": {
            "appsUseLightTheme": 1,
            "systemUsesLightTheme": 1,
            "enableTransparency": 1,
            "colorPrevalence": 0,
            "accentColor": "#0078D4",
        },
        "appearance": {
            "colorization_color": "0x00332211",
            "colorization_color_balance": 90,
        },
        "wallpaper": {"style": "10", "tile": "0"},
        "cursor": {
            "scheme": "Windows Default",
            "cursors": {"Arrow": r"%SystemRoot%\cursors\aero_arrow.cur"},
        },
    }

    flattened = engine._flatten_defaults(raw)
    assert flattened["theme"]["theme.dwm.colorizationColor"] == "#112233"
    assert flattened["theme"]["theme.dwm.colorizationColorBalance"] == 90
    assert flattened["wallpaper"]["wallpaper.style"] == "10"
    assert flattened["cursor"]["cursor.scheme"] == "Windows Default"
    assert flattened["cursor"]["cursor.arrow"] == r"C:\Windows\cursors\aero_arrow.cur"
