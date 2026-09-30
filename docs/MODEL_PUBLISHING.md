# Publishing model weights through Git LFS

The public repository currently contains no weights or LFS chunks. Do the following on a staging machine with ample free storage after confirming redistribution rights for each asset. GitHub Free/Pro has a per-object LFS limit; the default 1,000,000,000-byte chunks keep MuseTalk's 3.4 GB file below 2 GB per object. Chunking does not remove total storage or download quotas.

1. Download the pinned model files to their paths in `manifests/models.json`. Compare actual size and SHA-256 with the manifest. `python3 scripts/model_manager.py verify-installed` must pass. The source manifest is based on the original successful local installation; all weights were later removed from that Mac.
2. Run `git lfs install --local`. Confirm `.gitattributes` tracks `model-store/**/*.bin` in LFS. This changes this repository only.
3. Run `python3 scripts/model_manager.py pack --profile voice,video,transcribe`. This verifies each original and writes chunks plus `manifests/transport.json`. Transcription is optional; omit `transcribe` to save about 0.97 GB. The core voice/video set is about 6.5 GB.
4. Run `python3 scripts/model_manager.py verify-transport --profile voice,video,transcribe` for the same selected profiles. Inspect `git status`, added paths, `git lfs ls-files`, and the staged file sizes. Stage only `model-store/` and `manifests/transport.json` after license review. Never stage `inputs/`, `outputs/`, assembled `models/`, nested vendor weights, or private logs.
5. Commit and push to the selected branch. Confirm on a fresh checkout with `GIT_LFS_SKIP_SMUDGE=1` followed by `git lfs pull`, `verify-transport`, `restore`, and `verify-installed`. A pull or clone consumes LFS bandwidth.

If distribution rights for a support model are unclear, leave its chunks unpublished and have installers acquire it from the original source. A complete LFS-hosted offline model bundle is not ready until all required assets and licensing questions are resolved. Do not commit fabricated `transport.json` entries or ordinary Git blobs containing weights.
