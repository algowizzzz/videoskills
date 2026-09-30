# Coding-agent handoff: reproducible offline digital presenter with Git LFS model distribution

## Objective

Turn this working Mac prototype into a reproducible repository that another machine can install and run end to end. Store source, manifests, documentation, and dependency definitions in ordinary Git. Support storing model binaries in Git LFS, splitting oversized binaries into transport chunks that are reassembled and verified before inference. In particular, distribute the roughly 3.4 GB MuseTalk `unet.pth` on a GitHub plan with a 2 GB per-file LFS limit.

Deliver the implementation and tests, not only advice. Proceed with reversible local code and documentation work. Do not download models, install heavy AI environments, execute inference, upload files, or create a paid resource merely to implement the tooling. Those operational stages need an explicitly selected destination/machine and authorization. Report which stages actually ran and which remain unexecuted.

## Current project and constraints

- Project: this repository's root directory.
- Original test machine: MacBook Air M2, 16 GB unified memory, macOS 14.5.
- The voice/video prototype worked with OS-level networking blocked, but a roughly five-second executive presenter clip took approximately six minutes to render. The workload created substantial memory pressure. Do not benchmark or rerun it on this Mac by default.
- The user deliberately deleted all model weights, `.venv`, `.venv-video`, and runtime caches. Retained code, lockfiles, historical manifests, source footage, and generated outputs must be preserved. Historical reports do not prove a current installation exists.
- At the last inspection, this directory was not a Git repository; Git LFS 3.6.1 was installed. Recheck current state before acting. No destination remote has been supplied.
- No Docker, cloud inference API, runtime CDN dependency, or mandatory web service. The deliverable remains a local command-line workflow; no UI is required.
- Initial supported runtime is Apple Silicon macOS. Do not claim that the MLX voice runtime works on NVIDIA/Linux or Windows. A Linux/CUDA port is a separate extension with its own dependencies and validation.
- Reference footage/audio, transcripts, generated executive media, and personal logs remain local. They must not be published as part of the repository.

Read applicable repository instructions and the existing code before changing anything. Preserve existing working behavior unless a documented fix is necessary.

## Existing generation workflow

One-time presenter preparation:
1. Accept an authorized reference video or portrait plus clear voice reference audio.
2. Extract approximately 5–15 seconds of audible reference speech with FFmpeg. Provide its accurate transcript manually or through optional local transcription followed by review.
3. Prepare a short presenter clip containing exactly one clearly visible face.

For each new script:
1. Qwen3-TTS generates speech using the saved reference audio and transcript.
2. MuseTalk matches the presenter's mouth to that speech, using CPU YuNet face detection.
3. FFmpeg produces the final H.264/AAC MP4.

If spoken audio is already supplied, skip Qwen and run only video generation/muxing. Existing audio duration limit is 30 seconds; preserve it. Long-form segmentation, real-time interaction, knowledge bases, and conversational agents are out of scope.

## Existing implementation to preserve

- `voice.py`: MLX Audio/Qwen generation with local model paths.
- `video.py`: MuseTalk wrapper, 12 fps, batch size 1, optional `--float16`, CPU YuNet default, isolated temporary output directory.
- `transcribe.py`: optional local Whisper-small.en transcription.
- `doctor.py`: installation diagnostics; improve it to distinguish historical outputs from presently verified assets.
- `run-local.sh`: applies macOS network denial to inference and children and fails when environments are absent.
- `requirements-mac.lock.txt`, `requirements-video.lock.txt`: historical environment snapshots, not complete portable installers.
- `reports/`: source revisions, hashes, model provenance, and historical execution evidence.
- `vendor/musetalk-mac/`: customized Mac port. Preserve the restored `upstream/musetalk/models/vae.py` and `unet.py`, patched inference script, and new `utils/preprocessing_cpu.py`. The latter avoids the observed MediaPipe display/OpenGL hang.

Do not mistake `upstream/musetalk/models/` Python source for `upstream/models/` model weights.

## Model inventory and provenance

Use `reports/model-checksums.json` as the historical byte-count and SHA-256 source. Check coverage rather than treating it as automatically complete. Preserve exact pinned revisions from the existing reports. Sizes below are decimal GB and approximate, not runtime memory requirements.

