from winstyles.infra.filesystem import WindowsFileSystemAdapter
from winstyles.infra.registry import MockRegistryAdapter
from winstyles.plugins.theme import ThemeScanner


def test_theme_scanner_collects_dwm_colorization_fields() -> None:
    personalize_key = r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    accent_key = r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Accent"
    dwm_key = r"HKCU\SOFTWARE\Microsoft\Windows\DWM"
    registry = MockRegistryAdapter(
        {
            personalize_key: {
                "AppsUseLightTheme": 1,
                "SystemUsesLightTheme": 1,
                "EnableTransparency": 1,
                "ColorPrevalence": 0,
            },
            accent_key: {
                "AccentColorMenu": 0x00332211,
                "AccentPalette": b"\x11\x22",
            },
            dwm_key: {
                "ColorizationColor": 0x00332211,
                "ColorizationAfterglow": 0x00CCBBAA,
                "ColorizationColorBalance": 80,
                "ColorizationAfterglowBalance": 0,
                "ColorizationBlurBalance": 10,
                "AccentColorInactive": 0x00665544,
            },
        }
    )

    scanner = ThemeScanner(registry, WindowsFileSystemAdapter())
    items = scanner.scan()
    by_key = {item.key: item for item in items}

    assert by_key["theme.dwm.colorizationColor"].current_value == "#112233"
    assert by_key["theme.dwm.colorizationAfterglow"].current_value == "#AABBCC"
    assert by_key["theme.dwm.accentColorInactive"].current_value == "#445566"
    assert by_key["theme.dwm.colorizationColorBalance"].current_value == 80

    apply_item = by_key["theme.dwm.colorizationColor"]
    assert scanner.apply(apply_item) is True
    value, _ = registry.get_value(dwm_key, "ColorizationColor")
    assert value == 0x00332211
