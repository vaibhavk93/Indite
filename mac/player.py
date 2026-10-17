"""
Play a note's recording inside indite (founder, 17 Oct: "there is no UI while it plays"). Design: docs/PLAYER_PLAN.md.

The window's page can only read files in mac/ui/, so the sound is played here with Apple's AVAudioPlayer and the page
is told the time a few times a second; it lights up the line being spoken. One recording at a time. A meeting has two
tracks (you, others) that do not share a clock yet, so one track plays at a time.
"""

from __future__ import annotations

import tempfile
import wave
from pathlib import Path

import numpy as np


class Player:
    def __init__(self) -> None:
        self.p = None                  # the AVAudioPlayer, or None
        self.note = ""                 # which note is loaded
        self.track = 0                 # which of the note's files (a meeting: 0 = you, 1 = others)
        self.tmp: Path | None = None   # a converted copy, for formats AVAudioPlayer cannot read
        self.vol = 1.0                 # kept across loads (tests run silent)

    def load(self, note: str, path: Path, track: int = 0) -> float:
        """Loads a recording, paused at the start. Returns its length in seconds; raises if it cannot be played."""
        from AVFoundation import AVAudioPlayer
        from Foundation import NSURL
        self.stop()
        p, _err = AVAudioPlayer.alloc().initWithContentsOfURL_error_(NSURL.fileURLWithPath_(str(path)), None)
        if p is None:                  # .ogg / .opus from WhatsApp, odd video files: decode once to a wav
            p = AVAudioPlayer.alloc().initWithContentsOfURL_error_(NSURL.fileURLWithPath_(str(self._wav(path))), None)[0]
        if p is None:
            raise RuntimeError("this recording cannot be played")
        p.setEnableRate_(True)
        p.setVolume_(self.vol)
        p.prepareToPlay()
        self.p, self.note, self.track = p, note, track
        return float(p.duration())

    def _wav(self, path: Path) -> Path:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from indite.core import load_audio
        audio, _ = load_audio(path)
        f = Path(tempfile.mkstemp(suffix=".wav", prefix="indite-play-")[1])
        with wave.open(str(f), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16_000)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
        self.tmp = f
        return f

    def play(self) -> None:
        if self.p:
            self.p.play()

    def pause(self) -> None:
        if self.p:
            self.p.pause()

    def seek(self, t: float) -> None:
        if self.p:
            self.p.setCurrentTime_(max(0.0, min(float(t), float(self.p.duration()))))

    def rate(self, r: float) -> None:
        if self.p:
            self.p.setRate_(float(r))

    def stop(self) -> None:
        if self.p:
            self.p.stop()
        self.p, self.note = None, ""
        if self.tmp:
            self.tmp.unlink(missing_ok=True)
            self.tmp = None

    def state(self) -> dict:
        """What the page needs a few times a second."""
        if not self.p:
            return {"note": "", "playing": False, "t": 0.0, "dur": 0.0}
        return {"note": self.note, "track": self.track, "playing": bool(self.p.isPlaying()),
                "t": round(float(self.p.currentTime()), 2), "dur": round(float(self.p.duration()), 2),
                "rate": round(float(self.p.rate()), 2)}


if __name__ == "__main__":        # the player on a made-up tone: python mac/player.py
    f = Path(tempfile.mkstemp(suffix=".wav")[1])
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16_000)
        w.writeframes((np.sin(np.arange(3 * 16_000) / 16_000 * 2 * np.pi * 440) * 3000).astype(np.int16).tobytes())
    pl = Player()
    assert abs(pl.load("n1", f) - 3.0) < 0.05
    pl.seek(1.5)
    assert abs(pl.state()["t"] - 1.5) < 0.05 and not pl.state()["playing"]
    pl.rate(1.5)
    pl.seek(99)
    assert abs(pl.state()["t"] - 3.0) < 0.05                    # never past the end
    pl.stop()
    assert pl.state()["note"] == ""
    f.unlink()
    print("ok")
