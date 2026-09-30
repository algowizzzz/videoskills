# Third-party components

This file records source and license information to verify before redistributing a model bundle. The repository currently distributes code and checksums, not model weights.

| Component | Source | License/status |
|---|---|---|
| Qwen3-TTS base and MLX conversion | https://github.com/QwenLM/Qwen3-TTS and https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16 | Apache 2.0; preserve notices and confirm conversion model card |
| MLX Audio | https://github.com/Blaizzy/mlx-audio | Check pinned source license before bundling |
| MuseTalk v1.5 code/weights | https://github.com/TMElyralab/MuseTalk and https://huggingface.co/TMElyralab/MuseTalk | MIT for MuseTalk's own code and weights; preserve notice |
| MuseTalk Mac port | https://github.com/barnent1/musetalk-mac | Check pinned source license before bundling |
| Stable Diffusion VAE | https://huggingface.co/stabilityai/sd-vae-ft-mse | MIT (model card) |
| Whisper tiny/small.en | https://huggingface.co/openai/whisper-tiny and https://huggingface.co/openai/whisper-small.en | Apache 2.0 (model cards) |
| YuNet | https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet | Apache 2.0 (OpenCV Zoo) |
| Face parsing/BiSeNet | https://github.com/zllrunning/face-parsing.PyTorch | MIT; MuseTalk credits this source; model download URL is recorded in `reports/face-model-sources.json` |
| ResNet18 | https://github.com/pytorch/vision and https://download.pytorch.org/models/resnet18-5c106cde.pth | BSD 3-Clause (torchvision) |
| FFmpeg | https://www.ffmpeg.org/legal.html | LGPL or GPL depending on build/options |

Preserve original license and copyright notices with any redistributed binary bundle. The links above identify the original terms; they do not change those terms.
