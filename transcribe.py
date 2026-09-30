"""Transcribe local audio using the installed English Whisper model."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not args.audio.is_file():
        p.error("Audio input must be a local file.")
    import soundfile as sf
    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    torch.set_num_threads(4)
    path = str(ROOT / "models/whisper-small.en")
    processor = WhisperProcessor.from_pretrained(path, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(path, local_files_only=True).eval()
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / "audio.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(args.audio.resolve()),
                        "-ar", "16000", "-ac", "1", str(audio_path)], check=True)
        audio, rate = sf.read(audio_path)
    if len(audio) > 30 * rate:
        p.error("This short-clip transcriber accepts at most 30 seconds.")
    features = processor(audio, sampling_rate=rate, return_tensors="pt").input_features
    with torch.inference_mode():
        ids = model.generate(features, max_new_tokens=220)
    result = {"text": processor.batch_decode(ids, skip_special_tokens=True)[0],
              "model": "openai/whisper-small.en", "audio_seconds": len(audio)/rate}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
