from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gif_finder.api.app import app

FIXTURE = Path(__file__).parent / "fixtures" / "gif" / "animated_floor.gif"


def test_tag_endpoints(db_session) -> None:
    with TestClient(app) as client:
        created = client.post("/tags", json={"name": "Funny"})
        assert created.status_code == 201
        tag = created.json()
        assert tag["name"] == "funny"

        listed = client.get("/tags")
        assert listed.status_code == 200
        assert listed.json() == [tag]

        assert client.get(f"/tags/{tag['id']}").json() == tag
        assert client.delete(f"/tags/{tag['id']}").status_code == 204
        assert client.get(f"/tags/{tag['id']}").status_code == 404


def test_stream_endpoints_allow_partial_update(db_session) -> None:
    with TestClient(app) as client:
        created = client.post(
            "/streams",
            json={"stream_date": "2026-09-23", "description": "First stream"},
        )
        assert created.status_code == 201
        stream_id = created.json()["id"]

        updated = client.patch(
            f"/streams/{stream_id}", json={"description": "Updated stream"}
        )
        assert updated.status_code == 200
        assert updated.json()["stream_date"] == "2026-09-23"
        assert updated.json()["description"] == "Updated stream"

        assert client.delete(f"/streams/{stream_id}").status_code == 204


def test_media_upload_update_and_delivery(db_session) -> None:
    with TestClient(app) as client:
        created = client.post(
            "/media",
            files={"file": (FIXTURE.name, FIXTURE.read_bytes(), "image/gif")},
            data={"tags": ["funny", "reaction"], "title": "Floor"},
        )
        assert created.status_code == 201, created.text
        media = created.json()
        assert media["original_filename"] == FIXTURE.name
        assert media["tags"] == ["funny", "reaction"]
        assert media["file_url"] == f"/media/{media['id']}/file"

        updated = client.patch(
            f"/media/{media['id']}",
            json={"author": "Tester", "tags": ["animated"]},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["author"] == "Tester"
        assert updated.json()["tags"] == ["animated"]

        delivered = client.get(media["file_url"])
        assert delivered.status_code == 200
        assert delivered.content == FIXTURE.read_bytes()

        assert client.delete(f"/media/{media['id']}").status_code == 204
        assert client.get(f"/media/{media['id']}").status_code == 404
