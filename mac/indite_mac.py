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
import re
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
import ai                 # noqa: E402
from meeting import Meeting  # noqa: E402
import digits as numbers  # noqa: E402 - mac/digits.py ("numbers" is a stdlib module name)
import store              # noqa: E402
from overlay import Pill, Preview   # noqa: E402 - needs the path above
from window import Activation, Window, front_app   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WHISPER = ROOT / ".tools/whisper.cpp/build/bin/whisper-cli"
SERVER = ROOT / ".tools/whisper.cpp/build/bin/whisper-server"
PORT = 8711                   # localhost only; nothing listens outside this Mac
SNAP_REQUEST = store.DIR / "snapshot.request"   # write a tab name into it; the window saves a picture of itself
HANDS_FREE_CAP = 15 * 60      # seconds; a forgotten hands-free lock stops itself and writes what it heard
CTRL = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
CMD = {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}
WEB_PORT = 8000               # the web app (files, long recordings, editor), also localhost only
MODEL = ROOT / "mac/models/ggml-apex-q5_k.bin"   # the Mac's own copy: a phone model change cannot reach it
RATE = 16_000

# Hold one of these to talk. The right-hand Option key is the default: close to the hand, used by almost nothing
# else. Which one is in force is a setting, and changing it rebinds at once - the listener reads it on every press.
HOTKEYS = {"alt_r": "Right \u2325", "alt_l": "Left \u2325", "cmd_r": "Right \u2318", "ctrl_r": "Right \u2303"}
KEYS = {"alt_r": keyboard.Key.alt_r, "alt_l": keyboard.Key.alt_l,
        "cmd_r": keyboard.Key.cmd_r, "ctrl_r": keyboard.Key.ctrl_r}

# The Mac's own spelling list. Started as a copy of the phone's; the two now change independently.
SPELLING = ROOT / "mac/spelling.tsv"


def fixes() -> dict[str, str]:
    """Everyday Hinglish spellings (achha, kyunki, maine…)."""
    out: dict[str, str] = {}
    if SPELLING.exists():
        for line in SPELLING.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] and not parts[0].startswith("#"):
                out[parts[0].lower()] = parts[1]
    return out


def apply_fixes(text: str, table: dict[str, str]) -> str:
    """
    The spelling list, word by word. A comma or full stop stuck to a word is kept aside first: without that,
    "nahin." never matched "nahin" and the list silently skipped every word at the end of a sentence (measured
    15 Oct: fixing it took the clean set from 19.9% to 18.7% words wrong).
    """
    def one(w: str) -> str:
        m = re.match(r"^(\W*)(.*?)(\W*)$", w)
        return m.group(1) + table.get(m.group(2).lower(), m.group(2)) + m.group(3)
    return " ".join(one(w) for w in text.split())


def junk(text: str, seconds: float) -> bool:
    """
    A tap under a second that came back as noise: "R.", "KKK", a lone letter (seen in the founder's log, 15 Oct).
    Real short words - "OK", "No", "Haan" - are kept.
    """
    t = text.strip(" .,!?")
    return seconds < 1.0 and (len(t) <= 1 or bool(re.fullmatch(r"(\w)\1{2,}", t, re.I)))


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


