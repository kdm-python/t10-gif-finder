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
    assert "inspect" in result.stdout.lower()


def test_cli_show_tags_smoke():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "gif_finder.cli", "--show", "tags"],
        check=False,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "tags" in result.stdout.lower()
