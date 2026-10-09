"""Output styles. Each takes a transcript dict (Transcript.to_dict()) and returns text.

  srt / vtt   - subtitles for creators
  timestamped - "[01:23] Speaker: text" for interviews and calls
  paragraphs  - clean paragraphs for lectures and notes
"""
LINE_CHARS, CUE_LINES = 42, 2  # common subtitle limits
NOTE = {"no_speech": "no speech heard here", "repeated": "repeating text", "stock_phrase": "possibly invented",
        "junk_word": "junk text (nan)"}


def _clock(t: float, sep: str) -> str:
    ms = round(t * 1000)
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02}{sep}{ms % 1000:03}"


def _lines(text: str) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > LINE_CHARS:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur] if cur else lines


def cues(t: dict) -> list[tuple[float, float, list[str]]]:
    """Split segments into cues of at most 2 lines x 42 chars.

    ponytail: a cue's timing is the segment's time shared out by character count, since engines here give
    only segment-level times. Upgrade path: word timestamps from the engine.
    """
    out = []
    for s in t["segments"]:
        lines = _lines(s["text"])
        if not lines:
            continue
        groups = [lines[i : i + CUE_LINES] for i in range(0, len(lines), CUE_LINES)]
        total = sum(len(" ".join(g)) for g in groups)
        start = s["start"]
        for g in groups:
            end = start + (s["end"] - s["start"]) * len(" ".join(g)) / total
            out.append((start, end, g))
            start = end
    return out


def srt(t: dict) -> str:
    return "\n".join(f"{i}\n{_clock(a, ',')} --> {_clock(b, ',')}\n" + "\n".join(g) + "\n"
                     for i, (a, b, g) in enumerate(cues(t), 1))


def vtt(t: dict) -> str:
    return "WEBVTT\n\n" + "\n".join(f"{_clock(a, '.')} --> {_clock(b, '.')}\n" + "\n".join(g) + "\n"
                                    for a, b, g in cues(t))


def timestamped(t: dict) -> str:
    out = []
    for s in t["segments"]:
        if not s["text"].strip():
            continue
        m, sec = divmod(int(s["start"]), 60)
        who = f"{s['speaker']}: " if s.get("speaker") else ""
        check = f"  [check: {', '.join(NOTE.get(f, f) for f in s['flags'])}]" if s.get("flags") else ""
        out.append(f"[{m:02}:{sec:02}] {who}{s['text'].strip()}{check}")
    return "\n".join(out) + "\n"


def paragraphs(t: dict, pause: float = 2.0, max_words: int = 120) -> str:
    """New paragraph after a pause of 2 s or about 120 words."""
    paras, cur, prev_end = [], [], None
    for s in t["segments"]:
        text = s["text"].strip()
        if not text:
            continue
        if cur and (s["start"] - prev_end > pause or sum(len(x.split()) for x in cur) >= max_words):
            paras.append(" ".join(cur))
            cur = []
        cur.append(text)
        prev_end = s["end"]
    return "\n\n".join(paras + [" ".join(cur)] if cur else paras) + "\n"


STYLES = {"srt": (srt, ".srt"), "vtt": (vtt, ".vtt"), "timestamped": (timestamped, ".txt"), "paragraphs": (paragraphs, ".txt")}
