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

    def catch_up(self, t: float):
        """
        The Mac sends no sound while nothing plays, so this track would run ahead of the meeting's clock (17 Oct: a
        14-minute call's "others" file was 6.8 s long). Before a chunk that began at t seconds into the meeting, write
        the missing time as silence. Returns the piece held from before the gap, to be written as its own piece.
        """
        gap = int((t - self.at) * RATE) - len(self.buf)
        if gap < int(0.3 * RATE):                       # arrival jitter, not a gap
            return None
        held = self.take(force=True)
        self.wav.writeframes(bytes(2 * gap))
        self.at += gap / RATE
        return held

    def take(self, force: bool = False):
        cut = len(self.buf) if force else next_cut(self.buf)
        if not cut:
            return None
        piece, self.buf = self.buf[:cut], self.buf[cut:]
        start = self.at
        self.at += len(piece) / RATE
        return start, piece


class Meeting:
    """
    One recording. A new one is made for every meeting, so the next call can start while the last one is still
    finishing (last words, save, who spoke) in the background. The microphone is shared: a meeting lets go of it
    (`released`) before the next one opens it, and never reads it again after that.
    """

    def __init__(self, app, after: "Meeting | None" = None) -> None:
        self.app = app
        self.after = after                                      # the meeting before this one, maybe still finishing
        self.released = threading.Event()
        self.released.set()                                     # holds no microphone yet
        self.running = False
        self.note = None
        self.started = 0.0
        self.others_ok = False
        self.problem = ""
        self.segments: list[dict] = []
        self.lock = threading.Lock()

    def start(self) -> None:
        if self.after:                                          # it must be done with the shared mic first (~2 s at most)
            self.after.released.wait(10)
        self.app.mic.start()                                    # raises MicProblem: the caller shows it
        self.t0 = time.time()                                   # the meeting's clock: the mic's first sample
        print("meeting: mic =", getattr(self.app.mic, "using", "?"))   # which mic heard you (headphones? D20)
        self.released.clear()
        try:
            self._begin()
        except Exception:
            self.app.mic.stop()                                 # a failed start must not leave the mic running
            self.released.set()
            raise

    def _begin(self) -> None:
        self.sys = SystemAudio()
        self.others_ok = self.sys.start()
        self.problem = "" if self.others_ok else (
            "Recording your microphone only. To hear the other people in a call, allow indite under System "
            "Settings → Privacy & Security → Screen & System Audio Recording, then start again.")
        self.started = time.time()
        self.sys_tried, self.sys_restarts = 0.0, 0
        self.segments = []                                      # else the second meeting in a session keeps the first's lines
        self.note = store.add("…", 0, 0, "meeting", "", kind="meeting", title=time.strftime("Meeting %-d %b, %-I:%M ") + time.strftime("%p").lower(),
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
            self.watch_others()

    def watch_others(self, quiet_for: float = 4.0, every: float = 10.0) -> None:
        """
        macOS sends the call's sound all the time, silence included - until its capture dies. On 16 Oct it died 7 s into
        a 13-minute call (headphones switching into call mode, most likely) and indite never noticed: 6.8 s of "others"
        for 864 s of you. So: an error, or nothing for 4 s, means start the capture again (at most every 10 s); the
        gap is written as silence (Track.catch_up) and the meeting says so.
        """
        if not self.others_ok or not self.running:
            return
        if not (self.sys.error or time.time() - self.sys.last > quiet_for) or time.time() - self.sys_tried < every:
            return
        self.sys_tried = time.time()
        print("meeting: the call's sound stopped" + (f" ({self.sys.error})" if self.sys.error else "") + " - reconnecting")
        fresh = SystemAudio()
        ok = fresh.start()
        with self.lock:
            for at, x in self.sys.stop():                       # whatever the dead capture still held
                self.others(at, x)
            if ok:
                self.sys = fresh
        self.sys_restarts += ok
        self.problem = (f"The call’s sound dropped and was reconnected ({self.sys_restarts}×). A few seconds may be "
                        "missing." if ok else f"Lost the call’s sound: {fresh.error}. Trying again…")
        print("meeting:", "reconnected" if ok else f"could not reconnect ({fresh.error})")
        self.app.refresh()

    def pump(self, force: bool = False) -> None:
        with self.lock:
            if not force:
                if not self.running:                            # stopped: the mic queue may be the next meeting's now
                    return
                while not self.app.mic.q.empty():
                    self.you.feed(self.app.mic.q.get().flatten())
                while not self.sys.q.empty():
                    self.others(*self.sys.q.get())
            for track in (self.them, self.you):                 # others first, so an echo can be spotted
                got = track.take(force)
                if got and quiet(got[1]) > 0.004:               # skip pure silence: the model writes "nan" for it
                    self.write(track.name, *got)

    def others(self, at: float, x: np.ndarray) -> None:
        """One chunk of the Mac's sound, placed on the meeting's clock."""
        held = self.them.catch_up(at - len(x) / RATE - self.t0)
        if held and quiet(held[1]) > 0.004:
            self.write(self.them.name, *held)
        self.them.feed(x)

    def write(self, who: str, start: float, piece: np.ndarray) -> None:
        text = self.app.tidy(self.app.engine.transcribe(piece))
        if not text:
            return
        end = start + len(piece) / RATE
        if who == "You" and any(s["speaker"] == "Others" and s["start"] < end and s["end"] > start
                                and echo(text, s["text"]) for s in self.segments):
            return
        self.segments.append({"start": round(start, 2), "end": round(end, 2), "speaker": who, "text": text,
                              "k": 0 if who == "You" else 1})              # the track it was heard on: 0 you, 1 others
        self.segments.sort(key=lambda s: s["start"])
        self.save()

    def save(self, live: bool = True) -> None:
        body = "\n".join(f"{s['speaker']}: {s['text']}" for s in self.segments) or "…"
        store.update(self.note, text=body, segments=self.segments, seconds=round(time.time() - self.started, 1),
                     live=True if live else None, others=self.others_ok,
                     clock=True)                                # both tracks share one clock: they can play together
        self.app.refresh()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self.app.ai_busy[self.note] = "finishing"               # the row and the Meetings tab show it is still working
        self.app.refresh()
        try:
            mine, theirs = self.app.mic.stop(), self.sys.stop()  # whatever the streams still held: not one sample lost
            self.released.set()                                  # the next meeting may open the mic from here on
            with self.lock:                                      # after any piece the loop is still writing
                self.you.feed(mine)
                for at, x in theirs:
                    self.others(at, x)
            self.pump(force=True)                               # the last words, however short
            for t in (self.you, self.them):
                t.wav.close()
            self.save(live=False)
        finally:
            self.released.set()
            self.app.ai_busy.pop(self.note, None)
            self.app.refresh()
        if not self.segments:
            store.update(self.note, text="(nothing was heard)")
        elif self.app.prefs.get("auto_speakers", True):
            # by default: "Others" split into Person 1, 2...; a mic-only meeting split into Speaker 1, 2...
            self.app.who_spoke(self.note)


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
    import tempfile
    tr = Track("Others", tempfile.mkstemp(suffix=".wav")[1])
    tr.feed(np.full(RATE, 0.2, np.float32))                     # 1 s of sound at 0 s
    assert tr.catch_up(1.1) is None                              # next chunk on time: nothing to fill
    start, held = tr.catch_up(5.0)                               # then 4 s of nothing played
    assert start == 0.0 and len(held) == RATE and tr.at == 5.0   # the held second is written; the clock is at 5 s
    tr.feed(np.full(RATE, 0.2, np.float32))
    assert tr.take(force=True)[0] == 5.0                         # the next words are stamped 5 s, not 1 s
    print("ok")
