import json
import subprocess
from pathlib import Path

from loguru import logger


class MediaProbeError(RuntimeError):
    """Raised when ffprobe cannot return valid metadata for a file."""


def run_ffprobe(path: Path) -> dict:
    """Run ffprobe with machine-readable JSON output for one media file."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    try:
        logger.debug("Running ffprobe for {}", path)
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise MediaProbeError("ffprobe is not installed or is not on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise MediaProbeError(
            f"ffprobe could not inspect {path.name}: {exc.stderr.strip()}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise MediaProbeError(f"ffprobe timed out while inspecting {path.name}.") from exc

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MediaProbeError(f"ffprobe returned invalid JSON for {path.name}.") from exc
