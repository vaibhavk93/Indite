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


if __name__ == "__main__":        # the rules: python mac/wordtimes.py
    timed = [("Haan", 0.1, 0.2), ("chemist", 0.5, 0.7), ("crossin", 2.7, 3.2), ("le", 3.2, 3.3), ("aana", 3.4, 3.6)]
    got = align([["Haan,", "chemist", "Crocin", "le", "aana."]], timed, [0.0])
    assert got == [[0.1, 0.5, 0.5, 3.2, 3.4]], got                  # "Crocin" (fixed by you) borrows the time before it
    two = align([["Haan", "chemist"], ["le", "aana"]], timed, [0.0, 3.0])
    assert two == [[0.1, 0.5], [3.2, 3.4]], two
    assert align([["kuch", "aur"]], [], [5.0]) == [[5.0, 5.0]]       # nothing heard: the line's own start
    print("ok")
