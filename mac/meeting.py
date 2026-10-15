"""
Meeting recording: your microphone and what the Mac is playing, as two tracks, turned into text at every pause.

  you    = the microphone          -> lines marked "You"
  others = the Mac's sound output  -> lines marked "Others" (needs Screen & System Audio Recording permission;
                                      without it the meeting is still recorded, mic only, and the window says why)

Text arrives while the meeting goes on, and is saved after every piece, so a crash loses at most the last ~20 s.
Both tracks are also written to disk as they come (Application Support/indite/audio/<id>-you.wav / -others.wav).
"""

from __future__ import annotations

import difflib
import threading
import time
import wave

import numpy as np

import store
from system_audio import SystemAudio

RATE = 16_000
MOST, LEAST = 20.0, 12.0          # a piece is cut at the quietest moment between 12 and 20 s...
EARLY, PAUSE = 6.0, 0.7           # ...or as soon as there is a 0.7 s pause after 6 s of sound


def quiet(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def next_cut(buf: np.ndarray) -> int:
    """Where to cut the front of a growing buffer, or 0 to wait for more. Never drops a sample."""
    n = len(buf) / RATE
    if n >= EARLY:
        tail = buf[-int(PAUSE * RATE):]
        loud = quiet(buf[-int(EARLY * RATE):])
        if loud > 0 and quiet(tail) < 0.12 * loud:      # a real pause, relative to how loud the speaker is
            return len(buf)
    if n < MOST:
        return 0
    frame = int(0.3 * RATE)
    lo, hi = int(LEAST * RATE), int(MOST * RATE)
    q = [quiet(buf[i:i + frame]) for i in range(lo, hi - frame, frame // 3)]
    return lo + int(np.argmin(q)) * (frame // 3) + frame // 2


def echo(mine: str, theirs: str) -> bool:
    """Without headphones the mic also hears the others: the same words twice. Drop the mic's copy."""
    a, b = mine.lower().split(), theirs.lower().split()
    return bool(a and b) and difflib.SequenceMatcher(None, a, b).ratio() > 0.6


class Track:
    def __init__(self, name: str, path) -> None:
        self.name, self.buf, self.at = name, np.zeros(0, dtype=np.float32), 0.0
        self.wav = wave.open(str(path), "wb")
        self.wav.setnchannels(1)
        self.wav.setsampwidth(2)
        self.wav.setframerate(RATE)

    def feed(self, x: np.ndarray) -> None:
        self.buf = np.concatenate([self.buf, x])
        self.wav.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

    def take(self, force: bool = False):
        cut = len(self.buf) if force else next_cut(self.buf)
        if not cut:
            return None
        piece, self.buf = self.buf[:cut], self.buf[cut:]
        start = self.at
        self.at += len(piece) / RATE
        return start, piece


class Meeting:
    def __init__(self, app) -> None:
        self.app = app
        self.running = False
        self.note = None
        self.started = 0.0
        self.others_ok = False
        self.problem = ""
        self.segments: list[dict] = []
        self.lock = threading.Lock()

    def start(self) -> None:
        self.app.mic.start()                                    # raises MicProblem: the caller shows it
        self.sys = SystemAudio()
        self.others_ok = self.sys.start()
        self.problem = "" if self.others_ok else (
            "Recording your microphone only. To hear the other people in a call, allow indite under System "
            "Settings → Privacy & Security → Screen & System Audio Recording, then start again.")
        self.started = time.time()
        self.note = store.add("…", 0, 0, "meeting", "", kind="meeting", title=time.strftime("Meeting %d %b, %H:%M"),
                              segments=[], live=True)
        store.AUDIO.mkdir(parents=True, exist_ok=True)
        self.you = Track("You", store.AUDIO / f"{self.note}-you.wav")
        self.them = Track("Others", store.AUDIO / f"{self.note}-others.wav")
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self) -> None:
        while self.running:
            time.sleep(0.5)
            self.pump()

    def pump(self, force: bool = False) -> None:
        with self.lock:
            while not self.app.mic.q.empty():
                self.you.feed(self.app.mic.q.get().flatten())
            while not self.sys.q.empty():
                self.them.feed(self.sys.q.get())
            for track in (self.them, self.you):                 # others first, so an echo can be spotted
                got = track.take(force)
                if got and quiet(got[1]) > 0.004:               # skip pure silence: the model writes "nan" for it
                    self.write(track.name, *got)

    def write(self, who: str, start: float, piece: np.ndarray) -> None:
        text = self.app.tidy(self.app.engine.transcribe(piece))
        if not text:
            return
        end = start + len(piece) / RATE
        if who == "You" and any(s["speaker"] == "Others" and s["start"] < end and s["end"] > start
                                and echo(text, s["text"]) for s in self.segments):
            return
        self.segments.append({"start": round(start, 2), "end": round(end, 2), "speaker": who, "text": text})
        self.segments.sort(key=lambda s: s["start"])
        self.save()

    def save(self, live: bool = True) -> None:
        body = "\n".join(f"{s['speaker']}: {s['text']}" for s in self.segments) or "…"
        store.update(self.note, text=body, segments=self.segments, seconds=round(time.time() - self.started, 1),
                     live=True if live else None, others=self.others_ok)
        self.app.refresh()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        time.sleep(0.6)                                         # let the loop finish its last pump
        with self.lock:
            self.you.feed(self.app.mic.stop())                  # whatever the streams still held: not one sample lost
            self.them.feed(self.sys.stop())
        self.pump(force=True)                                   # the last words, however short
        for t in (self.you, self.them):
            t.wav.close()
        self.save(live=False)
        if not self.segments:
            store.update(self.note, text="(nothing was heard)")
        elif self.others_ok and any(x["speaker"] == "Others" for x in self.segments):
            self.app.who_spoke(self.note)                       # split "Others" into Person 1, Person 2...


if __name__ == "__main__":       # the cutting rules: python mac/meeting.py
    rng = np.random.default_rng(0)
    talk = rng.normal(0, 0.2, int(7 * RATE)).astype(np.float32)
    assert next_cut(talk) == 0                                  # 7 s of talk, no pause yet: wait
    paused = np.concatenate([talk, np.zeros(int(0.8 * RATE), np.float32)])
    assert next_cut(paused) == len(paused)                      # a pause after 6 s: cut it all
    long = rng.normal(0, 0.2, int(21 * RATE)).astype(np.float32)
    long[int(15 * RATE):int(15.4 * RATE)] = 0
    assert 15 * RATE <= next_cut(long) <= 15.4 * RATE           # 21 s with no pause: cut in the quietest moment
    assert echo("haan done maine invite bhej diya", "Haan done, maine invite bhej diya.")
    print("ok")
