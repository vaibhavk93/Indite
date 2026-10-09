#!/bin/sh
# Builds the free local engine: whisper.cpp + Oriserve Hindi2Hinglish-Apex shrunk to 5-bit (~550 MB).
# Needs: Xcode command line tools, git, uv. Takes ~10 min and ~4 GB of downloads. Safe to re-run.
# Add --best to also build the slower, loop-free Prime model (~1 GB more, ~6 GB download).
set -e
cd "$(dirname "$0")/.."
export UV_SYSTEM_CERTS=1  # for networks that inspect HTTPS
UV="${UV:-$HOME/.local/bin/uv}"
mkdir -p .tools/models && cd .tools

[ -d whisper.cpp ] || git clone --depth 1 https://github.com/ggml-org/whisper.cpp
[ -d whisper ] || git clone --depth 1 https://github.com/openai/whisper   # mel filters for the converter
command -v cmake >/dev/null || "$UV" tool install cmake
CMAKE="$(command -v cmake || echo "$HOME/.local/bin/cmake")"
"$CMAKE" -B whisper.cpp/build -S whisper.cpp -DCMAKE_BUILD_TYPE=Release -DWHISPER_BUILD_TESTS=OFF >/dev/null
"$CMAKE" --build whisper.cpp/build -j 4 --config Release --target whisper-cli whisper-quantize >/dev/null

build() {  # $1 = Hugging Face model, $2 = output file
  [ -f "models/$2" ] && return
  PY="$UV run --project .. --with transformers --with huggingface_hub python"  # converter-only deps, not installed in the app
  SNAP=$($PY -c "from huggingface_hub import snapshot_download as d; print(d('$1', allow_patterns=['*.json','*.safetensors','*.txt']))")
  # the weights may be bfloat16, which numpy can't read: convert to float first
  sed -i '' 's/data = list_vars\[src\].squeeze().numpy()/data = list_vars[src].squeeze().float().numpy()/' whisper.cpp/models/convert-h5-to-ggml.py
  $PY whisper.cpp/models/convert-h5-to-ggml.py "$SNAP" ./whisper ./models
  whisper.cpp/build/bin/whisper-quantize models/ggml-model.bin "models/$2" q5_0
  rm models/ggml-model.bin
}
build Oriserve/Whisper-Hindi2Hinglish-Apex ggml-apex-q5_0.bin
[ "$1" = "--best" ] && build Oriserve/Whisper-Hindi2Hinglish-Prime ggml-prime-q5_0.bin
echo "Local engine ready: .tools/models/ggml-apex-q5_0.bin"
