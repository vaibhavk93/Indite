"""Sarvam cloud on bench_synth/clean (synthetic audio only). Run from repo root:
uv run --env-file .env python bench_synth/run_sarvam.py > bench_synth/out/hyp_sarvam.tsv"""
import sys
from pathlib import Path
from indite.core import load_audio, sarvam

for f in sorted(Path(__file__).parent.glob("clean/*.wav")):
    samples, _ = load_audio(f)
    text = " ".join(s["text"] for s in sarvam(samples))
    print(f"clean/{f.stem}\t{text}", flush=True)
    print(f.stem, file=sys.stderr)
