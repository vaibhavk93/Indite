"""Run: uv run python tests/test_core.py   (also works under pytest)"""
import os
import tempfile

import numpy as np

from indite.bench import edits, normalize, score
from indite.core import SR, chunks, load_audio, wav_bytes


def test_scoring():
    assert normalize("Kal, MEETING hai!") == "kal meeting hai"
    assert edits("a b c".split(), "a x c".split()) == 1
    assert edits([], ["a"]) == 1
    s = score("kal meeting hai", "kal meating hai")
    assert (s["word_edits"], s["words"], s["char_edits"]) == (1, 3, 1)


def test_audio_roundtrip():
    tmp = os.path.join(tempfile.mkdtemp(), "tone.wav")
    tone = (0.5 * np.sin(np.linspace(0, 2 * np.pi * 440 * 2, 2 * SR))).astype(np.float32)
    open(tmp, "wb").write(wav_bytes(tone))
    back, damaged = load_audio(tmp)
    assert damaged == 0
    assert abs(len(back) - len(tone)) < 100 and np.abs(back).max() > 0.4
    pieces = list(chunks(np.zeros(60 * SR), 25))
    assert [round(s) for s, _ in pieces] == [0, 25, 50] and len(pieces[-1][1]) == 10 * SR


def test_guards():
    from indite.guards import flag, has_loop

    assert has_loop("haan haan haan theek hai") and has_loop("ok bye ok bye ok bye")
    assert not has_loop("haan haan theek hai")
    segs = [{"start": 0, "end": 5, "text": "kal meeting hai"},
            {"start": 5, "end": 10, "text": "thanks for watching"},
            {"start": 10, "end": 12, "text": ""}]
    flag(segs, speech=[(0.5, 4.5)])
    assert "flags" not in segs[0]
    assert segs[1]["flags"] == ["no_speech", "stock_phrase"]
    assert "flags" not in segs[2]  # empty text is never flagged
    junk = flag([{"start": 0, "end": 2, "text": "nan I am not able to hear you"},
                 {"start": 2, "end": 4, "text": "nana ji ne bola"}], speech=[(0, 4)])
    assert junk[0]["flags"] == ["junk_word"] and "flags" not in junk[1]


def test_styles():
    from indite.styles import _lines, paragraphs, srt, timestamped, vtt

    long = "kal hum log meeting karenge please time pe aa jana budget approve ho gaya hai " * 2
    assert all(len(l) <= 42 for l in _lines(long))
    t = {"segments": [{"start": 0.0, "end": 8.0, "text": long},
                      {"start": 12.0, "end": 14.0, "text": "theek hai", "speaker": "A", "flags": ["repeated"]}]}
    s = srt(t)
    assert s.startswith("1\n00:00:00,000 --> ") and "00:00:14,000" in s
    assert max(len(b.splitlines()) for b in s.strip().split("\n\n")) <= 4  # index + time + 2 lines
    assert vtt(t).startswith("WEBVTT\n\n00:00:00.000 --> ")
    assert "[00:12] A: theek hai  [check: repeating text]" in timestamped(t)
    assert paragraphs(t).count("\n\n") == 1  # 4 s pause -> new paragraph


def test_cut_at_pauses():
    from indite.core import cut_at_pauses

    speech = [(0, 10), (11, 20), (21, 30), (31, 90)]  # pauses at 10, 20, 30; then 59 s without a pause
    pieces = cut_at_pauses(speech, total=100, pad=0)
    assert pieces[0] == (0, 20) and pieces[1] == (21, 30)  # grouped up to 25 s, cut at a pause
    assert all(b - a <= 25 for a, b in pieces) and pieces[-1][1] == 90
    assert cut_at_pauses([], 10) == []


if __name__ == "__main__":
    test_scoring()
    test_audio_roundtrip()
    test_guards()
    test_styles()
    test_cut_at_pauses()
    print("ok")
