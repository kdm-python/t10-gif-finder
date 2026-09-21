from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from gif_finder.services.media_files.storage import MediaStorage, MediaStorageError


FIXTURE = Path(__file__).parent.parent / "fixtures" / "gif" / "animated_floor.gif"


def test_store_hashes_and_copies_a_file(tmp_path: Path) -> None:
    storage = MediaStorage(tmp_path / "media")

    stored = storage.store(FIXTURE)
    stored_path = storage.resolve(stored.storage_key)

    assert stored.was_created is True
    assert stored_path.exists()
    assert stored_path.read_bytes() == FIXTURE.read_bytes()
    assert stored.content_hash == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert stored.file_size_bytes == FIXTURE.stat().st_size
    assert not list((storage.root / ".staging").iterdir())


def test_store_is_idempotent_for_identical_content(tmp_path: Path) -> None:
    storage = MediaStorage(tmp_path / "media")

    first = storage.store(FIXTURE)
    second = storage.store(FIXTURE)

    assert first.content_hash == second.content_hash
    assert first.storage_key == second.storage_key
    assert first.was_created is True
    assert second.was_created is False


def test_store_uses_hash_shard_as_storage_key(tmp_path: Path) -> None:
    stored = MediaStorage(tmp_path / "media").store(FIXTURE)

    assert stored.storage_key == f"{stored.content_hash[:2]}/{stored.content_hash}"


def test_storage_rejects_missing_source_and_unsafe_keys(tmp_path: Path) -> None:
    storage = MediaStorage(tmp_path / "media")

    with pytest.raises(FileNotFoundError):
        storage.store(tmp_path / "missing.gif")

    with pytest.raises(MediaStorageError, match="escapes"):
        storage.resolve("../../outside")
