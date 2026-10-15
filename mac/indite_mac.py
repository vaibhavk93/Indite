"""
indite for Mac: hold a key anywhere, speak, let go, and the text appears where you were typing.

Everything happens on this Mac. The audio is written to a temporary file, transcribed by whisper.cpp with the same
Hinglish model the phone uses, and deleted. Nothing is sent anywhere.

Measured on an M1 (14 Oct): a 3-8 second utterance comes back in about 1.35 s, so the hold-and-speak interaction
works offline - the phone's 9.6 s is heat and small cores, not the model.

Run it:  .venv/bin/python mac/indite_mac.py
First run asks for two macOS permissions - Microphone, and Accessibility (to type into other apps).
"""

from __future__ import annotations

import math
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import rumps
import sounddevice as sd
from pynput import keyboard

ROOT = Path(__file__).resolve().parent.parent
WHISPER = ROOT / ".tools/whisper.cpp/build/bin/whisper-cli"
MODEL = ROOT / "android/app/src/main/assets/models/ggml-apex-q5_k.bin"
RATE = 16_000

# Hold this to talk. The right-hand Option key is close to the hand and used by almost nothing else.
HOTKEY = keyboard.Key.alt_r

# Spelling the phone applies too, so Mac and phone write the same words. Loaded from the shared list.
SPELLING = ROOT / "android/app/src/main/res/raw/spelling.tsv"


def fixes() -> dict[str, str]:
    """Everyday Hinglish spellings (achha, kyunki, maine…), shared with the phone."""
    out: dict[str, str] = {}
    if SPELLING.exists():
        for line in SPELLING.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] and not parts[0].startswith("#"):
                out[parts[0].lower()] = parts[1]
    return out


def apply_fixes(text: str, table: dict[str, str]) -> str:
    return " ".join(table.get(w.lower(), w) for w in text.split())


def can_listen() -> bool:
    """
    macOS will not hand key events to a program that is not trusted for Accessibility - and pynput does not complain
    when that happens, it simply never fires. So ask first, and say so in words (14 Oct: the first Mac build showed a
    cheerful microphone that did nothing at all).
    """
    try:
        import Quartz
        return bool(Quartz.CGPreflightListenEventAccess())
    except Exception:       # noqa: BLE001 - an old macOS without the call: assume yes and let the hotkey speak for itself
        return True


def ask_to_listen() -> None:
    try:
        import Quartz
        Quartz.CGRequestListenEventAccess()
    except Exception:       # noqa: BLE001
        pass


def window_for(seconds: float) -> int:
    """The same rule as the phone: the window follows the piece, never shorter than the audio (see Pauses.audioCtx)."""
    return min(1280, max(512, int(math.ceil((seconds + 2) * 50 / 256) * 256)))


class Engine:
    """whisper.cpp, one utterance at a time. Serialised, because two at once would fight over the cores."""

    def __init__(self) -> None:
        self.lock = threading.Lock()

    def ready(self) -> str | None:
        if not WHISPER.exists():
            return f"whisper-cli not found at {WHISPER}"
        if not MODEL.exists():
            return f"the speech model is missing at {MODEL}"
        return None

    def transcribe(self, audio: np.ndarray) -> str:
        seconds = len(audio) / RATE
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        try:
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(RATE)
                w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
            with self.lock:
                r = subprocess.run(
                    [str(WHISPER), "-m", str(MODEL), "-f", path, "-ac", str(window_for(seconds)),
                     "-t", "6", "-np", "-nt"],
                    capture_output=True, text=True, timeout=120,
                )
            return " ".join(r.stdout.split())
        finally:
            os.unlink(path)           # the recording never outlives the transcription