| Group | Upstream | Approximate size | Existing installation destination |
|---|---|---:|---|
| Voice, including speech tokenizer | `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16` on Hugging Face | 2.516 GB | `models/qwen3-tts-base/` |
| MuseTalk v1.5 | `TMElyralab/MuseTalk` on Hugging Face | 3.400 GB | `vendor/musetalk-mac/upstream/models/musetalkV15/` |
| VAE | `stabilityai/sd-vae-ft-mse` on Hugging Face | 0.335 GB | `vendor/musetalk-mac/upstream/models/sd-vae/` |
| Whisper tiny, required by video pipeline | `openai/whisper-tiny` on Hugging Face | 0.156 GB | `vendor/musetalk-mac/upstream/models/whisper/` |
| Face parsing/BiSeNet and ResNet18 | See `reports/face-model-sources.json` | 0.100 GB | `vendor/musetalk-mac/upstream/models/face-parse-bisent/` |
| YuNet | OpenCV Zoo, `face_detection_yunet_2023mar.onnx` | 232,589 bytes | `models/yunet/` |
| Optional transcription | `openai/whisper-small.en` on Hugging Face | 0.971 GB | `models/whisper-small.en/` |

Recurring voice/video weights total approximately 6.5 GB, excluding environments; transcription adds approximately 0.97 GB. FFmpeg is software, not a model.

Primary source references:
- https://github.com/Blaizzy/mlx-audio
- https://github.com/QwenLM/Qwen3-TTS
- https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16
- https://github.com/TMElyralab/MuseTalk
- https://huggingface.co/TMElyralab/MuseTalk
- https://github.com/barnent1/musetalk-mac
- https://huggingface.co/stabilityai/sd-vae-ft-mse
- https://huggingface.co/openai/whisper-tiny
- https://huggingface.co/openai/whisper-small.en
- https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
- https://www.ffmpeg.org/legal.html

Qwen is Apache 2.0; MuseTalk's own code/weights are MIT; FFmpeg's license depends on build options. Verify each support model's redistribution terms individually. Do not claim a blanket MIT/Apache license for the entire bundle. Produce `THIRD_PARTY_NOTICES.md` with source, pinned revision, license reference, and redistribution status per component. Unresolved redistribution rights block that asset's upload, not unrelated code work; document direct upstream acquisition as an alternative.

## Required repository structure

Implement an equivalent clear structure; exact script names below define the proposed CLI contract:

```text
.gitattributes
.gitignore
manifests/models.json
model-store/                 # LFS transport chunks only
scripts/model_manager.py    # lightweight standard-library core
scripts/bootstrap-macos.sh
scripts/publish-preflight.py
patches/                    # complete reproducible upstream modifications
tests/                      # tiny synthetic binary fixtures generated at test time
docs/INSTALL.md
docs/MODEL_PUBLISHING.md
docs/OFFLINE_DEPLOYMENT.md
THIRD_PARTY_NOTICES.md
```

Keep assembled models, virtual environments, download caches, personal inputs, outputs, and temporary files ignored. Ignore nested vendor weights explicitly if vendor source becomes tracked. Do not blindly `git add .`, change permissions globally, remove user files, or push nested vendor Git histories.

Make customized source reproducible by either vendoring a minimal licensed source snapshot without `.git` directories or pinning upstream commits and committing a complete patch/overlay. `git diff` alone misses untracked restored/new files: explicitly include them. Provide a source-only bootstrap and verify it in a clean temporary checkout. An offline bundle must include the resolved source, not require an upstream Git fetch.

## Manifest requirements

Use a versioned JSON schema. Each asset must include:
- Stable asset ID and profile memberships (`voice`, `video`, optional `transcribe`).
- Upstream repository/URL, immutable revision where available, and original relative filename.
- Expected original byte count and SHA-256.
- Safe relative installation path.
- License/provenance reference and redistribution status.
- Ordered chunk list with relative storage path, sequence index, exact size, and SHA-256.
- Packaging format version and configured maximum chunk size.

