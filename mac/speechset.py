"""
Score indite on your own speech (roadmap Mac next #1; plan docs/SPEECH_SET_PLAN.md, final part).

    python mac/speechset.py score        # every dictation you marked "This is exactly what I said"
    python mac/speechset.py --selftest

Each marked note's recording is transcribed again, fresh, through the same steps as a live dictation (engine → tidy →
Mark likely mistakes), and compared with what you said. It runs on a private engine (port 8712, 2 threads, low
priority) so your dictation never waits. Only numbers are printed; the sentences and results stay in
~/Library/Application Support/indite/speechset/ and are never put in docs or commits.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mac"))
sys.path.insert(0, str(ROOT / "bench_synth"))
sys.path.insert(0, str(ROOT))

import review  # noqa: E402
import store   # noqa: E402
from score import edits, normalize  # noqa: E402


def score_one(said: str, text: str, flags: list[dict]) -> dict:
    """Words wrong (strict and with Hinglish spelling/number rules), and whether each flag pointed at a real mistake."""
    ref, hyp = normalize(said), normalize(text)
    strict_ref, strict_hyp = said.lower().split(), text.lower().split()
    want = set(ref)
    right = sum(1 for f in flags if normalize(f["want"]) and set(normalize(f["want"])) <= want)
    return {"words": len(ref), "wrong": edits(ref, hyp), "wrong_strict": edits(strict_ref, strict_hyp),
            "flags": len(flags), "flags_right": right}


def totals(rows: list[dict]) -> dict:
    w = sum(r["words"] for r in rows) or 1
    return {"notes": len(rows), "words": sum(r["words"] for r in rows),
            "words_wrong_pct": round(100 * sum(r["wrong"] for r in rows) / w, 1),
            "words_wrong_strict_pct": round(100 * sum(r["wrong_strict"] for r in rows) / w, 1),
            "false_flags_per_100_words": round(100 * sum(r["flags"] - r["flags_right"] for r in rows) / w, 2),
            "notes_with_a_real_catch": sum(1 for r in rows if r["flags_right"])}


def score() -> None:
    import indite_mac as m
    from indite.core import load_audio
    store.TEST = True                                     # this process only: the engine gets 2 threads
    m.PORT = 8712
    marked = [r for r in store.history() if r.get("said") and store.audio_of(r)]
    if not marked:
        print("No notes marked yet. On Dictations: ⋯ → \"This is exactly what I said\" (after fixing the text).")
        return
    eng = m.Engine()
    if not eng.start_server():
        raise SystemExit("the private engine did not start")
    prefs, table, mine = store.prefs(), m.fixes(), store.my_fixes()
    targets = [want for _, want in mine]

    def tidy(t: str) -> str:                              # the app's tidy(), with your settings
        if prefs["spelling"]:
            t = m.apply_fixes(t, table)
        if prefs["digits"]:
            t = m.numbers.digits(t)
        return store.apply_my_fixes(t, mine)

    rows, t0 = [], time.time()
    try:
        for i, r in enumerate(marked, 1):
            audio, _ = load_audio(store.audio_of(r))
            text = tidy(eng.transcribe(audio))
            flags = review.on_text(text, eng.confidence(audio), targets) if targets else []
            rows.append({"id": r["id"], "said": r["said"], "heard": text, **score_one(r["said"], text, flags)})
            print(f"  {i}/{len(marked)}  {rows[-1]['wrong']}/{rows[-1]['words']} words wrong", flush=True)
    finally:
        eng.stop_server()
    out = {"at": time.strftime("%Y-%m-%d %H:%M"), "dictionary_names": len(targets), **totals(rows), "notes_scored": rows}
    d = store.DIR / "speechset" / "results"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{time.strftime('%Y%m%d-%H%M')}.json"
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print({k: v for k, v in out.items() if k != "notes_scored"}, f"({time.time() - t0:.0f} s)")
    print("details (with your sentences, kept on this Mac):", f)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        r = score_one("Kal Crocin le aana, 2 baje", "kal cross in le aana do baje", [{"want": "Crocin"}, {"want": "Zomato"}])
        assert r["words"] == 6 and r["wrong"] == 2, r          # "cross in" for "Crocin": one swap + one extra word
        assert r["wrong_strict"] > r["wrong"]                   # "2" vs "do", "Kal" vs "kal" only count when strict
        assert (r["flags"], r["flags_right"]) == (2, 1)         # Crocin was said; Zomato was not
        t = totals([r])
        assert t["false_flags_per_100_words"] == round(100 / 6, 2) and t["notes_with_a_real_catch"] == 1
        print("ok")
    elif sys.argv[1:2] == ["score"]:
        score()
    else:
        print(__doc__)
