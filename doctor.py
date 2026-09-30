"""Read-only local prerequisite report; never downloads or loads models."""
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys

root = Path(__file__).resolve().parent
manifest_path = root / "manifests/models.json"
assets = json.loads(manifest_path.read_text())["files"] if manifest_path.is_file() else []
model_status = {}
for profile in ("voice", "video", "transcribe"):
    selected = [item for item in assets if profile in item["profiles"]]
    missing = [item["path"] for item in selected if not (root / item["path"]).is_file()]
    model_status[profile] = {"required_files": len(selected), "present_files": len(selected)-len(missing),
                             "ready_by_presence": bool(selected) and not missing, "missing": missing}
packages = {}
for name in ("mlx", "mlx-metal", "mlx-audio"):
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = None

report = {
    "platform": platform.platform(),
    "architecture": platform.machine(),
    "python": sys.version.split()[0],
    "free_disk_gib": round(shutil.disk_usage(root).free / 2**30, 2),
    "ffmpeg": shutil.which("ffmpeg"),
    "packages": packages,
    "models": model_status,
    "voice_environment_present": (root / ".venv/bin/python").is_file(),
    "video_environment_present": (root / ".venv-video/bin/python").is_file(),
    "historical_voice_test_report_present": (root / "outputs/voice-smoke.json").is_file(),
    "historical_video_test_report_present": (root / "outputs/presenter-smoke.json").is_file(),
}
print(json.dumps(report, indent=2))
