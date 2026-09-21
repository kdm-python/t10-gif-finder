import json
import subprocess
import sys
from pathlib import Path


def test_cli_help_smoke():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "gif_finder.cli", "--help"],
        check=False,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "media" in result.stdout.lower()


def test_cli_tag_view_smoke():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "gif_finder.cli", "tag", "view"],
        check=False,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "tags" in result.stdout.lower()


def test_cli_tag_view_json_is_pipeable():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "gif_finder.cli", "tag", "view", "--json"],
        check=False,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert isinstance(json.loads(result.stdout), list)


def test_cli_media_view_json_is_pipeable():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "gif_finder.cli", "media", "view", "--json"],
        check=False,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert isinstance(json.loads(result.stdout), list)


def test_cli_media_inspect_outputs_json():
    project_root = Path(__file__).resolve().parents[1]
    fixture = project_root / "tests/fixtures/gif/animated_floor.gif"
    result = subprocess.run(
        [sys.executable, "-m", "gif_finder.cli", "media", "inspect", str(fixture)],
        check=False,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["container_format"] == "gif"
    assert payload["width"] > 0
    assert payload["height"] > 0
