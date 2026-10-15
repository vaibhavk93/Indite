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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import store              # noqa: E402
from overlay import Pill   # noqa: E402 - needs the path above
from window import Window, front_app   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WHISPER = ROOT / ".tools/whisper.cpp/build/bin/whisper-cli"
SERVER = ROOT / ".tools/whisper.cpp/build/bin/whisper-server"
PORT = 8711                   # localhost only; nothing listens outside this Mac
MODEL = ROOT / "android/app/src/main/assets/models/ggml-apex-q5_k.bin"
RATE = 16_000

# Hold one of these to talk. The right-hand Option key is the default: close to the hand, used by almost nothing
# else. Which one is in force is a setting, and changing it rebinds at once - the listener reads it on every press.
HOTKEYS = {"alt_r": "Right \u2325", "alt_l": "Left \u2325", "cmd_r": "Right \u2318", "ctrl_r": "Right \u2303"}
KEYS = {"alt_r": keyboard.Key.alt_r, "alt_l": keyboard.Key.alt_l,
        "cmd_r": keyboard.Key.cmd_r, "ctrl_r": keyboard.Key.ctrl_r}

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


def mic_allowed() -> bool | None:
    """True, False, or None when macOS will not say (an old system, or the framework is absent)."""
    try:
        import AVFoundation
        status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(AVFoundation.AVMediaTypeAudio)
        return {0: None, 1: False, 2: False, 3: True}.get(int(status))   # notDetermined, restricted, denied, authorized
    except Exception:       # noqa: BLE001
        return None


def ask_mic() -> None:
    """Shows the system prompt the first time; after a refusal only System Settings can change it."""
    try:
        import AVFoundation
        AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
            AVFoundation.AVMediaTypeAudio, lambda granted: None)
    except Exception:       # noqa: BLE001
        pass


def window_for(seconds: float) -> int:
    """The same rule as the phone: the window follows the piece, never shorter than the audio (see Pauses.audioCtx)."""
    return min(1280, max(512, int(math.ceil((seconds + 2) * 50 / 256) * 256)))


