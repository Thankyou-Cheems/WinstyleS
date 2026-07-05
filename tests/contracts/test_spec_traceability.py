# enforces: the traceability chain itself.
# Direction 1: every spec's "Contract Coverage" section must reference test files that exist.
# Direction 2: every file in tests/contracts/ must carry an "# enforces:" header
#              pointing at a spec file that exists.

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPECS = REPO / "docs" / "specs"
CONTRACTS = REPO / "tests" / "contracts"

COVERAGE_RE = re.compile(r"`(tests/[\w./-]+\.py)`")
ENFORCES_RE = re.compile(r"#\s*enforces:\s*(docs/specs/[\w./-]+\.md)")


def _extract_section(text: str, title: str) -> str:
    match = re.search(
        rf"^#{{2,}}\s+{re.escape(title)}\s*$(.*?)(?=^#{{2,}}\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def test_spec_contract_coverage_files_exist() -> None:
    missing = []
    for spec in sorted(SPECS.glob("*.md")):
        section = _extract_section(spec.read_text(encoding="utf-8"), "Contract Coverage")
        for path in COVERAGE_RE.findall(section):
            if not (REPO / path).exists():
                missing.append(f"{spec.name} -> {path}")
    assert not missing, f"dangling Contract Coverage references: {missing}"


def test_contract_files_declare_an_existing_spec() -> None:
    bad = []
    for test_file in sorted(CONTRACTS.glob("test_*.py")):
        if test_file.name == Path(__file__).name:
            continue
        head = test_file.read_text(encoding="utf-8")[:1000]
        match = ENFORCES_RE.search(head)
        if not match:
            bad.append(f"{test_file.name}: missing '# enforces: docs/specs/<spec>.md ...' header")
        elif not (REPO / match.group(1)).exists():
            bad.append(f"{test_file.name}: enforces nonexistent spec {match.group(1)}")
    assert not bad, "\n".join(bad)
