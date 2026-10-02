"""Authentication, URL parsing, and Helix calls for Twitch clips."""

from __future__ import annotations

from datetime import datetime
from re import fullmatch
from urllib.parse import urlparse

import requests

from gif_finder.services.twitch.contracts import TwitchClipData


class TwitchClientError(RuntimeError):
    """Raised when Twitch cannot satisfy a request."""


class InvalidTwitchClipUrl(ValueError):
    """Raised when a URL is not a supported Twitch clip URL."""


class TwitchClipNotFound(TwitchClientError):
    """Raised when Helix has no clip for the supplied ID."""


class TwitchConfigurationError(TwitchClientError):
    """Raised when Twitch credentials have not been configured."""


def get_clip_id(url: str) -> str:
    """Extract a clip slug from either of Twitch's public clip URL forms."""
    candidate = url.strip()
    if not candidate:
        raise InvalidTwitchClipUrl("Invalid Twitch clip URL.")
    if not candidate.startswith(("http://", "https://")):
        candidate = "https://" + candidate

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]

    clip_id = None
    if host == "clips.twitch.tv" and len(parts) == 1:
        clip_id = parts[0]
    elif (
        host in {"twitch.tv", "www.twitch.tv"}
        and len(parts) == 3
        and parts[1].lower() == "clip"
    ):
        clip_id = parts[2]

    if clip_id and fullmatch(r"[A-Za-z0-9_-]+", clip_id):
        return clip_id

    raise InvalidTwitchClipUrl("Invalid Twitch clip URL.")


class TwitchClient:
    """Small synchronous client for Twitch app authentication and Helix clips."""

    token_url = "https://id.twitch.tv/oauth2/token"
    clips_url = "https://api.twitch.tv/helix/clips"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        http: requests.Session | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.http = http or requests.Session()
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "TwitchClient":
        from gif_finder.config import settings

        return cls(settings.twitch_client_id, settings.twitch_client_secret)

    def get_clip(self, clip_id: str) -> TwitchClipData:
        token = self._get_access_token()
        try:
            response = self.http.get(
                self.clips_url,
                params={"id": clip_id},
                headers={
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {token}",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise TwitchClientError("Twitch clip lookup failed.") from exc

        if not isinstance(payload, dict):
            raise TwitchClientError("Twitch returned an invalid clip response.")
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise TwitchClientError("Twitch returned an invalid clip response.")
        if not rows:
            raise TwitchClipNotFound("Twitch clip not found.")

        try:
            return self._normalise_clip(rows[0])
        except (KeyError, TypeError, ValueError) as exc:
            raise TwitchClientError("Twitch returned invalid clip metadata.") from exc

    def _get_access_token(self) -> str:
        if not self.client_id.strip() or not self.client_secret.strip():
            raise TwitchConfigurationError("Twitch API credentials are not configured.")
        try:
            response = self.http.post(
                self.token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise TwitchClientError("Twitch authentication failed.") from exc
        if not isinstance(payload, dict):
            raise TwitchClientError("Twitch authentication returned an invalid response.")
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise TwitchClientError("Twitch authentication returned no access token.")
        return token

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @classmethod
    def _normalise_clip(cls, row: dict[str, object]) -> TwitchClipData:
        return TwitchClipData(
            twitch_clip_id=str(row["id"]),
            broadcaster_id=str(row["broadcaster_id"]),
            broadcaster_name=str(row["broadcaster_name"]),
            creator_id=cls._optional_text(row.get("creator_id")),
            creator_name=cls._optional_text(row.get("creator_name")),
            video_id=cls._optional_text(row.get("video_id")),
            game_id=cls._optional_text(row.get("game_id")),
            vod_offset=(
                int(row["vod_offset"]) if row.get("vod_offset") is not None else None
            ),
            title=str(row["title"]),
            language=cls._optional_text(row.get("language")),
            duration=float(row["duration"]),
            created_at=datetime.fromisoformat(
                str(row["created_at"]).replace("Z", "+00:00")
            ),
        )
