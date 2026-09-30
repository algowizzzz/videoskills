"""Local MuseTalk renderer for short presenter clips on this 16 GB Mac."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / "vendor/musetalk-mac/upstream"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--presenter", type=Path, required=True)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--face-detector", choices=("yunet", "mediapipe"), default="yunet")
    p.add_argument("--float16", action="store_true", help="Use lower-memory half-precision model inference")
    p.add_argument("--output", type=Path, default=ROOT / "outputs/presenter.mp4")
    args = p.parse_args()
    for path in (args.presenter, args.audio):
        if not path.is_file():
            p.error(f"Missing local input: {path}")
    probe = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "json", str(args.audio.resolve())], text=True)
    duration = float(json.loads(probe)["format"]["duration"])
    if not 0 < duration <= 30:
        p.error("Use an audio clip of up to 30 seconds for this Mac prototype.")
    env = os.environ.copy()
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
               PYTORCH_ENABLE_MPS_FALLBACK="1", GLOG_minloglevel="2",
               MPLCONFIGDIR=str(ROOT / ".runtime/matplotlib"),
               NUMBA_CACHE_DIR=str(ROOT / ".runtime/numba"))
    env["FACE_DETECTOR"] = args.face_detector
    env["YUNET_MODEL"] = str(ROOT / "models/yunet/face_detection_yunet_2023mar.onnx")
    (ROOT / "outputs").mkdir(exist_ok=True)
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="render-", dir=ROOT / "outputs") as directory:
        work = Path(directory)
        # Controlled names keep upstream intermediate filenames predictable.
        source = work / ("source" + args.presenter.suffix.lower())
        shutil.copyfile(args.presenter, source)
        audio = work / "speech.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(args.audio.resolve()),
                        "-ar", "16000", "-ac", "1", str(audio)], check=True)
        config = work / "config.json"
        config.write_text(json.dumps({"presenter": {"video_path": str(source),
                                      "audio_path": str(audio), "result_name": "presenter.mp4"}}))
        subprocess.run([str(ROOT / ".venv-video/bin/python"), "-u", "-m", "scripts.inference",
                        "--inference_config", str(config), "--result_dir", str(work / "results"),
                        "--unet_model_path", "models/musetalkV15/unet.pth",
                        "--unet_config", "models/musetalkV15/musetalk.json",
                        "--whisper_dir", "models/whisper", "--version", "v15",
                        "--batch_size", "1", "--fps", "12"] + (["--use_float16"] if args.float16 else []),
                       cwd=UPSTREAM, env=env, check=True)
        result = work / "results/v15/presenter.mp4"
        if not result.is_file() or result.stat().st_size == 0:
            raise RuntimeError("Video inference did not produce a usable file.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(result, args.output)
    report = {"elapsed_seconds": time.monotonic()-start, "input_audio_seconds": duration,
              "output": str(args.output.resolve())}
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
