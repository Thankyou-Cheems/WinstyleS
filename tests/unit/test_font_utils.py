from winstyles.utils.font_utils import split_font_families


def test_split_font_families_filters_generic_families() -> None:
    families = split_font_families("Maple Mono SC NF, Monaspace Neon, 'Dengxian', monospace")
    assert families == ["Maple Mono SC NF", "Monaspace Neon", "Dengxian"]
