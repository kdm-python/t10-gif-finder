from __future__ import annotations

import pytest

from gif_finder.services.twitch.api import (
    InvalidTwitchClipUrl,
    TwitchClient,
    TwitchClipNotFound,
    get_clip_id,
)


class FakeResponse:
    def __init__(self, payload) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class FakeHttp:
    def __init__(self, clip_payload) -> None:
        self.clip_payload = clip_payload
        self.get_kwargs = None

    def post(self, url, **kwargs) -> FakeResponse:
        return FakeResponse({"access_token": "test-token"})

    def get(self, url, **kwargs) -> FakeResponse:
        self.get_kwargs = kwargs
        return FakeResponse(self.clip_payload)


def twitch_payload() -> dict:
    return {
        "data": [
            {
                "id": "ClipSlug",
                "broadcaster_id": "123",
                "broadcaster_name": "Broadcaster",
                "creator_id": "456",
                "creator_name": "Creator",
                "video_id": "789",
                "game_id": "10",
                "vod_offset": 65,
                "title": "A clip",
                "language": "en",
                "duration": 30,
                "created_at": "2026-09-29T11:07:04Z",
            }
        ]
    }


def test_client_authenticates_and_fetches_normalised_clip_metadata() -> None:
    http = FakeHttp(twitch_payload())
    clip = TwitchClient("client-id", "client-secret", http=http).get_clip("ClipSlug")

    assert clip.twitch_clip_id == "ClipSlug"
    assert clip.video_id == "789"
    assert clip.vod_offset == 65
    assert http.get_kwargs["params"] == {"id": "ClipSlug"}
    assert http.get_kwargs["headers"] == {
        "Client-ID": "client-id",
        "Authorization": "Bearer test-token",
    }


def test_client_reports_an_empty_helix_result_as_not_found() -> None:
    with pytest.raises(TwitchClipNotFound):
        TwitchClient("client-id", "client-secret", http=FakeHttp({"data": []})).get_clip(
            "MissingClip"
        )


def test_clip_url_parser_accepts_twitch_forms_and_rejects_other_hosts() -> None:
    assert get_clip_id("https://clips.twitch.tv/ClipSlug") == "ClipSlug"
    assert get_clip_id("twitch.tv/channel/clip/ClipSlug") == "ClipSlug"
    with pytest.raises(InvalidTwitchClipUrl):
        get_clip_id("https://example.com/channel/clip/ClipSlug")
