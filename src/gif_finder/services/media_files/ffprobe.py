import json
import subprocess
from pathlib import Path


class MediaProbeError(RuntimeError):
    pass


def run_ffprobe(path: Path) -> dict:
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

    return json.loads(result.stdout)
