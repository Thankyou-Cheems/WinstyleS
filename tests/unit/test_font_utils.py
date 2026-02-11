from winstyles.utils.font_utils import identify_opensource, split_font_families


def test_split_font_families_filters_generic_families() -> None:
    families = split_font_families("Maple Mono SC NF, Monaspace Neon, 'Dengxian', monospace")
    assert families == ["Maple Mono SC NF", "Monaspace Neon", "Dengxian"]


def test_identify_opensource_matches_known_font() -> None:
    match = identify_opensource("Maple Mono SC NF")
    assert match is not None
    assert match["name"] == "Maple Mono"


def test_identify_opensource_returns_none_for_unknown_font() -> None:
    assert identify_opensource("This Font Should Not Exist 12345") is None