class Mic:
    """Records only while the key is held. Nothing is captured before the press or after the release."""

    def __init__(self) -> None:
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: sd.InputStream | None = None

    def start(self) -> None:
        if self.stream:
            return
        self.q = queue.Queue()

        def cb(indata, frames, time_info, status):      # noqa: ANN001 - sounddevice's signature
            self.q.put(indata.copy())

        self.stream = sd.InputStream(samplerate=RATE, channels=1, dtype="float32", callback=cb)
        self.stream.start()

    def stop(self) -> np.ndarray:
        if not self.stream:
            return np.zeros(0, dtype="float32")
        self.stream.stop()
        self.stream.close()
        self.stream = None
        chunks = []
        while not self.q.empty():
            chunks.append(self.q.get())
        return np.concatenate(chunks).flatten() if chunks else np.zeros(0, dtype="float32")


class Typer:
    """
    Puts the text where the cursor is. Typed character by character, so nothing touches the clipboard - the phone's
    floating mic has to use the clipboard and that is its one real privacy cost.
    """

    def __init__(self) -> None:
        self.kb = keyboard.Controller()

    def type(self, text: str) -> None:
        self.kb.type(text + " ")


class InditeApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("indite", title="🎙", quit_button=None)
        self.engine = Engine()
        self.mic = Mic()
        self.typer = Typer()
        self.table = fixes()
        self.busy = False
        self.started_at = 0.0
        self.last = ""
        self.menu = [
            rumps.MenuItem("Hold right-Option and speak" if can_listen()
                           else "⚠ No permission to see the hotkey - click About", callback=None),
            None,
            rumps.MenuItem("Copy last text", callback=self.copy_last),
            rumps.MenuItem("About", callback=self.about),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        problem = self.engine.ready()
        if problem:
            rumps.alert("indite can't start", problem)
            sys.exit(1)
        if not can_listen():
            self.title = "🎙⚠"
            ask_to_listen()
            rumps.alert(
                "indite needs permission to see the hotkey",
                "macOS has not allowed this program to notice key presses, so holding the key will do nothing.\n\n"
                "System Settings → Privacy & Security → Accessibility → + → press ⌘⇧G and paste:\n\n"
                f"{sys.executable}\n\n"
                "Tick it, then quit indite and start it again.",
            )
        threading.Thread(target=self.listen, daemon=True).start()

    # ---- the hotkey ----------------------------------------------------------------------------------------
    def listen(self) -> None:
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key) -> None:                     # noqa: ANN001 - pynput's signature
        if key == HOTKEY and not self.busy and self.started_at == 0.0:
            self.started_at = time.time()
            self.title = "🔴"
            self.mic.start()

    def on_release(self, key) -> None:                   # noqa: ANN001
        if key != HOTKEY or self.started_at == 0.0:
            return
        held = time.time() - self.started_at
        self.started_at = 0.0
        audio = self.mic.stop()
        if held < 0.4 or len(audio) < RATE // 2:          # a tap, not a sentence
            self.title = "🎙"
            return
        self.title = "⏳"
        self.busy = True
        threading.Thread(target=self.write_it, args=(audio,), daemon=True).start()

    # ---- the work ------------------------------------------------------------------------------------------
    def write_it(self, audio: np.ndarray) -> None:
        t0 = time.time()
        try:
            text = apply_fixes(self.engine.transcribe(audio), self.table)
        except Exception as e:                            # noqa: BLE001 - whatever went wrong, say so and carry on
            self.title = "🎙"
            self.busy = False
            rumps.notification("indite", "That didn't work", str(e)[:120])
            return
        self.busy = False
        self.title = "🎙"
        if not text:
            rumps.notification("indite", "Nothing heard", "Hold the key while you speak.")
            return
        self.last = text
        self.typer.type(text)
        print(f"{len(audio) / RATE:.1f}s of speech -> {time.time() - t0:.2f}s -> {text}")

    # ---- menu ----------------------------------------------------------------------------------------------
    def copy_last(self, _) -> None:                      # noqa: ANN001
        if self.last:
            subprocess.run("pbcopy", input=self.last, text=True, check=False)

    def about(self, _) -> None:                          # noqa: ANN001
        rumps.alert(
            "indite for Mac",
            "Hold the right-hand Option key, speak, let go. The text is typed where your cursor is.\n\n"
            "Everything happens on this Mac. The recording is deleted as soon as it has been written out, and "
            "nothing is sent anywhere.",
        )


if __name__ == "__main__":
    InditeApp().run()
