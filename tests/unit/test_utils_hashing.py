from __future__ import annotations

import hashlib
from pathlib import Path

from winstyles.utils.hashing import (
    compute_hash,
    compute_hashes_for_directory,
    generate_checksum_file,
    verify_checksum_file,
    verify_hash,
)


def test_compute_hash_matches_hashlib(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"hello world")

    expected = hashlib.sha256(b"hello world").hexdigest()
    assert compute_hash(str(file_path)) == expected


def test_verify_hash_handles_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.txt"
    assert verify_hash(str(missing_path), "deadbeef") is False


def test_checksum_roundtrip(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("beta", encoding="utf-8")

    generate_checksum_file(str(tmp_path))
    ok, failed = verify_checksum_file(str(tmp_path))

    assert ok is True
    assert failed == []

    hashes = compute_hashes_for_directory(str(tmp_path))
    assert "a.txt" in hashes
    assert str(Path("nested") / "b.txt") in hashes