Separate upstream inventory from actual packaging output. Since weights are absent, chunk hashes do not yet exist: mark assets unprepared and generate chunk metadata only from real verified bytes. Never fabricate hashes or indicate missing chunks are publish-ready.

Version model sets immutably, for example `model-store/<asset-id>/<original-sha256>/part-00000.bin`. Include small configuration/tokenizer files required for offline loading, not only weight binaries. If component source has no immutable URL, the trusted original hash remains mandatory.

## Git LFS packaging and reassembly

1. Default chunk size: **1,000,000,000 bytes**. MuseTalk's 3.4 GB file therefore becomes four transport chunks, each comfortably below a 2 GB hosting limit. These are arbitrary byte chunks, not model-format shards; MuseTalk cannot load them directly.
2. Stream reads, writes, and hashing in bounded buffers (for example 8 MiB). Never load a full model into RAM. No AI framework imports in management commands.
3. Verify the complete source file against its trusted manifest hash before accepting packaging output.
4. Write each chunk and generated metadata transactionally. Interrupted packaging must not appear complete. Identical bytes and chunk size must produce identical names and manifest content.
5. Verify chunk count, ordering, sizes, hashes, and final combined size/hash during restoration. Reject missing, extra/ambiguous, truncated, corrupt, or LFS-pointer text files with actionable errors.
6. Restore to a temporary sibling file, then atomically rename after verification. Do not replace an existing valid model; skip it. For an existing invalid destination, require an explicit repair/replace option and preserve it until replacement is verified.
7. Reject absolute paths, `..`, unsafe symlink traversal, duplicated output paths, and writes outside the selected installation root.
8. Check free space before downloading, packing, or restoring. Calculate staged downloads + LFS local objects + checked-out chunks + assembled files + temporary copies + reserve; account for filesystems separately. Do not assume 6.5 GB of weights needs only 6.5 GB free space.
9. Provide explicit cleanup for temporary/download/transport caches. Print paths and sizes in dry-run first. Never silently run `git lfs prune`, delete original weights, or delete personal media.

Track transport chunks with an appropriately scoped `.gitattributes` rule such as:

```gitattributes
model-store/**/*.bin filter=lfs diff=lfs merge=lfs -text
```

Ensure raw assembled weights cannot accidentally become ordinary Git blobs. LFS setup must use repository-local configuration; do not change the user's global Git settings unnecessarily. Preserve existing remotes, branches, attributes, and unrelated changes.

## CLI and operational workflow

All commands must offer clear help and nonzero exit codes on failure. Management defaults are offline and read-only where practical. Document these proposed commands after implementation:

```bash
# Lightweight status/planning; no model downloads or AI imports
python3 scripts/model_manager.py status
python3 scripts/model_manager.py plan --profile voice,video

# On an explicitly selected online staging machine
python3 scripts/model_manager.py fetch --profile voice,video --allow-network
python3 scripts/model_manager.py pack --profile voice,video --chunk-bytes 1000000000
python3 scripts/model_manager.py verify --transport
python3 scripts/publish-preflight.py

# On target: avoid downloading every LFS object at clone time
GIT_LFS_SKIP_SMUDGE=1 git clone <repository-url>
cd <repository-directory>
# Fetch selected profile chunks using manifest-generated exact LFS include paths
python3 scripts/model_manager.py pull --profile voice,video --allow-network
python3 scripts/model_manager.py restore --profile voice,video
python3 scripts/model_manager.py verify --installed
```

`fetch` obtains pinned upstream assets; `pull` obtains already-published LFS objects. Neither may silently fall back to the other. Support adopting already-local original files to avoid duplicate downloads. Network operations must be explicit; `status`, `plan`, `pack`, `restore`, and `verify` must work without networking.

Repository URL, visibility, owner, branch, hosting plan, staging directory, and target machine are required operational inputs. Ask once for missing inputs when they become necessary; do all independent implementation first. Default a newly proposed repository to private, but do not create it without an explicit destination choice. Never embed tokens in manifests, commands, URLs, or logs.

Before any push, inspect staged contents and enumerate paths/sizes, verify LFS pointers and object availability, check actual per-file limits, and report expected storage/upload volume. Never force-push. Read current GitHub LFS limits/billing documentation rather than assuming unlimited storage. Chunking avoids the per-file ceiling but does not avoid storage/bandwidth quotas or the cost of retaining old model versions.

