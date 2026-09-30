"""Generate speech from a local reference recording using local Qwen weights."""
import argparse
import json
import os
from pathlib import Path
import time
import wave

ROOT = Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
os.environ["HF_HOME"] = str(ROOT / "models/hf-cache")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--transcript", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--output", type=Path, default=ROOT / "outputs/voice.wav")
    p.add_argument("--max-tokens", type=int, default=512)
    args = p.parse_args()
    if not args.reference.is_file():
        p.error("Reference recording must be an existing local file.")
    if not args.text.strip() or not args.transcript.strip():
        p.error("Text and reference transcript must not be empty.")
    import numpy as np
    import mlx.core as mx
    from mlx_audio.tts.utils import load_model
    start = time.monotonic()
    mx.random.seed(42)
    model = load_model(str(ROOT / "models/qwen3-tts-base"))
    chunks, rate = [], None
    for result in model.generate(text=args.text, ref_audio=str(args.reference.resolve()),
                                 ref_text=args.transcript, lang_code="english",
                                 max_tokens=args.max_tokens, verbose=True):
        chunks.append(np.asarray(result.audio).reshape(-1))
        rate = result.sample_rate
    if not chunks:
        raise RuntimeError("The model returned no audio.")
    audio = np.concatenate(chunks)
    if not np.isfinite(audio).all() or np.max(np.abs(audio)) == 0:
        raise RuntimeError("The model returned invalid or silent audio.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(args.output), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    report = {"audio_seconds": len(audio) / rate, "elapsed_seconds": time.monotonic()-start,
              "peak_memory_gb": mx.get_peak_memory()/1e9, "sample_rate": rate,
              "output": str(args.output.resolve())}
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
