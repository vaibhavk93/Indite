"""
Who spoke: the phone's recipe (android/.../notes/Speakers.kt), written again for the Mac.

  1.5 s windows of sound (silent ones skipped) -> TitaNet-small voice fingerprints (sherpa-onnx, Apache 2.0;
  the model is CC BY 4.0: credit NVIDIA) -> spherical k-means into k speakers, or a guess of 2-5 when k = 0
  (stops adding speakers once two groups sound alike) -> a little smoothing -> turns.

The phone labels each paragraph with its majority speaker. Here the audio is cut at the speaker changes first and
each turn is transcribed on its own, so a 20 s piece with two people in it becomes two lines, one each.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

RATE = 16_000
WIN, HOP = 1.5, 0.75
MODEL = Path(__file__).resolve().parent / "models/titanet_small.onnx"
_extractor = None


def _fingerprints(audio: np.ndarray) -> tuple[np.ndarray, list[float]]:
    """One unit-length voice fingerprint per 1.5 s window that has sound in it, and where each window starts."""
    global _extractor
    import sherpa_onnx
    if _extractor is None:
        cfg = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(MODEL), num_threads=4)
        _extractor = sherpa_onnx.SpeakerEmbeddingExtractor(cfg)
    w, h = int(WIN * RATE), int(HOP * RATE)
    loud = float(np.sqrt(np.mean(audio ** 2))) or 1e-6
    out, starts = [], []
    for i in range(0, max(1, len(audio) - w + 1), h):
        x = audio[i:i + w]
        if float(np.sqrt(np.mean(x ** 2))) < 0.25 * loud:      # a pause: no voice to fingerprint
            continue
        s = _extractor.create_stream()
        s.accept_waveform(RATE, x)
        s.input_finished()
        e = np.array(_extractor.compute(s), dtype=np.float32)
        out.append(e / (np.linalg.norm(e) or 1))
        starts.append(i / RATE)
    return (np.stack(out) if out else np.zeros((0, 192), np.float32)), starts


def kmeans(e: np.ndarray, k: int, tries: int = 20) -> np.ndarray:
    if len(e) <= k:
        return np.arange(len(e))
    rng = np.random.default_rng(0)
    best, score = None, -np.inf
    for _ in range(tries):
        c = e[rng.choice(len(e), k, replace=False)]
        for _ in range(30):
            lab = np.argmax(e @ c.T, axis=1)
            c = np.stack([e[lab == j].sum(0) if (lab == j).any() else e[rng.integers(len(e))] for j in range(k)])
            c /= np.linalg.norm(c, axis=1, keepdims=True)
        s = float((e * c[lab]).sum())
        if s > score:
            best, score = lab, s
    return best


def guess(e: np.ndarray) -> np.ndarray:
    """2-5 speakers, the phone's rule: stop when a group is tiny or two groups sound alike (cosine gap < 0.35)."""
    pick = np.zeros(len(e), dtype=int)
    for k in range(2, 6):
        if len(e) < k * 4:
            break
        lab = kmeans(e, k)
        if min((lab == j).sum() for j in range(k)) < max(int(5 / HOP), len(e) // 20):
            break
        c = np.stack([e[lab == j].sum(0) for j in range(k)])
        c /= np.linalg.norm(c, axis=1, keepdims=True)
        if min(1 - float(c[a] @ c[b]) for a in range(k) for b in range(a + 1, k)) < 0.35:
            break
        pick = lab
    return pick


def turns(audio: np.ndarray, k: int = 0) -> tuple[list[tuple[float, float, int]], int]:
    """[(start, end, speaker)], speakers numbered by first appearance, and how many were found."""
    e, starts = _fingerprints(audio)
    if len(e) < 2:
        return [(0.0, len(audio) / RATE, 0)], 1
    lab = kmeans(e, k) if k > 0 else guess(e)
    lab = np.array([np.bincount(lab[max(0, i - 1):i + 2]).argmax() for i in range(len(lab))])   # smooth 1-window flips
    order = {v: n for n, v in enumerate(dict.fromkeys(lab.tolist()))}
    out: list[list] = []
    for s, l in zip(starts, lab):
        who, a, b = order[int(l)], s, s + WIN
        if out and out[-1][2] == who and a <= out[-1][1] + 1.0:
            out[-1][1] = b
        elif out and a < out[-1][1]:
            mid = (a + out[-1][1]) / 2                        # overlapping windows of two speakers: meet halfway
            out[-1][1] = mid
            out.append([mid, b, who])
        else:
            out.append([a, b, who])
    end = len(audio) / RATE
    out[0][0], out[-1][1] = 0.0, end                         # nothing before the first or after the last is lost
    for x, y in zip(out, out[1:]):                           # gaps (pauses) go to the earlier speaker
        x[1] = y[0]
    return [tuple(t) for t in out], len(order)


if __name__ == "__main__":       # measured on the two-speaker test dialogue: python mac/speakers.py
    import csv
    import sys
    import wave
    with wave.open(sys.argv[1] if len(sys.argv) > 1 else "bench_synth/dialogue_2spk.wav") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    ref = [r for r in csv.DictReader(open("bench_synth/dialogue_turns.tsv"), delimiter="\t")]
    for k in (0, 2):
        t, n = turns(a, k)
        hit = tot = 0
        names = {}
        for r in ref:
            mid = (float(r["start"]) + float(r["end"])) / 2
            got = next((x[2] for x in t if x[0] <= mid < x[1]), None)
            names.setdefault(got, {}).setdefault(r["speaker"], 0)
            names[got][r["speaker"]] += 1
        hit = sum(max(v.values()) for v in names.values())
        print(f"k={k}: found {n} speakers, {len(t)} turns, {hit}/{len(ref)} reference turns labelled right")
