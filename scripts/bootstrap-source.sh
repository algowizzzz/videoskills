#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
target="$root/vendor/musetalk-mac"
revision=7fd019315127d7f31e2e7f9853547ddceabbeb6e
if [ -e "$target" ]; then
  echo "Source target already exists: $target" >&2
  exit 1
fi
mkdir -p "$root/vendor"
git clone https://github.com/barnent1/musetalk-mac.git "$target"
git -C "$target" checkout --detach "$revision"
git -C "$target" apply "$root/patches/musetalk-mac.patch"
mkdir -p "$target/upstream/musetalk/models" "$target/upstream/musetalk/utils"
cp "$root/patches/vae.py" "$target/upstream/musetalk/models/vae.py"
cp "$root/patches/unet.py" "$target/upstream/musetalk/models/unet.py"
cp "$root/patches/preprocessing_cpu.py" "$target/upstream/musetalk/utils/preprocessing_cpu.py"
echo "MuseTalk Mac source prepared at $target"
