#!/bin/sh
# Usage: ./run_local.sh MODEL.bin OUT.tsv clean noisy10 ...   -> TSV "cond/id<TAB>text" for score.py text
W="$(dirname "$0")/../.tools/whisper.cpp/build/bin/whisper-cli"
M=$1; OUT=$2; shift 2; : > "$OUT"
for c in "$@"; do for f in "$(dirname "$0")/$c"/*.wav; do
  t=$("$W" -m "$M" -l en -bs 1 -bo 1 -np -nt -f "$f" 2>/dev/null | tr '\n' ' ')
  printf '%s/%s\t%s\n' "$c" "$(basename "$f" .wav)" "$t" >> "$OUT"
done; done