## Installation and offline operation

- Separate code bootstrap, environment installation, model retrieval, restoration, and inference. None should trigger another expensive phase implicitly.
- Audit historical lockfiles for local paths, wheel compatibility, unavailable packages, and unnecessary MediaPipe dependencies. Preserve historical files; add corrected tested dependency definitions separately.
- Maintain separate voice/video environments where dependency constraints require them. Fix or explicitly exclude the observed MediaPipe wheel metadata issue for the default YuNet workflow. Do not declare dependency checks passed if they fail.
- Add a runtime preflight that checks architecture, Python, FFmpeg/ffprobe, environment availability, required local assets, and actionable missing-file information before importing heavy frameworks.
- Reuse existing local-path loading, offline flags, and macOS network blocking. Missing weights must fail locally, never auto-download.
- For an air-gapped target, prepare an OS/architecture/Python-specific bundle on a connected staging machine: resolved source, verified models/chunks, dependency wheels, required build/runtime artifacts, and appropriate FFmpeg binaries or explicit offline prerequisites. Include hashes and notices. Prove installation using `--no-index` and a local wheelhouse on the matching target. Do not promise one wheelhouse works across operating systems.
- Environment offline flags alone are not proof of network isolation. Verify the OS/network boundary for inference and children; record exactly what was tested.
- Preserve single-job inference, batch size 1, short clips, and explicit cancellation that terminates only the job's own subprocess group. Do not start background services or workers automatically.

## Tests and acceptance criteria

Run lightweight tests with deterministic small binary fixtures; no real models or GPU required:
- Byte-identical pack/restore for empty, tiny, exact chunk-boundary, and multi-chunk files.
- Correct missing/corrupt/truncated/reordered chunk rejection and LFS-pointer detection.
- Original and chunk checksum validation; no final file exposed after failed restoration.
- Existing valid file skip; safe handling of invalid destinations and interrupted operations.
- Path traversal/symlink escape rejection and atomic-write behavior.
- Mocked insufficient disk space; bounded streaming reads; deterministic manifests.
- Correct voice/video/transcription profile dependencies, including required Whisper tiny.
- Offline management commands do not open network connections; network opt-in is enforced.
- Temporary local Git/LFS repository verifies only pointer blobs enter Git and selected chunks round-trip correctly without remote publication.
- Clean source bootstrap preserves all custom MuseTalk fixes, including files omitted by the historical patch.
- Publish preflight blocks raw large Git blobs, missing LFS objects, unprepared manifests, and personal inputs/outputs. Inspect reports individually; do not assume all are safe to publish.

After explicit authorization on a suitable machine, perform full integration acceptance:
1. Fresh checkout with LFS smudging disabled, selected LFS pull, restore, and full hash verification.
2. Install the tested target environment and pass meaningful dependency/import checks.
3. Use synthetic or explicitly supplied test assets, generate one short voice clip and presenter video with network access blocked.
4. Also test the supplied-audio route that skips voice generation.
5. Verify finite/non-silent audio, positive duration, expected streams, full FFmpeg decode, and reasonable A/V duration alignment; inspect sampled frames. Human review is still needed for voice similarity and lip-sync quality.
6. Record machine specifications, elapsed time, memory measurements when available, versions, asset hashes, and exact commands. Do not promise a particular rendering speed.
7. Confirm no orphan inference workers remain and temporary files are cleaned without deleting retained inputs/outputs.

## Required final handoff

Deliver implementation, lightweight tests, manifests, notices, and user-facing install/publish/offline instructions. Summarize:
- What changed and where the entry points are.
- Which tests actually passed.
- Whether any model bytes were downloaded, restored, uploaded, or executed.
- Repository/commit links only if actually created or pushed.
- Remaining inputs or blockers, including destination, redistribution status, quotas, or target-machine validation.

Do not mark this end-to-end deployment complete merely because chunking unit tests pass. Distinguish completed tooling from an actual verified publish/install/render cycle. Keep the user's Mac lightweight throughout the tooling stage.
