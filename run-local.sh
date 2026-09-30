#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python=.venv/bin/python
case "${1:-}" in
  voice) script=voice.py ;;
  video) script=video.py ;;
  transcribe) script=transcribe.py; python=.venv-video/bin/python ;;
  doctor) exec python3 doctor.py ;;
  *) echo 'Usage: ./run-local.sh {voice|video|transcribe|doctor} [options]'; exit 2 ;;
esac
shift
if [ ! -x "$python" ]; then
  echo 'AI runtime and models were removed to free space. Code and completed outputs are preserved.'
  echo 'Generation requires an explicit reinstall; nothing will be downloaded automatically.'
  exit 1
fi
# Deny networking for inference and its child processes while allowing Metal.
exec /usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' "$python" "$script" "$@"
