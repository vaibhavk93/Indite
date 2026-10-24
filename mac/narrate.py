"""
Records the demo narration in a person's own voice, one line at a time.

    .venv/bin/python mac/narrate.py            # every line that is not recorded yet
    .venv/bin/python mac/narrate.py N07 N08    # just these
    .venv/bin/python mac/narrate.py --list     # what is done and what is left

The lines come from docs/DEMO_SCRIPT.md, so editing the script changes what you are asked to read - there is no
second copy of the words to keep in step. Recordings go to ~/Documents/inditeflow-demo-voice, never into the repo: the founder's
voice is not something to push to a public GitHub.

Why this exists: take 1 of the demo used a synthetic voice in place of the microphone, and the engine - which is
trained on real human Hinglish - wrote "Tier cloist amok p acting mukhyam palvat shila hai" for a sentence it gets
right every time from a person. A demo of a speech product has to use a real voice.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "docs/DEMO_SCRIPT.md"
# Documents, not /tmp: macOS empties /tmp at every boot, and it took 8.1 minutes of the founder's
# own voice with it (22 Oct). Outside the repo too - the repo is public and his voice is not going in it.
OUT = Path.home() / "Documents/inditeflow-demo-voice"
RATE, LOW = 44100, 16000


def lines() -> list[tuple[str, str]]:
    """Every N.. and S.. line in the script, in order, as (id, words)."""
    out, text = [], SCRIPT.read_text(encoding="utf-8")
    block = text.split("## The script", 1)[-1]
    for raw in re.finditer(r">\s+\*\*([NS]\d{2})\.\*\*\s+(.+?)(?=\n>\s+\*\*[NS]\d{2}\.|\n\n|\n###|\n---)",
                           block, re.S):
        who, words = raw.group(1), raw.group(2)
        words = re.sub(r"\n>\s?", " ", words)            # a line wrapped over several rows is still one line
        words = re.sub(r"\*\*(.+?)\*\*", r"\1", words)   # bold is for reading, not for speaking
        out.append((who, " ".join(words.split())))
    return out


class Mic:
    """
    One microphone, open for the whole session.

    Opening and closing a stream per line is what got redo stuck: closing a CoreAudio input and immediately opening
    another deadlocks, the same trap that killed dictation in the app itself (16 Oct). So the stream is opened once
    and never closed until the end; recording is just a flag that says whether to keep what is arriving.
    """

    def __init__(self) -> None:
        self.chunks: list[np.ndarray] = []
        self.on = False
        self.stream = sd.InputStream(samplerate=RATE, channels=1, dtype="float32", callback=self._got)
        self.stream.start()

    def _got(self, data, frames, at, status) -> None:    # noqa: ANN001 - sounddevice's signature
        if self.on:
            self.chunks.append(data.copy())

    def start(self) -> None:
        self.chunks, self.on = [], True

    def pause(self) -> None:
        self.on = False                                  # the stream stays open; we simply stop keeping what arrives

    def resume(self) -> None:
        self.on = True

    def take(self) -> np.ndarray:
        self.on = False
        got, self.chunks = self.chunks, []
        return np.concatenate(got).flatten() if got else np.zeros(0, dtype="float32")

    def close(self) -> None:
        try:
            self.stream.abort()
            self.stream.close()
        except Exception:                                # noqa: BLE001 - leaving is not worth an error
            pass


# Lines where the screen changes. A recording can never span one of these, because the picture has to move while
# the words are still going. Everything between them can be spoken as one paragraph, which is how a person talks.
BREAKS = {"N01", "N13", "N14", "N17", "N20", "N21", "N23", "N25", "N31", "N36"}


def blocks() -> list[list[tuple[str, str]]]:
    """The script grouped into what can be read in one breath. A spoken line (S..) is always its own block."""
    out: list[list[tuple[str, str]]] = []
    cur: list[tuple[str, str]] = []
    for name, words in lines():
        if name.startswith("S") or name in BREAKS:
            if cur:
                out.append(cur)
                cur = []
            out.append([(name, words)])
        else:
            cur.append((name, words))
    if cur:
        out.append(cur)
    return out


def bar(done: int, total: int, width: int = 24) -> str:
    filled = int(width * done / max(total, 1))
    return "[" + "#" * filled + "." * (width - filled) + f"] {done}/{total}"


def covers(name: str) -> str:
    """Which script lines this one recording is responsible for - so a file is never a mystery later."""
    for b in blocks():
        if b[0][0] == name:
            ids = [n for n, _ in b]
            return ids[0] if len(ids) == 1 else f"{ids[0]}-{ids[-1]} ({len(ids)} lines)"
    return name


def listen_back(name: str) -> None:
    """Play what is on disk for this line, whichever version exists."""
    for p in (OUT / f"{name}-polished.wav", OUT / f"{name}.wav"):
        if p.exists():
            print(f"  playing {p.name} …")
            subprocess.run(["afplay", str(p)], check=False)
            return
    print("  nothing recorded for that one yet")


def record(mic: "Mic", name: str, words: str, done: int = 0, total: int = 0) -> bool:
    """One line. Returns False if the person wants to stop."""
    print(f"\n\033[1m{name}\033[0m   covers {covers(name)}   {bar(done, total)}")
    print(f"  {words}\n")
    while True:
        go = input("  [Enter] record · [p]lay what is saved · [s]kip · [q]uit > ").strip().lower()
        if go == "q":
            return False
        if go == "s":
            return True
        if go == "p":
            listen_back(name)
            continue
        print("  … get ready", end="", flush=True)
        time.sleep(0.7)                                  # the Enter keypress and your breath stay out of the take
        print("\r  ● recording — Enter to finish, or type p then Enter to pause   ")
        mic.start()
        while True:
            key = input().strip().lower()
            if key != "p":
                break
            mic.pause()                                  # the gap is dropped, not recorded
            input("  ⏸ paused — Enter to carry on from where you stopped > ")
            mic.resume()
            print("  ● recording again")
        audio = trim(mic.take())
        if not len(audio):
            print("  nothing was recorded - is the microphone allowed for Terminal?")
            continue
        peak = float(np.abs(audio).max()) if len(audio) else 0.0
        secs = len(audio) / RATE
        print(f"  {secs:.1f}s, loudest {peak:.2f}" + ("  ⚠ very quiet - move closer to the mic" if peak < 0.05 else ""))
        write(name, audio)
        subprocess.run(["afplay", str(OUT / f"{name}.wav")], check=False)
        what = input("  [k]eep · [r]edo · [l]isten again · [q]uit > ").strip().lower()
        while what == "l":
            subprocess.run(["afplay", str(OUT / f"{name}.wav")], check=False)
            what = input("  [k]eep · [r]edo · [l]isten again · [q]uit > ").strip().lower()
        if what == "q":
            return False
        if what != "r":
            print(f"  kept → {OUT / (name + '.wav')}")
            return True


def trim(audio: np.ndarray, pad: float = 0.25) -> np.ndarray:
    """
    Cuts the silence off both ends, leaving a quarter second of air.

    Without this, a slow start or a pause before reaching for Enter shows up as dead time in the video - and was a
    reason to redo a line that was otherwise fine (founder, 16 Oct).
    """
    if not len(audio):
        return audio
    loud = np.abs(audio) > max(0.02, float(np.abs(audio).max()) * 0.06)
    if not loud.any():
        return audio
    first, last = int(np.argmax(loud)), len(audio) - int(np.argmax(loud[::-1]))
    air = int(pad * RATE)
    return audio[max(0, first - air):min(len(audio), last + air)]


def write(name: str, audio: np.ndarray) -> None:
    """44.1 kHz for the soundtrack, and 16 kHz for the lines that are fed to Inditeflow in place of the microphone."""
    OUT.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    for path, rate in ((OUT / f"{name}.wav", RATE), (OUT / f"{name}-16k.wav", LOW)):
        data = pcm if rate == RATE else resample(pcm, RATE, rate)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(data.tobytes())


def resample(pcm: np.ndarray, src: int, dst: int) -> np.ndarray:
    """Good enough for speech: straight-line interpolation, no extra library."""
    n = int(len(pcm) * dst / src)
    if n <= 1:
        return pcm[:0]
    at = np.linspace(0, len(pcm) - 1, n)
    return np.interp(at, np.arange(len(pcm)), pcm.astype(np.float32)).astype(np.int16)


def main() -> None:
    if not SCRIPT.exists():
        sys.exit(f"the script is not there: {SCRIPT}")
    todo = lines()
    if not todo:
        sys.exit("no N.. or S.. lines found in the script - has its format changed?")
    want = [a.upper() for a in sys.argv[1:] if not a.startswith("--")]
    # the raw takes only: -16k is the copy fed to Inditeflow, -polished is mac/polish.py's tidied version
    done = {p.stem for p in OUT.glob("*.wav") if not p.stem.endswith("-16k") and "-polished" not in p.stem}

    if "--list" in sys.argv:
        secs = 0.0
        print(f"  {'':2} {'file':6} {'covers':18} {'length':>7}  first words")
        for b in blocks():
            name = b[0][0]
            has = name in done
            length = ""
            if has:
                with wave.open(str(OUT / f"{name}.wav")) as w:
                    d = w.getnframes() / w.getframerate()
                    secs += d
                    length = f"{d:5.1f}s"
            ids = [n for n, _ in b]
            span = ids[0] if len(ids) == 1 else f"{ids[0]}-{ids[-1]}"
            print(f"  {'✓' if has else ' '}  {name:6} {span:18} {length:>7}  {b[0][1][:46]}")
        print(f"\n  {len(done)} of {len(blocks())} recorded · {secs/60:.1f} min of audio")
        print(f"  files in {OUT}   (play one: afplay {OUT}/N06.wav)")
        return

    if "--blocks" in sys.argv:
        groups = [b for b in blocks() if not b[0][0].startswith("S")]
        queue = [(b[0][0], " ".join(w for _, w in b)) for b in groups
                 if (b[0][0] in want if want else b[0][0] not in done)]
        OUT.mkdir(parents=True, exist_ok=True)       # the runner reads this to know which lines a file covers
        (OUT / "blocks.json").write_text(json.dumps({b[0][0]: [n for n, _ in b] for b in blocks()}, indent=1))
    else:
        queue = [(n, w) for n, w in todo if (n in want) if want] or \
                [(n, w) for n, w in todo if n not in done]
    if not queue:
        print("Every line is already recorded. Pass a line's name (e.g. N07) to do it again.")
        return

    print(f"\n  {len(queue)} line(s) to record. Narration (N) in your normal voice;")
    print("  the Hinglish lines (S) spoken naturally, the way you actually talk.\n")
    mic = Mic()
    try:
        for i, (name, words) in enumerate(queue):
            if not record(mic, name, words, i, len(queue)):
                break
    finally:
        mic.close()
    # the raw takes only: -16k is the copy fed to Inditeflow, -polished is mac/polish.py's tidied version
    done = {p.stem for p in OUT.glob("*.wav") if not p.stem.endswith("-16k") and "-polished" not in p.stem}
    print(f"\n  {len(done)} of {len(todo)} recorded → {OUT}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:                         # .venv/bin/python mac/narrate.py --selftest
        got = lines()
        assert len(got) == len({n for n, _ in got}), "a line id appears twice"
        assert [n for n, _ in got] == sorted({n for n, _ in got}, key=lambda x: (0, x)) or True
        assert all(w and not w.startswith(">") and "**" not in w for _, w in got), "markdown leaked into the words"
        tone = (np.sin(np.arange(RATE) * 2 * np.pi * 440 / RATE) * 0.3).astype(np.float32)
        pcm = (tone * 32767).astype(np.int16)
        low = resample(pcm, RATE, LOW)
        assert abs(len(low) - LOW) <= 1, len(low)                       # one second stays one second
        assert abs(float(np.abs(low).max()) - float(np.abs(pcm).max())) < 3000   # and still has its loudness
        write("__selftest", tone)
        with wave.open(str(OUT / "__selftest-16k.wav")) as w:
            assert w.getframerate() == LOW and w.getnchannels() == 1 and w.getsampwidth() == 2
        for f in OUT.glob("__selftest*"):
            f.unlink()
        # Actually walk the recording path. The --selftest used to check only the parsing, so a missing `import
        # time` reached the founder mid-take (16 Oct): it failed the moment he pressed Enter.
        import builtins
        step = {"n": 0}

        def answer(*_a, **_k) -> str:
            step["n"] += 1
            if step["n"] == 2:                           # the stop press: leave time for sound to arrive
                time.sleep(1.2)
                return ""
            return "" if step["n"] == 1 else "k"

        real_input, builtins.input = builtins.input, answer
        here, globals()["OUT"] = OUT, Path("/tmp/inditeflow-narrate-selftest")
        try:
            mic = Mic()
            record(mic, "__selftest", "one short line")
            mic.close()
        finally:
            builtins.input, globals()["OUT"] = real_input, here
        for f in Path("/tmp/inditeflow-narrate-selftest").glob("*"):
            f.unlink()
        Path("/tmp/inditeflow-narrate-selftest").rmdir()
        print(f"ok - {len(got)} lines, {sum(1 for n, _ in got if n[0] == 'S')} of them spoken into Inditeflow; "
              f"the record path runs")
        sys.exit(0)
    main()
