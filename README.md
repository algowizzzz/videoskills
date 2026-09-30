# Local digital presenter prototype

This repository contains a Mac prototype that generates speech from a local voice reference and animates a presenter's mouth to match it. The pipeline uses Qwen3-TTS through MLX Audio, MuseTalk v1.5, YuNet face detection, and FFmpeg. It is a short-clip research prototype, not a real-time service.

The model weights are **not currently in this repository**. `manifests/models.json` records their original sizes and SHA-256 checksums. `scripts/model_manager.py` can split verified local weights into Git LFS transport chunks and reassemble them on another machine. `manifests/transport.json` will exist only after actual weights are packed. Do not treat the source manifest as proof that weights were uploaded.

Read [installation](docs/INSTALL.md), [model publishing](docs/MODEL_PUBLISHING.md), and [third-party notices](THIRD_PARTY_NOTICES.md) before use.

The original test machine was an M2 MacBook Air with 16 GB memory. It rendered one roughly five-second clip in about six minutes with substantial memory pressure. A higher-memory Apple Silicon machine is preferable. The Python environments and models were intentionally removed from the test Mac after validation.

No personal reference footage, transcripts, generated executive media, or private logs belong in this public repository. Use only media for which you have rights and consent.
