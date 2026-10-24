"""Score engines against hand-typed reference transcripts.

Clips folder layout:  clips/<group>/<name>.<audio ext>  +  clips/<group>/<name>.txt  (Roman script)
Engine outputs are cached in clips/.results/<engine>/ so re-running never re-bills a paid API.
"""
import json
import re
from pathlib import Path

from .core import COST_PER_HOUR, transcribe

AUDIO_EXT = {".wav", ".mp3", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".mp4", ".webm", ".amr", ".aiff", ".mpeg", ".mpg", ".mpga"}


def normalize(text: str) -> str:
    """Lowercase, drop punctuation, collapse spaces. Same rules for reference and engine output."""
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def edits(ref: list, hyp: list) -> int:
    """Levenshtein distance between two token lists."""
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i]
        for j, h in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h)))
        prev = cur
    return prev[-1]


def score(ref: str, hyp: str) -> dict:
    """Word and character edit counts. CER is kinder to Hinglish spelling variants (hai/hain)."""
    r, h = normalize(ref), normalize(hyp)
    return {"word_edits": edits(r.split(), h.split()), "words": len(r.split()),
            "char_edits": edits(list(r.replace(" ", "")), list(h.replace(" ", ""))), "chars": len(r.replace(" ", ""))}


def find_clips(root: Path):
    for audio in sorted(root.rglob("*")):
        if audio.suffix.lower() in AUDIO_EXT and ".results" not in audio.parts:
            ref = audio.with_suffix(".txt")
            if ref.exists():
                yield audio, ref


def run(root: Path, engines: list[str]) -> list[dict]:
    clips = list(find_clips(root))
    if not clips:
        raise SystemExit(f"No clips in {root}. Each audio file needs a .txt reference beside it.")
    rows = []
    for engine in engines:
        cache = root / ".results" / engine
        by_group: dict[str, dict] = {}
        for audio, ref in clips:
            out = cache / audio.relative_to(root).with_suffix(".json")
            if out.exists():
                t = json.loads(out.read_text())
            else:
                t = transcribe(audio, engine).to_dict()
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(t, ensure_ascii=False, indent=2))
            group = audio.relative_to(root).parts[0] if len(audio.relative_to(root).parts) > 1 else "all"
            g = by_group.setdefault(group, {"word_edits": 0, "words": 0, "char_edits": 0, "chars": 0, "audio": 0.0, "elapsed": 0.0, "clips": 0})
            for k, v in score(ref.read_text(), t["text"]).items():
                g[k] += v
            g["audio"] += t["audio_seconds"]
            g["elapsed"] += t["elapsed_seconds"]
            g["clips"] += 1
        for group, g in sorted(by_group.items()):
            rows.append({
                "engine": engine, "group": group, "clips": g["clips"],
                "wer": g["word_edits"] / max(g["words"], 1), "cer": g["char_edits"] / max(g["chars"], 1),
                "speed": g["audio"] / max(g["elapsed"], 1e-9),  # x real-time
                "cost_per_hour": COST_PER_HOUR[engine],
            })
    return rows


def table(rows: list[dict]) -> str:
    lines = [f"{'engine':<13} {'group':<12} {'clips':>5} {'WER':>7} {'CER':>7} {'speed':>8} {'₹/hour':>7}"]
    for r in rows:
        lines.append(f"{r['engine']:<13} {r['group']:<12} {r['clips']:>5} {r['wer']:>7.1%} {r['cer']:>7.1%} "
                     f"{r['speed']:>7.1f}x {r['cost_per_hour']:>7.0f}")
    return "\n".join(lines)
