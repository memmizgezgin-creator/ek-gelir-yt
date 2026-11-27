#!/usr/bin/env bash
# Kokoro TTS model files (Apache-2.0), about 350 MB, cached between runs.
set -euo pipefail
cd "$(dirname "$0")/../models"
base=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s kokoro-v1.0.onnx ] || curl -fsSL -o kokoro-v1.0.onnx "$base/kokoro-v1.0.onnx"
[ -s voices-v1.0.bin ]  || curl -fsSL -o voices-v1.0.bin  "$base/voices-v1.0.bin"
ls -la
