from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from gif_finder.api.app import app
from gif_finder.services.twitch.api import (
    TwitchClient,
    TwitchClientError,
    TwitchClipNotFound,
)
from gif_finder.services.twitch.contracts import TwitchClipData


def clip_data(
    *,
    video_id: str | None = "987654321",
    vod_offset: int | None = 3723,
) -> TwitchClipData:
    return TwitchClipData(
        twitch_clip_id="ApatheticMistyPlumWholeWheat",
        broadcaster_id="167124768",
        broadcaster_name="T10Nat",
        creator_id="484542553",
        creator_name="demolaze",
        video_id=video_id,
        game_id="509658",
        vod_offset=vod_offset,
        title="Nat took the shoes",
        language="en",
        duration=60.0,
        created_at=datetime(2026, 9, 29, 11, 7, 4, tzinfo=UTC),
    )


def test_import_duplicate_get_list_and_delete(db_session, monkeypatch) -> None:
    calls: list[str] = []

    def fake_get_clip(self, clip_id: str) -> TwitchClipData:
        calls.append(clip_id)
        return clip_data()

    monkeypatch.setattr(TwitchClient, "get_clip", fake_get_clip)
    payload = {"url": "https://www.twitch.tv/t10nat/clip/ApatheticMistyPlumWholeWheat"}

    with TestClient(app) as client:
        created = client.post("/twitch/clips", json=payload)
        assert created.status_code == 201, created.text
        clip = created.json()
        assert clip["twitch_clip_id"] == "ApatheticMistyPlumWholeWheat"
        assert clip["vod_url"] == (
            "https://www.twitch.tv/videos/987654321?t=1h2m3s"
        )

        duplicate = client.post("/twitch/clips", json=payload)
        assert duplicate.status_code == 200
        assert duplicate.json() == clip
        assert calls == ["ApatheticMistyPlumWholeWheat"]

        listed = client.get("/twitch/clips")
        assert listed.status_code == 200
        assert listed.json() == [clip]
        assert client.get(f"/twitch/clips/{clip['id']}").json() == clip
        assert client.get("/twitch/clips/999999").status_code == 404

        assert client.delete(f"/twitch/clips/{clip['id']}").status_code == 204
        assert client.get(f"/twitch/clips/{clip['id']}").status_code == 404
        assert client.delete(f"/twitch/clips/{clip['id']}").status_code == 404


def test_import_rejects_invalid_twitch_url(db_session, monkeypatch) -> None:
    def unexpected_call(self, clip_id: str) -> TwitchClipData:
        raise AssertionError("Twitch should not be called for an invalid URL")

    monkeypatch.setattr(TwitchClient, "get_clip", unexpected_call)
    with TestClient(app) as client:
        response = client.post(
            "/twitch/clips", json={"url": "https://example.com/not-a-clip"}
        )
    assert response.status_code == 400


def test_import_returns_404_when_twitch_has_no_clip(db_session, monkeypatch) -> None:
    def missing_clip(self, clip_id: str) -> TwitchClipData:
        raise TwitchClipNotFound("Twitch clip not found.")

    monkeypatch.setattr(TwitchClient, "get_clip", missing_clip)
    with TestClient(app) as client:
        response = client.post(
            "/twitch/clips", json={"url": "https://clips.twitch.tv/MissingClip"}
        )
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("video_id", "vod_offset"),
    [(None, 12), ("987654321", None)],
)
def test_vod_url_is_null_without_complete_vod_location(
    db_session, monkeypatch, video_id, vod_offset
) -> None:
    def fake_get_clip(self, clip_id: str) -> TwitchClipData:
        return clip_data(video_id=video_id, vod_offset=vod_offset)

    monkeypatch.setattr(TwitchClient, "get_clip", fake_get_clip)
    with TestClient(app) as client:
        response = client.post(
            "/twitch/clips",
            json={"url": "https://clips.twitch.tv/ApatheticMistyPlumWholeWheat"},
        )
    assert response.status_code == 201
    assert response.json()["vod_url"] is None


def test_import_maps_twitch_api_errors_to_bad_gateway(db_session, monkeypatch) -> None:
    def failed_lookup(self, clip_id: str) -> TwitchClipData:
        raise TwitchClientError("Twitch clip lookup failed.")

    monkeypatch.setattr(TwitchClient, "get_clip", failed_lookup)
    with TestClient(app) as client:
        response = client.post(
            "/twitch/clips", json={"url": "https://clips.twitch.tv/UnavailableClip"}
        )
    assert response.status_code == 502
