"""Flag text the engine probably invented. Flags only: nothing is ever deleted (VAD can miss singing or whispers).

Flags added to a segment's "flags" list:
  no_speech    - text where the speech detector heard (almost) nothing
  repeated     - a phrase looping 3+ times in a row (a known Whisper failure)
  stock_phrase - a phrase models invent on silence/music ("thanks for watching")
  junk_word    - the model's literal "nan" output (seen at the start of real recordings)
"""
import re

import numpy as np

STOCK_PHRASES = [
    "thanks for watching", "thank you for watching", "please subscribe", "like and subscribe",
    "subscribe to my channel", "subtitles by", "see you in the next video",
]


def speech_ranges(samples: np.ndarray, sr: int) -> list[tuple[float, float]]:
    import torch
    from silero_vad import get_speech_timestamps, load_silero_vad

    ts = get_speech_timestamps(torch.from_numpy(samples), load_silero_vad(), sampling_rate=sr, return_seconds=True)
    return [(t["start"], t["end"]) for t in ts]


def has_loop(text: str, times: int = 3) -> bool:
    """True if any 1-4 word phrase repeats `times` times back to back."""
    w = re.sub(r"[^\w\s]", " ", text.lower()).split()
    for n in range(1, 5):
        for i in range(len(w) - n * times + 1):
            if all(w[i + k * n : i + (k + 1) * n] == w[i : i + n] for k in range(1, times)):
                return True
    return False


def flag(segments: list[dict], speech: list[tuple[float, float]]) -> list[dict]:
    for s in segments:
        text, flags = s["text"].strip(), []
        if not text:
            continue
        dur = max(s["end"] - s["start"], 1e-6)
        heard = sum(max(0.0, min(s["end"], b) - max(s["start"], a)) for a, b in speech)
        if heard < min(0.3, 0.2 * dur):
            flags.append("no_speech")
        if has_loop(text):
            flags.append("repeated")
        if any(p in text.lower() for p in STOCK_PHRASES):
            flags.append("stock_phrase")
        if re.search(r"(?<![\w'])nan(?![\w'])", text.lower()):
            flags.append("junk_word")
        if flags:
            s["flags"] = flags
    return segments