class Engine:
    """
    whisper.cpp kept loaded and waiting.

    The first Mac build ran `whisper-cli` per sentence, which reloads the 574 MB model every time - about 0.9 s of
    the 1.4 s a user waits. A small local server keeps the model in memory, so only the transcription is paid for.
    It listens on 127.0.0.1 and nothing else; if it will not start, the per-sentence binary is used instead and the
    app still works, only slower.
    """

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None

    def ready(self) -> str | None:
        if not WHISPER.exists():
            return f"whisper-cli not found at {WHISPER}"
        if not MODEL.exists():
            return f"the speech model is missing at {MODEL}"
        return None

    def start_server(self) -> bool:
        """Starts the resident engine and waits for the model to load. False means we fall back to the binary."""
        if not SERVER.exists():
            return False
        self.proc = subprocess.Popen(
            [str(SERVER), "-m", str(MODEL), "--port", str(PORT), "--host", "127.0.0.1", "-t", "6", "-nt"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(60):                     # the model takes a few seconds to load; wait, do not guess
            time.sleep(0.5)
            if self.proc.poll() is not None:
                return False
            try:
                import urllib.request
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=1)
                return True
            except Exception:                   # noqa: BLE001 - not up yet
                continue
        return False

    def stop_server(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    def _wav(self, audio: np.ndarray) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
        return path

    def transcribe(self, audio: np.ndarray) -> str:
        seconds = len(audio) / RATE
        path = self._wav(audio)
        try:
            with self.lock:
                if self.proc and self.proc.poll() is None:
                    return self._ask_server(path, window_for(seconds))
                r = subprocess.run(
                    [str(WHISPER), "-m", str(MODEL), "-f", path, "-ac", str(window_for(seconds)),
                     "-t", "6", "-np", "-nt"],
                    capture_output=True, text=True, timeout=120,
                )
                return " ".join(r.stdout.split())
        finally:
            os.unlink(path)       # the recording never outlives the transcription

    def _ask_server(self, path: str, audio_ctx: int) -> str:
        """A plain multipart POST, so there is no HTTP library to add."""
        import uuid
        boundary = uuid.uuid4().hex
        with open(path, "rb") as f:
            wav = f.read()
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.wav\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n".encode() + wav +
            f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\ntext\r\n"
            # Without this the server pads every sentence to 30 s and takes 2.2 s instead of 0.5 s (measured 15 Oct).
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio_ctx\"\r\n\r\n{audio_ctx}\r\n"
            f"--{boundary}--\r\n".encode()
        )
        import urllib.request
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/inference", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            return " ".join(r.read().decode("utf-8", "replace").split())


class MicProblem(Exception):
    """The microphone could not be opened, with a reason worth showing someone."""


class Mic:
    """Records only while the key is held. Nothing is captured before the press or after the release."""

    def __init__(self) -> None:
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: sd.InputStream | None = None
        self.level = 0.0
        self.preferred: int | None = None      # the device that worked last time
        self.using = ""

    def start(self) -> None:
        """
        Opens the first microphone that actually opens.

        The default input is whatever macOS last picked, and that is often a Bluetooth headset that is off, or an
        iPhone that is not nearby (15 Oct: default was "Rockerz 255 Pro+" and every press died with PortAudio -9986,
        taking the key handler with it). So: try the default, then the built-in microphone, then anything else, and
        remember what worked. Raises MicProblem with something a person can act on if none of them open.
        """
        if self.stream:
            return
        self.q = queue.Queue()

        def cb(indata, frames, time_info, status):      # noqa: ANN001 - sounddevice's signature
            self.q.put(indata.copy())
            self.level = float(np.sqrt(np.mean(indata ** 2)) * 12)   # rough loudness, 0..1 for the pill

        last = None
        for device in self._candidates():
            try:
                stream = sd.InputStream(samplerate=RATE, channels=1, dtype="float32",
                                        device=device, callback=cb)
                stream.start()
                self.stream = stream
                self.using = sd.query_devices(device if device is not None else sd.default.device[0])["name"]
                return
            except Exception as e:                      # noqa: BLE001 - try the next one, keep the reason
                last = e
        raise MicProblem(str(last))

    def _candidates(self) -> list:
        """The remembered one first, then the default, then the built-in, then every other input."""
        out: list = []
        if self.preferred is not None:
            out.append(self.preferred)
        out.append(None)                                 # None = whatever macOS calls the default
        try:
            devices = sd.query_devices()
            built_in = [i for i, d in enumerate(devices)
                        if d["max_input_channels"] > 0 and "macbook" in d["name"].lower()]
            others = [i for i, d in enumerate(devices) if d["max_input_channels"] > 0 and i not in built_in]
            out += built_in + others
        except Exception:                                # noqa: BLE001 - no list is better than a crash
            pass
        seen, unique = set(), []
        for d in out:
            if d not in seen:
                seen.add(d)
                unique.append(d)
        return unique

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


def focused_is_text() -> bool:
    """
    Is the cursor actually in something that accepts typing?

    macOS can say: it reports the focused element of the front app and its role. If that is a text field, text area,
    search box or combo box, typing lands where the user is looking. If it is a button, a web page with no caret, or
    nothing at all, typed characters go nowhere and the dictation is silently lost - so the text goes to the
    clipboard instead and the pill says so.

    When the question cannot be answered (an app that exposes nothing), the answer is yes: typing is the thing the
    user asked for, and the clipboard is the fallback, not the default.
    """
    try:
        from ApplicationServices import (
            AXUIElementCopyAttributeValue,
            AXUIElementCreateSystemWide,
            kAXFocusedUIElementAttribute,
            kAXRoleAttribute,
        )
        err, element = AXUIElementCopyAttributeValue(
            AXUIElementCreateSystemWide(), kAXFocusedUIElementAttribute, None)
        if err != 0 or element is None:
            return False                      # nothing focused at all: the clipboard is the only sensible place
        err, role = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
        if err != 0 or role is None:
            return True
        return str(role) in {
            "AXTextField", "AXTextArea", "AXComboBox", "AXSearchField", "AXWebArea", "AXStaticText",
        }
    except Exception:                         # noqa: BLE001 - never block a dictation on a permission or API quirk
        return True


class Typer:
    """
    Puts the text where the cursor is. Typed character by character, so nothing touches the clipboard - the phone's
    floating mic has to use the clipboard and that is its one real privacy cost.
    """

    def __init__(self) -> None:
        self.kb = keyboard.Controller()

    def type(self, text: str) -> None:
        self.kb.type(text + " ")

    @staticmethod
    def copy(text: str) -> None:
        """No text field to type into, so the words wait on the clipboard instead of disappearing."""
        subprocess.run("pbcopy", input=text, text=True, check=False)


class InditeApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("indite", title="🎙", quit_button=None)
        self.engine = Engine()
        self.mic = Mic()
        self.typer = Typer()
        self.table = fixes()
        self.prefs = store.prefs()
        self.window: Window | None = None
        self.engine_kind = "Starting the engine\u2026"
        self.busy = False
        self.started_at = 0.0
        self.last = ""
        self.pill = Pill()
        self.done_until = 0.0
        self.done_state = "done"
        # 20 times a second, on the main thread: the only place the pill is ever touched.
        rumps.Timer(self.paint, 0.05).start()
        self.menu = [
            rumps.MenuItem("Hold right-Option and speak" if can_listen()
                           else "⚠ No permission to see the hotkey - click About", callback=None),
            None,
            rumps.MenuItem("Open indite", callback=self.open_window, key="o"),
            rumps.MenuItem("Copy last text", callback=self.copy_last),
            None,
            rumps.MenuItem("Quit", callback=self.quit_all),
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
        threading.Thread(target=self.warm_up, daemon=True).start()

    def warm_up(self) -> None:
        """Load the model now, not when the user is waiting with their finger on the key."""
        self.title = "🎙…"
        ok = self.engine.start_server()
        self.engine_kind = "Fast engine ready." if ok else "Slower engine \u2014 the model reloads each time."
        self.title = "🎙" if can_listen() else "🎙⚠"
        print("resident engine:", "ready" if ok else "not available - using the slower per-sentence path")

    def paint(self, _) -> None:                          # noqa: ANN001 - rumps' signature
        """Shows what is happening, in the place the eye already is: just above the Dock."""
        if self.started_at:
            self.pill.show("listening")
            self.pill.level(self.mic.level)
        elif self.busy:
            self.pill.show("writing")
            self.pill.tick_writing()
        elif time.time() < self.done_until:
            self.pill.show(self.done_state)
        else:
            self.pill.hide()

    # ---- the hotkey ----------------------------------------------------------------------------------------
    def listen(self) -> None:
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def hotkey(self):
        """Read on every press, so changing it in the window works at once and not after a restart."""
        return KEYS.get(self.prefs["hotkey"], keyboard.Key.alt_r)

    def on_press(self, key) -> None:                     # noqa: ANN001 - pynput's signature
        if key == self.hotkey() and not self.busy and self.started_at == 0.0:
            try:
                self.mic.start()
            except Exception as e:                       # noqa: BLE001 - never let this kill the listener
                self.started_at = 0.0
                self.title = "🎙"
                self.mic_trouble(e)
                return
            self.started_at = time.time()
            self.title = "🔴"

    def on_release(self, key) -> None:                   # noqa: ANN001
        if key != self.hotkey() or self.started_at == 0.0:
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

    def mic_trouble(self, err: Exception) -> None:
        """
        A microphone that will not open is either a permission macOS has not granted, or a device that is not there.
        Both are fixable by the user, and neither should be a silent nothing-happens (the lesson from the alarm
        switch, the API key and the hotkey: a thing that cannot work has to say so).
        """
        self.pill.show("error")
        allowed = mic_allowed()
        if allowed is False:
            ask_mic()
            rumps.alert(
                "indite cannot hear the microphone",
                "macOS has not given indite permission to use the microphone.\n\n"
                "System Settings → Privacy & Security → Microphone → turn on indite, then quit and open it again.",
            )
        else:
            rumps.alert(
                "indite could not open any microphone",
                "Tried every input on this Mac and none of them opened.\n\n"
                "The usual cause is a Bluetooth headset that is switched off, or an iPhone microphone that is not "
                f"nearby. Connect a microphone, or turn Bluetooth off, and try again.\n\n({err})",
            )
        threading.Timer(2.0, self.pill.hide).start()

    # ---- the work ------------------------------------------------------------------------------------------
    def write_it(self, audio: np.ndarray) -> None:
        t0 = time.time()
        where = front_app()              # asked before anything is typed, so the history says which app it went to
        try:
            text = self.engine.transcribe(audio)
            if self.prefs["spelling"]:
                text = apply_fixes(text, self.table)
        except Exception as e:                            # noqa: BLE001 - whatever went wrong, say so and carry on
            self.title = "🎙"
            self.busy = False
            self.done_state = "failed"
            self.done_until = time.time() + 2.0
            print("dictation failed:", e)
            return
        self.busy = False
        self.title = "🎙"
        if not text:
            self.done_state = "nothing"
            self.done_until = time.time() + 1.2
            return
        self.last = text
        # The pill says what happened. A notification was tried here and crashed the thread that had just produced
        # the text (rumps needs a bundle identifier it could not find), so the words landed with nothing said.
        mode = self.prefs["output"]
        if mode == "type" or (mode == "smart" and focused_is_text()):
            self.typer.type(text)
            self.done_state = "done"
        else:
            self.typer.copy(text)
            self.done_state = "copied"
        self.done_until = time.time() + 1.6
        took = time.time() - t0
        store.add(text, len(audio) / RATE, took, self.done_state, where)
        if self.window:
            self.window.bridge.push()    # the list grows while it is open, so a dictation shows up as it lands
        print(f"{len(audio) / RATE:.1f}s of speech -> {took:.2f}s -> {text}")

    # ---- menu ----------------------------------------------------------------------------------------------
    def reload_prefs(self) -> None:
        """Called by the window after a setting changes. The prefs are not cached anywhere else."""
        self.prefs = store.prefs()

    def open_window(self, _) -> None:                    # noqa: ANN001
        if self.window is None:                          # built on first use: AppKit, so main thread only
            self.window = Window(self)
        self.window.show()

    def copy_last(self, _) -> None:                      # noqa: ANN001
        if self.last:
            subprocess.run("pbcopy", input=self.last, text=True, check=False)

    def quit_all(self, _) -> None:                       # noqa: ANN001
        self.engine.stop_server()
        rumps.quit_application()


if __name__ == "__main__":
    InditeApp().run()
