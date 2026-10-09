"""One whisper-cli run per experiment (model loads once). Usage: python3 run_batch.py MODEL OUT.tsv "EXTRA FLAGS" clean noisy10 ...
Writes TSV "cond/id<TAB>text" for score.py text."""
import json, subprocess, sys
from pathlib import Path
W = Path(__file__).resolve().parent.parent / ".tools/whisper.cpp/build/bin/whisper-cli"
model, out, flags, conds = sys.argv[1], Path(sys.argv[2]), sys.argv[3].split(), sys.argv[4:]
here = Path(__file__).resolve().parent
files = [f for c in conds for f in sorted((here / c).glob("*.wav"))]
cmd = [str(W), "-m", model, "-l", "en", "-np", "-oj", *flags]
for f in files: cmd += ["-f", str(f)]
subprocess.run(cmd, check=True, capture_output=True)
with out.open("w") as o:
    for f in files:
        j = Path(f"{f}.json")
        t = " ".join(s["text"].strip() for s in json.loads(j.read_text(errors="replace"))["transcription"])
        j.unlink()
        o.write(f"{f.parent.name}/{f.stem}\t{t}\n")
