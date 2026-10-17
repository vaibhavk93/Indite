"""
When each shown word was spoken, for the Listen view's highlight (founder, 17 Oct: "whichever part is playing should be
highlighted in the text"). The engine's timed words never match the saved text exactly - it was tidied, fixed by the
Dictionary, maybe edited - so the two are lined up word by word; a shown word with no match takes the time of the
nearest matched word before it.
"""

from __future__ import annotations

import difflib
import re


def norm(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())


def align(lines: list[list[str]], timed: list[tuple[str, float, float]], floor: list[float]) -> list[list[float]]:
    """
    lines: the shown words of each line, in order. timed: (word, start, end) from the engine for the same audio.
    floor: each line's own start time (used before the first match). Returns a start time for every shown word.
    """
    flat = [(i, w) for i, ws in enumerate(lines) for w in ws]
    a, b = [norm(w) for _, w in flat], [norm(w) for w, _, _ in timed]
    got: list[float | None] = [None] * len(flat)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            got[blk.a + k] = timed[blk.b + k][1]
    out: list[list[float]] = [[] for _ in lines]
    last = None
    for (i, _), t in zip(flat, got):
        if t is not None and (last is None or t >= last):
            last = t
        elif last is None or last < floor[i]:
            last = floor[i]                                  # nothing matched yet in this line: its own start
        out[i].append(round(last, 2))
    return out


def matched(lines: list[list[str]], timed: list[tuple[str, float, float]]) -> float:
    """How many of the shown words the engine's timed words cover (0-1)."""
    a, b = [norm(w) for ws in lines for w in ws], [norm(w) for w, _, _ in timed]
    hit = sum(blk.size for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
    return hit / len(a) if a else 1.0


def usable(times: list[list[float]]) -> bool:
    """False when too many words share one time (the engine's timestamps bunched up: 10 words at 9.49 s, 17 Oct)."""
    flat = [t for ts in times for t in ts]
    return len(flat) < 4 or len(set(flat)) >= 0.6 * len(flat)


def spread(lines: list[list[str]], starts: list[float], ends: list[float], audio=None, rate: int = 16_000) -> list[list[float]]:
    """
    A fallback when the engine gives no usable times: each line's words spread over that line's span (a line with
    no end: the part of the recording with sound), longer words taking longer. Approximate, but the lit word moves
    with the voice instead of sitting on the first word.
    """
    import numpy as np
    out = []
    for ws, a, b in zip(lines, starts, ends):
        if b <= a and audio is not None and len(audio):
            frame = rate // 10
            n = len(audio) // frame * frame
            loud = np.flatnonzero(np.abs(audio[:n]).reshape(-1, frame).max(axis=1) > 0.02) if n else []
            a, b = (a + loud[0] / 10, a + (loud[-1] + 1) / 10) if len(loud) else (a, a + len(audio) / rate)
        weight = [len(w) + 1 for w in ws]
        total, t = sum(weight) or 1, 0
        out.append([])
        for x in weight:
            out[-1].append(round(float(a + (b - a) * t / total), 2))
            t += x
    return out


if __name__ == "__main__":        # the rules: python mac/wordtimes.py
    timed = [("Haan", 0.1, 0.2), ("chemist", 0.5, 0.7), ("crossin", 2.7, 3.2), ("le", 3.2, 3.3), ("aana", 3.4, 3.6)]
    got = align([["Haan,", "chemist", "Crocin", "le", "aana."]], timed, [0.0])
    assert got == [[0.1, 0.5, 0.5, 3.2, 3.4]], got                  # "Crocin" (fixed by you) borrows the time before it
    two = align([["Haan", "chemist"], ["le", "aana"]], timed, [0.0, 3.0])
    assert two == [[0.1, 0.5], [3.2, 3.4]], two
    assert align([["kuch", "aur"]], [], [5.0]) == [[5.0, 5.0]]       # nothing heard: the line's own start
    assert matched([["Haan,", "chemist", "Crocin"]], timed) == 2 / 3 and matched([["a", "b"]], [("nan", 0, 1)]) == 0
    assert usable([[0.0, 0.3, 0.9, 1.4, 1.4]]) and not usable([[0.0, 0.3, 9.5, 9.5, 9.5, 9.5, 9.5]])
    assert spread([["ab", "cd"]], [2.0], [4.0]) == [[2.0, 3.0]]                 # two equal words: half each
    import numpy as np
    sound = np.concatenate([np.zeros(16_000), np.full(32_000, 0.3), np.zeros(16_000)]).astype(np.float32)
    assert spread([["ab", "cd"]], [0.0], [0.0], sound) == [[1.0, 2.0]]           # only where there is sound
    print("ok")