def pieces(audio: np.ndarray, most: float = 20.0, least: float = 15.0) -> list[np.ndarray]:
    """
    A long hold, cut where the speaker is quietest, into back-to-back pieces of at most `most` seconds.

    Measured 15 Oct: one 62 s hold came back 75% wrong (the window cap clips every 30 s stretch, and it loops),
    against 19% for the same sentences sent one by one. Every sample is kept - nothing between pieces is dropped,
    so a quiet speaker loses no words - and the cut lands in the quietest 0.3 s between `least` and `most` seconds,
    not mid-word. No voice detector: that would mean torch, 19 s to import, in a menu-bar app.
    """
    out, frame = [], int(0.3 * RATE)
    while len(audio) > most * RATE:
        lo, hi = int(least * RATE), int(most * RATE)
        quiet = [float(np.mean(audio[i:i + frame] ** 2)) for i in range(lo, hi - frame, frame // 3)]
        cut = lo + int(np.argmin(quiet)) * (frame // 3) + frame // 2
        out.append(audio[:cut])
        audio = audio[cut:]
    return out + [audio]


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
        # An app that was killed or crashed never ran stop_server, so its engine is still holding 574 MB and the port
        # (15 Oct: three were found). Clear them first, or the new one cannot listen and the old one answers instead.
        subprocess.run(["pkill", "-f", f"whisper-server.*--port {PORT}"], check=False)
        time.sleep(0.3)
        self.proc = subprocess.Popen(
            [str(SERVER), "-m", str(MODEL), "--port", str(PORT), "--host", "127.0.0.1", "-t", "6", "-nt"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # The very first start on a Mac compiles the GPU code for the model: measured 63 s on a fresh copy of the
        # app, 3 s every time after. So wait up to 2 minutes, and say so (engine_kind) instead of looking broken.
        for _ in range(240):
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
        # The model writes "nan" when it hears no speech (15 Oct: a 1.7 s hold typed "nan" into the user's app).
        # A piece that says only that is treated as silence, so the pill says "nothing heard" instead.
        texts = (self._one(p) for p in pieces(audio))
        return " ".join(t for t in texts if t and t.strip(" .").lower() != "nan")

    def _one(self, audio: np.ndarray) -> str:
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
        self.worked = ""                       # name of the mic that opened last time (names survive reconnects)
        self.chosen = ""                       # the mic picked in Settings; "" = automatic
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
        try:                                            # re-read the device list (3 ms), so a headset connected
            sd._terminate()                             # after launch shows up - PortAudio reads it only once
            sd._initialize()
        except Exception:                               # noqa: BLE001
            pass
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
                self.worked = self.using                # remembered by name: positions change after a reconnect
                return
            except Exception as e:                      # noqa: BLE001 - try the next one, keep the reason
                last = e
        raise MicProblem(str(last))

    def _candidates(self) -> list:
        """The one picked in Settings, then the one that worked last, the default, the built-in, then any input."""
        out: list = []
        try:
            devices = sd.query_devices()
            for name in (self.chosen, self.worked):
                out += [i for i, d in enumerate(devices) if name and d["name"] == name and d["max_input_channels"] > 0]
        except Exception:                                # noqa: BLE001
            devices = []
        out.append(None)                                 # None = whatever macOS calls the default
        try:
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


def NSApp_activate() -> None:
    from AppKit import NSApp
    NSApp.activateIgnoringOtherApps_(True)


def mic_names() -> list[str]:
    """Physical inputs for the Settings picker. Virtual ones (Zoom, BlackHole) are left out: they are never a voice."""
    try:
        return [d["name"] for d in sd.query_devices() if d["max_input_channels"] > 0
                and not any(v in d["name"].lower() for v in ("zoomaudio", "blackhole", "teams", "aggregate"))]
    except Exception:                                    # noqa: BLE001
        return []


def chime(name: str) -> None:
    """A short system sound. Off with Settings → Sounds."""
    try:
        from AppKit import NSSound
        s = NSSound.soundNamed_(name)
        if s:
            s.setVolume_(0.35)
            s.play()
    except Exception:                                    # noqa: BLE001
        pass


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


def focused_is_secret() -> bool:
    """
    Is the cursor in a password box? The phone refuses to type into one (Secret.kt), and so does this.

    A password box reports role AXTextField with subrole AXSecureTextField, so the role check above would happily
    type into it. Only the subrole is checked: macOS "secure input" is not used as a signal, because other apps leave
    it on (Terminal's Secure Keyboard Entry, password managers) and it would block every dictation.
    """
    try:
        from ApplicationServices import (
            AXUIElementCopyAttributeValue,
            AXUIElementCreateSystemWide,
            kAXFocusedUIElementAttribute,
            kAXSubroleAttribute,
        )
        err, element = AXUIElementCopyAttributeValue(
            AXUIElementCreateSystemWide(), kAXFocusedUIElementAttribute, None)
        if err != 0 or element is None:
            return False
        err, sub = AXUIElementCopyAttributeValue(element, kAXSubroleAttribute, None)
        return err == 0 and str(sub) == "AXSecureTextField"
    except Exception:                         # noqa: BLE001
        return False


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
        self.mic.chosen = self.prefs["mic"]
        self.window: Window | None = None
        self.engine_kind = "Starting the engine\u2026"
        self.busy = False
        self.started_at = 0.0
        self.locked = False              # hands-free: double-tap the key, then tap once to stop
        self.last_tap = 0.0
        self.taps = 0                    # taps in a row, each within 0.6 s of the last
        self.hf_down = 0.0               # when the hands-free key went down, if it is a different key
        self.held_keys: set = set()
        self.last = ""
        self.web_proc: subprocess.Popen | None = None
        self.meeting = Meeting(self)
        self.meeting_item = rumps.MenuItem("Record a meeting", callback=self.toggle_meeting)
        self.ai_busy: dict = {}
        self.ai_who: dict = {}
        self.ai_keys: dict = {}          # note id -> what the AI is doing for it
        self.ai_error = ""
        self.notice = ""                 # one line for the window: backup done, restore result
        self.job: dict | None = None     # a file being transcribed: name, parts done, parts in all
        self.file_error = ""
        self.pill = Pill()
        self.preview = Preview()
        self.pill.set_glass(self.prefs["pill_glass"])
        self.done_until = 0.0
        self.done_state = "done"
        # 20 times a second, on the main thread: the only place the pill is ever touched.
        rumps.Timer(self.paint, 0.05).start()
        self.menu = [
            rumps.MenuItem(f"Hold {HOTKEYS.get(self.prefs['hotkey'], 'Right ⌥')} and speak" if can_listen()
                           else "⚠ No permission to see the hotkey - click About", callback=None),
            None,
            rumps.MenuItem("Open indite", callback=self.open_window, key="o"),
            rumps.MenuItem("Copy last text", callback=self.copy_last),
            rumps.MenuItem("Edit my word fixes\u2026", callback=self.edit_fixes),
            rumps.MenuItem("Transcribe a file\u2026", callback=self.open_files),
            self.meeting_item,
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
        # Opening the app shows its window, like any Mac app; a timer, so it is built on the main thread once the
        # run loop is going. ponytail: a second `open` while running does nothing; handle reopen if that annoys.
        self._activation = Activation.alloc().initWithApp_(self)
        self._first = rumps.Timer(self._show_on_launch, 0.5)
        self._first.start()

    def _show_on_launch(self, timer) -> None:            # noqa: ANN001
        timer.stop()
        self.open_window(None)
        # Opening indite again (Finder, Spotlight, Dock) only activates the running copy; nothing appeared, so it
        # looked as if it was not running (founder, 15 Oct). Show the window whenever the app is activated.
        from AppKit import NSNotificationCenter
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self._activation, "fire:", "NSApplicationDidBecomeActiveNotification", None)

    def warm_up(self) -> None:
        """Load the model now, not when the user is waiting with their finger on the key."""
        if not self.prefs.get("asked_screen"):           # once: lets the meeting recorder hear the other people
            try:
                import Quartz
                if not Quartz.CGPreflightScreenCaptureAccess():
                    Quartz.CGRequestScreenCaptureAccess()  # macOS shows its own prompt and adds indite to the list
            except Exception:                            # noqa: BLE001
                pass
            store.set_pref("asked_screen", True)
        self.title = "🎙…"
        self.engine_kind = "Starting the engine… the first start on a Mac can take a minute"
        self.refresh()
        ok = self.engine.start_server()
        self.engine_kind = "Fast engine ready." if ok else "Slower engine \u2014 the model reloads each time."
        self.title = "🎙" if can_listen() else "🎙⚠"
        print("resident engine:", "ready" if ok else "not available - using the slower per-sentence path")

    def paint(self, _) -> None:                          # noqa: ANN001 - rumps' signature
        """Shows what is happening, in the place the eye already is: just above the Dock."""
        self.snap_tick = getattr(self, "snap_tick", 0) + 1
        if self.snap_tick % 20 == 0 and SNAP_REQUEST.exists():
            if SNAP_REQUEST.read_text().startswith("preview:"):          # the text card, with this text
                self.preview.snapshot(SNAP_REQUEST)
            elif self.window:
                self.window.snapshot(SNAP_REQUEST)      # a developer's look at the real window (see window.py)
        if self.meeting.running:
            t = int(time.time() - self.meeting.started)
            self.pill.view.label = f"REC {t // 60:02d}:{t % 60:02d}"
            self.pill.show("meeting")
            self.pill.tick_writing()
            return
        if self.started_at:
            if self.locked and time.time() - self.started_at > HANDS_FREE_CAP:
                self.finish()                            # a forgotten lock must not leave the mic on all day
                return
            self.pill.view.locked = self.locked
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
        with keyboard.Listener(on_press=self._press, on_release=self._release) as listener:
            listener.join()

    def _press(self, key) -> None:                       # noqa: ANN001
        self.held_keys.add(key)
        if (key == keyboard.KeyCode.from_char("v") or getattr(key, "char", None) in ("v", "\x16")) \
                and self.held_keys & CTRL and self.held_keys & CMD:
            threading.Thread(target=self.paste_last, daemon=True).start()
        self.on_press(key)

    def _release(self, key) -> None:                     # noqa: ANN001
        self.held_keys.discard(key)
        self.on_release(key)

    def paste_last(self) -> None:
        """
        ⌃⌘V types the last dictation again, where the cursor is (Wispr Flow uses the same keys). Waits for the
        modifiers to come up first, or every typed letter would arrive as ⌃⌘-letter. The password guard applies.
        """
        if not self.last:
            return
        for _ in range(100):                             # up to 2 s
            if not (self.held_keys & (CTRL | CMD)):
                break
            time.sleep(0.02)
        if focused_is_secret():
            self.done_state, self.done_until = "secret", time.time() + 2.0
        elif focused_is_text():
            self.typer.type(self.last)
            self.done_state, self.done_until = "done", time.time() + 1.6
        else:
            self.typer.copy(self.last)
            self.done_state, self.done_until = "copied", time.time() + 1.6

    def hotkey(self):
        """Read on every press, so changing it in the window works at once and not after a restart."""
        return KEYS.get(self.prefs["hotkey"], keyboard.Key.alt_r)

    def hf_key(self):
        return KEYS.get(self.prefs.get("hf_key") or self.prefs["hotkey"], self.hotkey())

    def count_tap(self) -> bool:
        """One more quick tap. True when the run reaches the hands-free count (2 or 3, from Settings)."""
        now = time.time()
        self.taps = self.taps + 1 if now - self.last_tap < 0.6 else 1
        self.last_tap = now
        if self.taps >= int(self.prefs.get("hf_taps", 2)):
            self.taps = 0
            self.last_tap = 0.0
            return True
        return False

    def start_listening(self) -> bool:
        try:
            self.mic.start()
        except Exception as e:                           # noqa: BLE001 - never let this kill the listener
            self.started_at = 0.0
            self.title = "🎙"
            self.mic_trouble(e)
            return False
        self.started_at = time.time()
        self.title = "🔴"
        return True

    def on_press(self, key) -> None:                     # noqa: ANN001 - pynput's signature
        if self.meeting.running:                          # the mic belongs to the meeting until it stops
            return
        if key == keyboard.Key.esc and self.started_at:   # cancel: nothing is written, the audio is dropped
            # ponytail: pynput cannot swallow the key on macOS, so Esc also reaches the app underneath
            self.started_at = 0.0
            self.locked = False
            self.mic.stop()
            self.title = "🎙"
            self.done_state, self.done_until = "cancelled", time.time() + 1.2
            return
        if self.locked and key in (self.hotkey(), self.hf_key()):   # hands-free: one tap of either key stops it
            self.finish()
            return
        if key == self.hf_key() and key != self.hotkey():
            self.hf_down = time.time()                   # a separate hands-free key: counted on release
            return
        if key == self.hotkey() and not self.busy and self.started_at == 0.0:
            if self.start_listening() and self.prefs["sounds"] and time.time() - self.last_tap > 0.6:
                chime("Tink")                            # not again on the second tap of a double-tap

    def on_release(self, key) -> None:                   # noqa: ANN001
        if key == self.hf_key() and key != self.hotkey():
            quick = self.hf_down and time.time() - self.hf_down < 0.4
            self.hf_down = 0.0
            if quick and not self.locked and not self.busy and not self.started_at and self.count_tap():
                if self.start_listening():
                    self.locked = True
                    if self.prefs["sounds"]:
                        chime("Tink")
            return
        if key != self.hotkey() or self.started_at == 0.0 or self.locked:
            return
        if time.time() - self.started_at < 0.4:          # a tap, not a sentence
            if self.hf_key() == self.hotkey() and self.count_tap():
                self.locked = True                       # the last tap of the run: keep listening, hands free
                if self.prefs["sounds"]:
                    chime("Tink")
                return
            self.started_at = 0.0
            self.mic.stop()
            self.title = "🎙"
            return
        self.taps = 0
        self.finish()

    def finish(self) -> None:
        """Stop listening and write what was said. Ends a hold, a hands-free tap, and the hands-free time cap."""
        self.started_at = 0.0
        self.locked = False
        audio = self.mic.stop()
        if self.prefs["sounds"]:
            chime("Pop")
        if len(audio) < RATE // 2:
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
            text = self.tidy(self.engine.transcribe(audio))
            if junk(text, len(audio) / RATE):
                text = ""
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
        if focused_is_secret():          # every mode, "always type" included: never typed, copied or saved
            self.done_state = "secret"
            self.done_until = time.time() + 2.0
            print("password box focused - dictation dropped")
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
        note = store.add(text, len(audio) / RATE, took, self.done_state, where)
        if note and self.prefs["keep_audio"]:            # off by default: a recording of everything said is a lot
            store.AUDIO.mkdir(parents=True, exist_ok=True)
            with wave.open(str(store.AUDIO / f"{note}.wav"), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(RATE)
                w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
        self.refresh()                   # the list grows while it is open, so a dictation shows up as it lands
        if self.prefs["preview"]:
            self.preview.show(text)
        print(f"{len(audio) / RATE:.1f}s of speech -> {took:.2f}s -> {text}")

    # ---- menu ----------------------------------------------------------------------------------------------
    def reload_prefs(self) -> None:
        """Called by the window after a setting changes. The prefs are not cached anywhere else."""
        self.prefs = store.prefs()
        self.mic.chosen = self.prefs["mic"]
        self.pill.set_glass(self.prefs["pill_glass"])

    def open_window(self, _) -> None:                    # noqa: ANN001
        if self.window is None:                          # built on first use: AppKit, so main thread only
            self.window = Window(self)
        self.window.show()

    def edit_fixes(self, _) -> None:                     # noqa: ANN001
        subprocess.run(["open", "-e", str(store.fixes_file())], check=False)

    def open_files(self, _) -> None:                     # noqa: ANN001
        """Pick an audio or video file and transcribe it here (main thread: the open panel is AppKit)."""
        from AppKit import NSOpenPanel
        if self.job:
            rumps.alert("indite is still on another file", f"{self.job['name']} is {self.job['done']} of "
                        f"{self.job['total']} parts in. It will be in Home when it is done.")
            return
        panel = NSOpenPanel.openPanel()
        panel.setTitle_("Transcribe a file")
        panel.setPrompt_("Transcribe")
        panel.setAllowsMultipleSelection_(False)
        NSApp_activate()
        if panel.runModal() == 1 and panel.URLs():
            path = Path(str(panel.URLs()[0].path()))
            threading.Thread(target=self.transcribe_file, args=(path,), daemon=True).start()

    def transcribe_file(self, path: Path) -> None:
        """
        Any audio or video file -> a note in Home, with times for subtitles. Decoded by the same reader the web app
        uses (PyAV, no torch), cut by the same quiet-point rule as a long hold, one piece at a time through the
        engine that is already loaded - so a file needs no second model and no web page. Dictation still works
        while it runs: each piece takes the engine for ~2 s, then lets go.
        """
        sys.path.insert(0, str(ROOT))
        from indite.core import load_audio
        t0 = time.time()
        self.job = {"name": path.name, "done": 0, "total": 0}
        self.refresh()
        try:
            audio, _damaged = load_audio(path)
            parts = pieces(audio)
            self.job["total"] = len(parts)
            segments, at = [], 0.0
            for p in parts:
                text = self.tidy(self.engine.transcribe(p))
                if text:
                    segments.append({"start": round(at, 2), "end": round(at + len(p) / RATE, 2), "text": text})
                at += len(p) / RATE
                self.job["done"] += 1
                self.title = f"📄 {self.job['done']}/{self.job['total']}"
                self.refresh()
            body = "\n\n".join(s["text"] for s in segments)
            if body:
                store.add(body, at, time.time() - t0, "file", "", kind="file", title=path.name,
                          segments=segments, source=str(path))
            print(f"file {path.name}: {at:.0f}s of audio -> {time.time() - t0:.0f}s, {len(segments)} parts")
            self.done_state = "done" if body else "nothing"
        except Exception as e:                           # noqa: BLE001 - say so, keep the app alive
            print("file failed:", path, e)
            self.done_state = "failed"
            self.file_error = f"{path.name}: {e}"
        finally:
            self.job = None
            self.title = "🎙"
            self.done_until = time.time() + 2.0
            self.refresh()

    def ask_ai(self, note_id: str, action: str, extra: str = "") -> None:
        """
        Main thread. The first time, a dialog says plainly that this text leaves the Mac for Claude, through the
        user's own login - the one exception to "nothing leaves this Mac". Then the answer is fetched on a thread.
        """
        from AppKit import NSAlert, NSAlertFirstButtonReturn
        if not self.prefs.get("ai_ok"):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Send this note to an AI?")
            where = ai.PROVIDERS.get(self.prefs["ai_provider"], "Claude")
            alert.setInformativeText_(
                f"AI answers come from: {where}. The note's text leaves this Mac to get the answer; nothing else "
                "does. If the note is about work, check your company's rules first.\n\nYou will not be asked "
                "again; change or turn off AI in Settings → AI.")
            alert.addButtonWithTitle_("Send")
            alert.addButtonWithTitle_("Cancel")
            if alert.runModal() != NSAlertFirstButtonReturn:
                return
            store.set_pref("ai_ok", True)
            self.reload_prefs()
        row = next((r for r in store.history() if r["id"] == note_id), None)
        if not row or note_id in self.ai_busy:
            return
        self.ai_busy[note_id] = ai.ACTIONS[action][0]
        self.refresh()
        threading.Thread(target=self._ai, args=(row, action, extra), daemon=True).start()

    def _ai(self, row: dict, action: str, extra: str) -> None:
        t0 = time.time()
        try:
            answer = ai.run(action, row["text"], extra, self.prefs["ai_provider"], self.prefs["ai_model"])
            if action == "improve":
                store.update(row["id"], improved=answer)          # beside the original, never instead of it
            else:
                label = ai.ACTIONS[action][0] + (f" · {extra}" if extra else "")
                answers = [a for a in row.get("ai", []) if a["label"] != label]
                store.update(row["id"], ai=answers + [{"action": action, "label": label, "text": answer,
                                                       "at": time.time()}])
            print(f"ai {action}: {time.time() - t0:.1f}s")
        except Exception as e:                           # noqa: BLE001 - not logged in, out of quota, offline...
            self.ai_error = str(e)
            print("ai failed:", e)
        finally:
            self.ai_busy.pop(row["id"], None)
            self.refresh()

    def add_tasks(self, note_id: str, answer_label: str) -> None:
        """Every line of an Action items answer becomes its own To do, linked back to the note it came from."""
        row = next((r for r in store.history() if r["id"] == note_id), None)
        found = next((a for a in (row or {}).get("ai", []) if a["label"] == answer_label), None)
        for t in ai.tasks(found["text"]) if found else []:
            store.add(t, 0, 0, "task", "", kind="task", todo="open", source=note_id)
        self.refresh()

    def backup(self) -> None:
        """Main thread: pick where, then write the zip with the scope and audio choice from Settings."""
        from AppKit import NSSavePanel
        panel = NSSavePanel.savePanel()
        panel.setNameFieldStringValue_(time.strftime("indite backup %Y-%m-%d.zip"))
        NSApp_activate()
        if panel.runModal() == 1 and panel.URL():
            n = store.backup(Path(str(panel.URL().path())), self.prefs["backup_scope"], self.prefs["backup_audio"])
            self.notice = f"Backed up {n} note{'s' if n != 1 else ''}."
            self.refresh()

    def restore(self) -> None:
        from AppKit import NSOpenPanel
        panel = NSOpenPanel.openPanel()
        panel.setPrompt_("Restore")
        NSApp_activate()
        if panel.runModal() == 1 and panel.URLs():
            try:
                n = store.restore_zip(Path(str(panel.URLs()[0].path())))
                self.notice = f"Restored {n} note{'s' if n != 1 else ''}." if n else "Nothing new: every note in that backup is already here."
            except Exception as e:                       # noqa: BLE001 - not a backup, damaged, or too new
                self.notice = f"Could not restore: {e}"
            self.refresh()

    def tidy(self, text: str) -> str:
        """Everything after the engine, in one place for dictation and files alike."""
        if self.prefs["spelling"]:
            text = apply_fixes(text, self.table)
        if self.prefs["digits"]:
            text = numbers.digits(text)
        return store.apply_my_fixes(text, store.my_fixes())   # yours last, and even with the others off

    def toggle_meeting(self, _=None) -> None:            # noqa: ANN001
        """Start or stop a meeting recording (main thread)."""
        if self.meeting.running:
            threading.Thread(target=self.meeting.stop, daemon=True).start()
            self.meeting_item.title = "Record a meeting"
            return
        if self.started_at or self.busy:
            return
        try:
            self.meeting.start()
        except Exception as e:                           # noqa: BLE001 - usually no microphone
            self.mic_trouble(e)
            return
        self.meeting_item.title = "Stop the meeting recording"
        self.refresh()

    def who_spoke(self, note_id: str, k: int = 0) -> None:
        """
        Label a file or meeting by voice (mac/speakers.py). The audio is cut where the speaker changes and each turn
        is transcribed again on its own, so a line never mixes two people. In a meeting only the "Others" track is
        split - "You" is already known. Runs on a thread; the note shows that it is working.
        """
        row = next((r for r in store.history() if r["id"] == note_id), None)
        if not row or note_id in self.ai_busy:
            return
        self.ai_busy[note_id] = "finding who spoke"
        self.refresh()
        threading.Thread(target=self._who, args=(row, k), daemon=True).start()

    def _who(self, row: dict, k: int) -> None:
        import speakers
        t0 = time.time()
        try:
            sys.path.insert(0, str(ROOT))
            from indite.core import load_audio
            meet = row.get("kind") == "meeting"
            path = store.AUDIO / f"{row['id']}-others.wav" if meet else store.audio_of(row)
            if not path or not Path(path).exists():
                raise RuntimeError("the audio for this note is not on this Mac any more")
            audio, _ = load_audio(path)
            spans, n = speakers.turns(audio, k)
            label = (lambda i: f"Person {i + 1}") if meet else (lambda i: f"Speaker {i + 1}")
            segs = [s for s in row.get("segments", []) if meet and s.get("speaker") == "You"]
            for a, b, who in spans:
                at = a
                # 0.4 s of lead-in: the cut is found in 0.75 s steps and can land just after a turn's first word
                # (measured: "CleverTap wala" lost its first word without it; no repeated words with it)
                for p in pieces(audio[int(max(0.0, a - 0.4) * RATE):int(b * RATE)]):
                    text = self.tidy(self.engine.transcribe(p)) if float(np.sqrt(np.mean(p ** 2))) > 0.004 else ""
                    if text:
                        segs.append({"start": round(at, 2), "end": round(at + len(p) / RATE, 2),
                                     "speaker": label(who), "text": text})
                    at += len(p) / RATE
            segs.sort(key=lambda s: s["start"])
            names = row.get("names") or {}
            body = "\n".join(f"{names.get(s['speaker'], s['speaker'])}: {s['text']}" for s in segs)
            store.update(row["id"], segments=segs, text=body or row["text"], speakers=n, speakers_guessed=k == 0)
            print(f"speakers: {n} in {time.time() - t0:.0f}s")
        except Exception as e:                           # noqa: BLE001
            self.ai_error = f"Could not tell who spoke: {e}"
            print("speakers failed:", e)
        finally:
            self.ai_busy.pop(row["id"], None)
            self.refresh()

    def check_ai(self, later: bool = False) -> None:
        """Who is signed in to Claude, and which API keys are saved - slow calls, so on a thread, then shown."""
        def go() -> None:
            for _ in range(20 if later else 1):          # after "Sign in…", watch for the login to finish
                if later:
                    time.sleep(3)
                self.ai_who = ai.claude_status()
                self.ai_keys = {p: bool(ai.key_get(p)) for p in ai.PROVIDERS if p != "claude"}
                self.refresh()
                if later and self.ai_who.get("loggedIn"):
                    break
        threading.Thread(target=go, daemon=True).start()

    def refresh(self) -> None:
        """Tell the window something changed. WKWebView must be touched on the main thread only."""
        if self.window:
            from PyObjCTools import AppHelper
            AppHelper.callAfter(self.window.bridge.push)

    def export(self, note_id: str, fmt: str) -> None:
        """Save a note as plain text or as subtitles (.srt), where the user picks (main thread)."""
        from AppKit import NSSavePanel
        row = next((r for r in store.history() if r["id"] == note_id), None)
        if not row:
            return
        sys.path.insert(0, str(ROOT))
        from indite.styles import srt
        name = Path(row.get("title") or "indite note").stem
        if fmt == "srt" and row.get("segments"):
            body, ext = srt({"segments": row["segments"]}), ".srt"
        else:
            body, ext = (row.get("improved") or row["text"]) if fmt == "improved" else row["text"], ".txt"
        panel = NSSavePanel.savePanel()
        panel.setNameFieldStringValue_(name + ext)
        if panel.runModal() == 1 and panel.URL():
            Path(str(panel.URL().path())).write_text(body, encoding="utf-8")

    def copy_last(self, _) -> None:                      # noqa: ANN001
        if self.last:
            subprocess.run("pbcopy", input=self.last, text=True, check=False)

    def quit_all(self, _) -> None:                       # noqa: ANN001
        self.engine.stop_server()
        if self.web_proc and self.web_proc.poll() is None:   # only the web app this app started
            self.web_proc.terminate()
        rumps.quit_application()


if __name__ == "__main__":
    InditeApp().run()
