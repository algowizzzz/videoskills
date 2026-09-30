#!/usr/bin/env python3
"""Pack and restore verified model files using Git LFS transport chunks.

This module uses only the Python standard library. It never downloads models.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "manifests/models.json"
TRANSPORT_MANIFEST = ROOT / "manifests/transport.json"
BUFFER = 8 * 1024 * 1024
DEFAULT_CHUNK = 1_000_000_000
POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"


def safe_path(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    if not relative or p.is_absolute() or any(part in (".", "..") for part in p.parts):
        raise ValueError(f"unsafe relative path: {relative!r}")
    base = root.resolve()
    target = base.joinpath(*p.parts)
    if not target.resolve().is_relative_to(base):
        raise ValueError(f"path escapes root: {relative!r}")
    return target


def load_manifest(path: Path) -> dict:
    with path.open() as f:
        value = json.load(f)
    if value.get("version") != 1 or not isinstance(value.get("files"), list):
        raise ValueError(f"invalid manifest: {path}")
    return value


def file_hash(path: Path) -> tuple[int, str]:
    total = 0
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(BUFFER):
            total += len(data)
            digest.update(data)
    return total, digest.hexdigest()


def checked_file(root: Path, item: dict) -> Path:
    path = safe_path(root, item["path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    size, digest = file_hash(path)
    if size != item["bytes"] or digest != item["sha256"]:
        raise ValueError(f"size or SHA-256 mismatch: {path}")
    return path


def selected(manifest: dict, profiles: set[str]) -> list[dict]:
    return [item for item in manifest["files"] if profiles.intersection(item["profiles"])]


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(temp, path)


def pack(root: Path, files: list[dict], chunk_bytes: int, transport: Path) -> None:
    if not 0 < chunk_bytes < 2_000_000_000:
        raise ValueError("chunk size must be below 2,000,000,000 bytes")
    entries = []
    for item in files:
        source = checked_file(root, item)
        chunks = []
        with source.open("rb") as f:
            index = 0
            while True:
                first = f.read(min(BUFFER, chunk_bytes))
                if not first:
                    break
                relative = f"model-store/{item['id']}/{item['sha256']}/part-{index:05d}.bin"
                target = safe_path(root, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                count = 0
                with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as output:
                    temp = Path(output.name)
                    data = first
                    while data:
                        output.write(data)
                        digest.update(data)
                        count += len(data)
                        if count == chunk_bytes:
                            break
                        data = f.read(min(BUFFER, chunk_bytes - count))
                os.replace(temp, target)
                chunks.append({"path": relative, "bytes": count, "sha256": digest.hexdigest()})
                index += 1
        entries.append({"id": item["id"], "path": item["path"], "bytes": item["bytes"],
                        "sha256": item["sha256"], "chunks": chunks})
        print(f"packed {item['id']}: {len(chunks)} chunks", file=sys.stderr)
    atomic_json(transport, {"version": 1, "chunk_bytes": chunk_bytes, "files": entries})


def verify_transport(root: Path, files: list[dict]) -> None:
    for item in files:
        if not item["chunks"]:
            raise ValueError(f"no chunks for {item['id']}")
        total = 0
        for index, chunk in enumerate(item["chunks"]):
            expected = f"model-store/{item['id']}/{item['sha256']}/part-{index:05d}.bin"
            if chunk["path"] != expected:
                raise ValueError(f"unexpected chunk order/path for {item['id']}")
            path = safe_path(root, chunk["path"])
            with path.open("rb") as f:
                if f.read(len(POINTER_PREFIX)) == POINTER_PREFIX:
                    raise ValueError(f"LFS pointer instead of downloaded model data: {path}")
            size, digest = file_hash(path)
            if size != chunk["bytes"] or digest != chunk["sha256"]:
                raise ValueError(f"chunk checksum mismatch: {path}")
            total += size
        if total != item["bytes"]:
            raise ValueError(f"combined chunk size mismatch: {item['id']}")


def restore(root: Path, files: list[dict], repair: bool) -> None:
    verify_transport(root, files)
    for item in files:
        target = safe_path(root, item["path"])
        if target.exists():
            try:
                checked_file(root, item)
                print(f"already valid: {item['id']}")
                continue
            except ValueError:
                if not repair:
                    raise ValueError(f"invalid existing file (pass --repair to replace): {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("wb", dir=target.parent, delete=False) as output:
            temp = Path(output.name)
            for chunk in item["chunks"]:
                with safe_path(root, chunk["path"]).open("rb") as source:
                    shutil.copyfileobj(source, output, BUFFER)
        try:
            size, digest = file_hash(temp)
            if size != item["bytes"] or digest != item["sha256"]:
                raise ValueError(f"restored checksum mismatch: {item['id']}")
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        print(f"restored {item['id']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "plan", "pack", "verify-transport", "restore", "verify-installed"])
    parser.add_argument("--profile", default="voice,video", help="comma-separated voice,video,transcribe")
    parser.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK)
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    profiles = set(args.profile.split(","))
    if not profiles or not profiles.issubset({"voice", "video", "transcribe"}):
        parser.error("invalid profile")
    manifest = load_manifest(root / "manifests/models.json")
    files = selected(manifest, profiles)
    if args.command in ("status", "plan"):
        for item in files:
            path = safe_path(root, item["path"])
            print(f"{item['id']}: {item['bytes']} bytes; {'present' if path.is_file() else 'missing'}; {item['path']}")
        print(f"total model bytes: {sum(x['bytes'] for x in files)}")
        return 0
    if args.command == "pack":
        pack(root, files, args.chunk_bytes, root / "manifests/transport.json")
        return 0
    if args.command == "verify-installed":
        for item in files:
            checked_file(root, item)
            print(f"verified {item['id']}")
        return 0
    transport = load_manifest(root / "manifests/transport.json")
    packed = {item["id"]: item for item in transport["files"]}
    chosen = []
    for item in files:
        if item["id"] not in packed:
            raise ValueError(f"not packed: {item['id']}")
        entry = packed[item["id"]]
        if any(entry[k] != item[k] for k in ("path", "bytes", "sha256")):
            raise ValueError(f"source/transport manifest mismatch: {item['id']}")
        chosen.append(entry)
    if args.command == "verify-transport":
        verify_transport(root, chosen)
        print(f"verified {len(chosen)} transport assets")
    else:
        restore(root, chosen, args.repair)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"model manager: {exc}", file=sys.stderr)
        raise SystemExit(1)
