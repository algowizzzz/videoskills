#!/usr/bin/env python3
"""Download pinned public assets and publish verified LFS chunks from a disposable runner.

Run only in GitHub Actions with an authenticated repository checkout. Never run
this on the user's Mac: the weights and transport copies need substantial disk.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

from model_manager import ROOT, SOURCE_MANIFEST, TRANSPORT_MANIFEST, checked_file, pack, safe_path


HF = {
    "models/qwen3-tts-base/": ("mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16", "1eccf1cb2519b5a4e8a95b5f0544f3303568164f"),
    "vendor/musetalk-mac/upstream/models/musetalkV15/": ("TMElyralab/MuseTalk", "3ef28bc5cff08c90ad8178a25f1b570cd800170f"),
    "vendor/musetalk-mac/upstream/models/sd-vae/": ("stabilityai/sd-vae-ft-mse", "31f26fdeee1355a5c34592e401dd41e45d25a493"),
    "vendor/musetalk-mac/upstream/models/whisper/": ("openai/whisper-tiny", "169d4a4341b33bc18d8881c4b69c2e104e1cc0af"),
    "models/whisper-small.en/": ("openai/whisper-small.en", "e8727524f962ee844a7319d92be39ac1bd25655a"),
}


def source(item: dict) -> tuple[str, str]:
    path = item["path"]
    for prefix, (repo, revision) in HF.items():
        if path.startswith(prefix):
            relative = path[len(prefix):]
            if repo == "TMElyralab/MuseTalk":
                relative = "musetalkV15/" + relative
            return "url", f"https://huggingface.co/{repo}/resolve/{revision}/{urllib.parse.quote(relative)}"
    if path.endswith("/79999_iter.pth"):
        return "gdrive", "154JgKpzCPW82qINcVieuPH3fZ2e0P812"
    if path.endswith("/resnet18-5c106cde.pth"):
        return "url", "https://download.pytorch.org/models/resnet18-5c106cde.pth"
    if path.endswith("/face_detection_yunet_2023mar.onnx"):
        return "url", "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    raise ValueError(f"no source mapped for {path}")


def download(item: dict) -> Path:
    target = safe_path(ROOT, item["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    kind, location = source(item)
    print(f"Downloading {item['id']} ({item['bytes']} bytes)", flush=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as f:
        temporary = Path(f.name)
    try:
        if kind == "gdrive":
            import gdown
            if not gdown.download(id=location, output=str(temporary), quiet=False):
                raise RuntimeError("Google Drive download failed")
        else:
            req = urllib.request.Request(location, headers={"User-Agent": "videoskills-model-publisher/1.0"})
            with urllib.request.urlopen(req, timeout=180) as response, temporary.open("wb") as out:
                shutil.copyfileobj(response, out, 8 * 1024 * 1024)
        probe = dict(item, path=str(temporary.relative_to(ROOT)))
        checked_file(ROOT, probe)
        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REPOSITORY") != "algowizzzz/videoskills":
        raise RuntimeError("this publisher runs only in the videoskills GitHub Actions checkout")
    manifest = json.loads(SOURCE_MANIFEST.read_text())
    entries = json.loads(TRANSPORT_MANIFEST.read_text())["files"] if TRANSPORT_MANIFEST.exists() else []
    published = {item["id"] for item in entries}
    run("git", "lfs", "install", "--local")
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    for item in manifest["files"]:
        if item["id"] in published:
            print(f"already published: {item['id']}", flush=True)
            continue
        # Download + checked-out chunks + local LFS object copies can coexist.
        required = item["bytes"] * 3 + 1_000_000_000
        available = shutil.disk_usage(ROOT).free
        if available < required:
            raise RuntimeError(f"insufficient runner disk for {item['id']}: need {required}, have {available}")
        original = download(item)
        one_manifest = ROOT / "manifests" / "transport-one.json"
        try:
            pack(ROOT, [item], 1_000_000_000, one_manifest)
            entry = json.loads(one_manifest.read_text())["files"][0]
            entries.append(entry)
            TRANSPORT_MANIFEST.write_text(json.dumps({"version": 1, "chunk_bytes": 1_000_000_000,
                                                      "files": entries}, indent=2, sort_keys=True) + "\n")
            paths = [chunk["path"] for chunk in entry["chunks"]]
            run("git", "add", "manifests/transport.json", *paths)
            run("git", "lfs", "ls-files")
            run("git", "commit", "-m", f"Publish verified model asset {item['id']}")
            run("git", "push", "origin", "HEAD:main")
            published.add(item["id"])
        finally:
            original.unlink(missing_ok=True)
            one_manifest.unlink(missing_ok=True)
            # This is a disposable runner; published objects are already remote.
            if item["id"] in published:
                for chunk in entry["chunks"]:
                    safe_path(ROOT, chunk["path"]).unlink(missing_ok=True)
                shutil.rmtree(ROOT / ".git/lfs/objects", ignore_errors=True)
    print(f"Published {len(published)} model assets", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"publish models: {exc}", file=sys.stderr)
        raise
