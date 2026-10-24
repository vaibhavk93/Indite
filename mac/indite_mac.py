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

import json
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
# Set before PortAudio loads: it prints AUHAL warnings of its own even when the microphone is fine, and they hide
# ours. Done here rather than in the launcher because anything inside the .app bundle breaks its signature, and a
# broken signature is what costs the Accessibility permission (22 Oct, four times over).
os.environ.setdefault("PA_SUPPRESS_STARTUP_MESSAGES", "1")


def _rotate_log() -> None:
    """Keep the log under 5 MB, with one old copy. It is the only record there is of a crash."""
    try:
        log = Path.home() / "Library/Logs/indite-mac.log"
        if log.exists() and log.stat().st_size > 5_000_000:
            log.replace(log.with_suffix(".log.1"))
    except Exception:                                    # noqa: BLE001 - a log that will not rotate is not fatal
        pass


_rotate_log()

import sounddevice as sd
from pynput import keyboard


def _layout_on_main_thread() -> None:
    """
    pynput reads the keyboard layout (TIS... calls) from its listener thread; on macOS 26 those calls must run on the
    main thread, and off it macOS kills the whole app (SIGTRAP in dispatch_assert_queue, 15 Oct - it crashed the
    moment key access was finally granted). Read it once here, on the main thread, and hand pynput that copy.
    """
    import contextlib
    from pynput._util import darwin as util
    from pynput.keyboard import _darwin as kb
    with util.keycode_context() as ctx:
        pass
    # ponytail: a layout switched after start-up isn't seen; the hotkeys are modifier keys, so it doesn't matter
    util.keycode_context = kb.keycode_context = contextlib.contextmanager(lambda: (yield ctx))


_layout_on_main_thread()


def _skip_media_keys() -> None:
    """
    Volume, brightness and play/pause keys arrive as "system defined" events, and pynput turns each into an AppKit
    NSEvent on its listener thread (keyboard/_darwin.py:303). On macOS 26 that off-main-thread AppKit call aborts the
    whole app (18 Oct: indite died mid-morning; the crash stack ended on that line). indite never uses those keys, so
    they are dropped before pynput looks at them. The hotkeys are ordinary key and modifier events, untouched.
    """
    from pynput.keyboard import _darwin as kb
    system_defined = getattr(kb, "NSSystemDefined", 14)
    handle = kb.Listener._handle_message

    def handle_except_media(self, proxy, event_type, event, refcon, injected):
        if event_type == system_defined:
            return
        return handle(self, proxy, event_type, event, refcon, injected)
    kb.Listener._handle_message = handle_except_media


_skip_media_keys()

# A crash inside macOS code kills Python with no word in the log (15 Oct: it looked like a permission problem for
# hours). This writes the Python stack of every thread into the log first. SIGTRAP is what macOS's own checks raise.
import faulthandler   # noqa: E402
import signal         # noqa: E402
faulthandler.enable(all_threads=True)
faulthandler.register(signal.SIGTRAP, all_threads=True, chain=True)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai                 # noqa: E402
from meeting import Meeting  # noqa: E402
import digits as numbers  # noqa: E402 - mac/digits.py ("numbers" is a stdlib module name)
import store              # noqa: E402
from overlay import Pill, Preview   # noqa: E402 - needs the path above
from player import Player           # noqa: E402
from window import Activation, Window, front_app, front_pid   # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WHISPER = ROOT / ".tools/whisper.cpp/build/bin/whisper-cli"
SERVER = ROOT / ".tools/whisper.cpp/build/bin/whisper-server"
PORT = 8712 if store.TEST else 8711   # localhost only; the test copy has its own engine
DEMO_FEED = store.DIR / "demo_feed.wav"          # demo video only (mac/demo.py)
DEMO_CMD = store.DIR / "demo.cmd"                 # demo video only: one instruction per line for the window
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
        word, new = m.group(2), table.get(m.group(2).lower(), m.group(2))
        if word[:1].isupper() and new[:1].islower():     # "Thik hai" stays capitalised: "Theek hai", not "theek hai"
            new = new[:1].upper() + new[1:]
        return m.group(1) + new + m.group(3)
    return " ".join(one(w) for w in text.split())


def junk(text: str, seconds: float) -> bool:
    """
    A tap under a second that came back as noise: "R.", "KKK", a lone letter (seen in the founder's log, 15 Oct).
    Real short words - "OK", "No", "Haan" - are kept.
    """
    t = text.strip(" .,!?")
    return seconds < 1.0 and (len(t) <= 1 or bool(re.fullmatch(r"(\w)\1{2,}", t, re.I)))


def signature_broken() -> str:
    """
    "" when the app's own signature still holds, otherwise what broke it, in one line.

    macOS judges indite by its signature before trusting it with the keyboard. The app used to break its own
    signature every time it ran: Python writes .pyc files beside the modules it imports, and its interpreter lives
    inside the bundle (16 Oct: 249 of them, and Accessibility switched itself off mid-session). That is fixed with
    PYTHONDONTWRITEBYTECODE, but anything else that writes into the bundle would do the same, silently - so the app
    checks itself at start-up rather than waiting for the keyboard to go dead.
    """
    bundle = Path(sys.executable).resolve()
    while bundle.parent != bundle and bundle.suffix != ".app":
        bundle = bundle.parent
    if bundle.suffix != ".app":
        return ""                                        # not running from a bundle (a developer run): nothing to check
    try:
        r = subprocess.run(["codesign", "--verify", "--strict", str(bundle)],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return ""
        first = next((l for l in (r.stderr or "").splitlines() if l.strip()), "the signature no longer matches")
        return first.replace(str(bundle), "the app")[:200]
    except Exception as e:                               # noqa: BLE001 - a check that fails is not a verdict
        print("could not check the signature:", e)
        return ""


def can_listen() -> bool:
    """
    macOS will not hand key events to a program that is not trusted for Accessibility - and pynput does not complain
    when that happens, it simply never fires. So ask first, and say so in words (14 Oct: the first Mac build showed a
    cheerful microphone that did nothing at all). Accessibility, not Input Monitoring (CGPreflightListenEventAccess):
    15 Oct the hotkey worked with Input Monitoring off, and checking that list showed a false warning for hours.
    """
    try:
        import ApplicationServices
        return bool(ApplicationServices.AXIsProcessTrusted())
    except Exception:       # noqa: BLE001 - an old macOS without the call: assume yes and let the hotkey speak for itself
        return True


def ask_to_listen() -> None:
    try:
        import ApplicationServices as AS
        AS.AXIsProcessTrustedWithOptions({AS.kAXTrustedCheckOptionPrompt: True})   # macOS's own "allow" prompt
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
            [str(SERVER), "-m", str(MODEL), "--port", str(PORT), "--host", "127.0.0.1", "-t", "2" if store.TEST else "6", "-nt"],
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

    def confidence(self, audio: np.ndarray) -> list[tuple[str, float]]:
        """
        Every word with how sure the engine was, for the offline review of a dictation (roadmap Mac 5/7).

        NOT used on the live path, and that is the whole point of measuring it: asking the server for the detail
        costs about 600 ms on a four-second clip - 0.8 s became 1.4 s, measured 16 Oct on this Mac - and the speed
        of a dictation is the thing indite is actually good at. So the words are fetched when something wants to
        look at them, not on every press.

        The signal itself is strong. On the founder's own recording of "CleverTap", which the engine gets wrong:
        C 0.35, le 0.32, var 0.14 - and every word it got right scored 1.00.
        """
        out: list[tuple[str, float]] = []
        for piece in pieces(audio):
            path = self._wav(piece)
            try:
                with self.lock:
                    if not (self.proc and self.proc.poll() is None):
                        return out                       # no resident server: the slow binary has no word detail
                    raw = self._ask_server(path, window_for(len(piece) / RATE), detail=True)
                for seg in json.loads(raw).get("segments", []):
                    for w in seg.get("words") or []:
                        # the server sends word PIECES (" chem" + "ist"): a leading space starts a word, no space joins
                        # the one before. A word is only as sure as its least sure piece.
                        piece, p = w.get("word") or "", float(w.get("probability", 1.0))
                        if not piece.strip():
                            continue
                        if piece.startswith(" ") or not out:
                            out.append((piece.strip(), p))
                        else:
                            out[-1] = (out[-1][0] + piece.strip(), min(out[-1][1], p))
            finally:
                os.unlink(path)
        return out

    def word_times(self, audio: np.ndarray) -> list[tuple[str, float, float]]:
        """
        Every word with when it was spoken (seconds from the start), for the Listen view's highlight. Needs the FULL
        listening window and timestamps on: with the short window the dictation path uses, every word after ~4 s got
        the same time (measured 17 Oct). About 4 s per piece of up to 20 s, so it runs once and is kept on the note.
        """
        out: list[tuple[str, float, float]] = []
        at = 0.0
        for piece in pieces(audio):
            got = self._timed(piece, 0.0)
            if not got and float(np.sqrt(np.mean(piece ** 2))) > 0.004:
                # with timestamps on, this model sometimes answers just "nan" (17 Oct: a 9.5 s dictation); half a
                # second of silence in front gets a real answer
                got = self._timed(np.concatenate([np.zeros(RATE // 2, np.float32), piece]), 0.5)
            if got is None:                                  # the engine is not running
                return out
            out += [(w, at + a, at + b) for w, a, b in got]
            at += len(piece) / RATE
        return out

    def _timed(self, piece: np.ndarray, lead: float) -> list[tuple[str, float, float]] | None:
        """One piece's words with times (minus `lead` seconds of added silence); [] for a junk answer."""
        path = self._wav(piece)
        try:
            with self.lock:
                if not (self.proc and self.proc.poll() is None):
                    return None
                raw = self._ask_server(path, 0, detail=True, times=True)
        finally:
            os.unlink(path)
        out: list[tuple[str, float, float]] = []
        for seg in json.loads(raw).get("segments", []):
            for w in seg.get("words") or []:
                piece_text = w.get("word") or ""
                if not piece_text.strip():
                    continue
                a, b = max(0.0, float(w.get("start", 0)) - lead), max(0.0, float(w.get("end", 0)) - lead)
                if piece_text.startswith(" ") or not out:
                    out.append((piece_text.strip(), a, b))
                else:                                    # a word piece joins the word before ("chem" + "ist")
                    out[-1] = (out[-1][0] + piece_text.strip(), out[-1][1], b)
        return [] if all(w.strip(".,").lower() in ("nan", "") for w, _, _ in out) else out

    def _ask_server(self, path: str, audio_ctx: int, detail: bool = False, times: bool = False) -> str:
        """A plain multipart POST, so there is no HTTP library to add."""
        import uuid
        boundary = uuid.uuid4().hex
        with open(path, "rb") as f:
            wav = f.read()
        fmt = "verbose_json" if detail else "text"
        field = lambda k, v: f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
        # Without audio_ctx the server pads every sentence to 30 s and takes 2.2 s instead of 0.5 s (measured 15 Oct).
        # Word times are the exception: they need the full window and timestamps back on (the server starts with -nt).
        extra = field("no_timestamps", "false") if times else field("audio_ctx", audio_ctx)
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.wav\"\r\n"
                f"Content-Type: audio/wav\r\n\r\n".encode() + wav +
                ("\r\n" + field("response_format", fmt) + extra + f"--{boundary}--\r\n").encode())
        import urllib.request
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/inference", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            text = r.read().decode("utf-8", "replace")
        return text if detail else " ".join(text.split())


CRASH = store.DIR / "crash.txt"                   # the last crash, so the next start can own up to it


def _remember_crash(kind: str, value, tb) -> None:   # noqa: ANN001
    """
    Write an uncaught error down where the next start will find it.

    indite crashed four times in a week and nobody knew: the only record was a log file nobody reads, and each
    crash was found by grepping it after the fact (22 Oct). A crash that says nothing is a crash that gets
    reported as "the app stopped working" and costs a diagnosis round trip.
    """
    import traceback
    try:
        CRASH.parent.mkdir(parents=True, exist_ok=True)
        CRASH.write_text(time.strftime("%d %b %H:%M") + "\n"
                         + "".join(traceback.format_exception(kind, value, tb)), encoding="utf-8")
    except Exception:                                # noqa: BLE001 - never crash while recording a crash
        pass
    traceback.print_exception(kind, value, tb)


sys.excepthook = _remember_crash
threading.excepthook = lambda a: _remember_crash(a.exc_type, a.exc_value, a.exc_traceback)


class MicProblem(Exception):
    """The microphone could not be opened, with a reason worth showing someone."""


class MicStuck(MicProblem):
    """
    CoreAudio is deadlocked inside this process, and nothing but a new process gets the microphone back.

    16 Oct, sampled live: PortAudio's stop waited on CoreAudio's device lock while CoreAudio's own audio thread, inside
    PortAudio's start/stop listener, waited on PortAudio's lock. Neither ever lets go, and every later open queues on
    the same device lock - the pill appeared, nothing was recorded. Abandoning the stream does not release the lock.
    """


CARD_DEFAULTS = [("prompt", ""), ("rewrite", "Formal English")]   # most dictations go to Claude; Formal was most used


def card_slots(uses: dict, pins: list | None = None) -> list[tuple[str, str]]:
    """
    The text card's 2nd and 3rd buttons. A button you picked in Settings ("action|extra") stays put; an "Automatic"
    one is filled with the AI actions asked most often (each with the style or language it was last asked with),
    topped up from CARD_DEFAULTS. One button per action.
    """
    ok = lambda k: isinstance(k, str) and "|" in k and k.split("|", 1)[0] in ai.ACTIONS \
        and not k.startswith(("custom|", "review|"))     # review answers on the note, not on the card
    pins = [tuple(k.split("|", 1)) if ok(k) else None for k in (list(pins or []) + [None, None])[:2]]
    ranked = [tuple(k.split("|", 1)) for k, _ in sorted(uses.items(), key=lambda kv: -kv[1]) if ok(k)]
    fill = iter(x for x in ranked + CARD_DEFAULTS if x[0] not in [p[0] for p in pins if p])
    out: list[tuple[str, str]] = []
    for pin in pins:
        if pin and pin[0] not in [o[0] for o in out]:
            out.append(pin)
            continue
        for x in fill:
            if x[0] not in [o[0] for o in out]:
                out.append(x)
                break
    return out


def slot_title(action: str, extra: str) -> str:
    """"Make it a prompt", "Rewrite · Formal", "Translate · Hindi" - short enough for a button."""
    name = {"rewrite": "Rewrite", "translate": "Translate"}.get(action, ai.ACTIONS[action][0])
    return f"{name} · {extra.split()[0]}" if extra else name


def restart_allowed(mark: Path, every: float = 600.0) -> bool:
    """True at most once per `every` seconds; touching `mark` records the restart. Stops a restart loop."""
    if mark.exists() and time.time() - mark.stat().st_mtime < every:
        return False
    mark.parent.mkdir(parents=True, exist_ok=True)
    mark.touch()
    return True


def _alive() -> None:
    """
    Makes sure PortAudio is initialised before we ask it anything.

    It can be left shut down behind our back: re-reading the device list is Pa_Terminate + Pa_Initialize, and if the
    terminate wedges against CoreAudio's lock (16 Oct) it may finish later, on its own, with nothing to re-initialise
    it. Every microphone open after that failed with "Error querying device -1" until the app was restarted.
    """
    try:
        sd.query_devices()
        return
    except Exception:                                    # noqa: BLE001 - not initialised, or no devices
        pass
    try:
        sd._initialize()
        print("mic: PortAudio had been shut down; started it again")
    except Exception as e:                               # noqa: BLE001
        print("mic: could not start PortAudio:", e)


def _rescan() -> None:
    """
    Re-reads the device list, so a microphone plugged in after launch is found.

    This is Pa_Terminate + Pa_Initialize, which deadlocks against CoreAudio's lock if a stream is still on its way
    down. So it is NOT done on every press any more - only after every known device has already failed to open,
    where there is nothing left to lose. On its own thread, never waited on for long, and PortAudio is restarted
    afterwards whatever happened.
    """
    def go() -> None:
        try:
            sd._terminate()
        except Exception as e:                           # noqa: BLE001
            print("mic: could not close the device list:", e)
        try:
            sd._initialize()
        except Exception as e:                           # noqa: BLE001
            print("mic: could not re-open the device list:", e)

    t = threading.Thread(target=go, daemon=True)
    t.start()
    t.join(2.0)
    if t.is_alive():
        print("mic: re-reading the device list did not come back; carrying on")
    _alive()


class Mic:
    """Records only while the key is held. Nothing is captured before the press or after the release."""

    def __init__(self) -> None:
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        self.stream: sd.InputStream | None = None
        self.level = 0.0
        self.worked = ""                       # name of the mic that opened last time (names survive reconnects)
        self.chosen = ""                       # the mic picked in Settings; "" = automatic
        self.using = ""
        self.stuck = False                     # CoreAudio deadlocked in this process: only a restart helps (MicStuck)

    def start(self, wait: float = 8.0) -> None:
        """
        Opens the microphone, but never waits on a stuck CoreAudio for longer than `wait` seconds (a Bluetooth mic can
        be slow; a deadlock is forever). Raises MicStuck if CoreAudio is stuck, now or since an earlier close.
        """
        if self.stuck:
            raise MicStuck("the microphone got stuck in macOS earlier")
        box: dict = {}

        def go() -> None:
            try:
                self._start()
            except Exception as e:                       # noqa: BLE001 - handed to the caller below
                box["e"] = e

        t = threading.Thread(target=go, daemon=True)
        t.start()
        t.join(wait)
        if t.is_alive():
            self.stuck = True
            raise MicStuck(f"macOS did not open the microphone within {wait:.0f} s")
        if "e" in box:
            raise box["e"]

    def _start(self) -> None:
        """
        Opens the first microphone that actually opens.

        The default input is whatever macOS last picked, and that is often a Bluetooth headset that is off, or an
        iPhone that is not nearby (15 Oct: the default was a Bluetooth headset and every press died with PortAudio -9986,
        taking the key handler with it). So: try the default, then the built-in microphone, then anything else, and
        remember what worked. Raises MicProblem with something a person can act on if none of them open.
        """
        if self.stream:
            # It should already be None. If a previous stop() threw (a device yanked out, a sleep/wake, another app
            # taking the input), self.stream stayed set and every press after that opened nothing: the pill appeared,
            # the bars never moved, and the release wrote nothing (founder, 16 Oct). Never trust it - clear it.
            print("mic: a stream was still open from last time; closing it")
            self._drop()
        if DEMO_FEED.exists():                          # demo video only: this recording instead of the microphone
            self._feed(DEMO_FEED)
            return
        _alive()                                        # PortAudio can be left shut down by a wedged rescan
        self.q = queue.Queue()

        def cb(indata, frames, time_info, status):      # noqa: ANN001 - sounddevice's signature
            self.q.put(indata.copy())
            self.level = float(np.sqrt(np.mean(indata ** 2)) * 12)   # rough loudness, 0..1 for the pill

        last = None
        for attempt in (1, 2):
            for device in self._candidates():
                try:
                    stream = sd.InputStream(samplerate=RATE, channels=1, dtype="float32",
                                            device=device, callback=cb)
                    stream.start()
                    self.stream = stream
                    self.using = sd.query_devices(device if device is not None else sd.default.device[0])["name"]
                    self.worked = self.using            # remembered by name: positions change after a reconnect
                    return
                except Exception as e:                  # noqa: BLE001 - try the next one, keep the reason
                    last = e
            if attempt == 1:                            # everything failed: the list may be stale, or PortAudio dead
                print("mic: no device opened; re-reading the device list and trying once more")
                _rescan()
        raise MicProblem(str(last))

    def _feed(self, path: Path) -> None:
        """
        Plays a WAV into the recording as if it were the microphone, in real time, then stops on its own. Used only by
        the demo video (mac/demo.py), whose voice-over is synthetic speech; everything after this - the pill, the
        engine, the typing - is the normal path.
        """
        with wave.open(str(path)) as w:
            audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        path.unlink(missing_ok=True)
        self.q = queue.Queue()
        stop = threading.Event()

        def run():
            for i in range(0, len(audio), 1600):
                if stop.is_set():
                    return
                x = audio[i:i + 1600]
                self.q.put(x.reshape(-1, 1))
                self.level = float(np.sqrt(np.mean(x ** 2)) * 12)
                time.sleep(0.1)
            self.level = 0.0

        threading.Thread(target=run, daemon=True).start()
        self.stream = type("Feed", (), {"stop": lambda _s: stop.set(), "close": lambda _s: None})()
        self.using = "demo recording"

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

    def _drop(self) -> None:
        """
        Let go of the stream. The one rule: this returns, and afterwards there is no stream.

        16 Oct: four of indite's threads were found wedged in CoreAudio's own lock, inside PortAudio's
        FinishStoppingStream. `stream.stop()` never came back, so the release of the key never wrote anything and
        every press after that was dead - the pill appeared, the bars never moved, nothing was typed. CoreAudio is
        not ours to fix, so it does not get to hold the app: the close runs on a thread of its own, and if it has
        not finished in a second and a half the stream object is simply abandoned.
        """
        stream, self.stream, self.level = self.stream, None, 0.0

        def close() -> None:
            try:
                stream.abort()                           # abort, not stop: do not wait for buffers to drain
            except Exception:                            # noqa: BLE001
                pass
            try:
                stream.close()
            except Exception:                            # noqa: BLE001
                pass

        t = threading.Thread(target=close, daemon=True)
        t.start()
        t.join(1.5)
        if t.is_alive():
            self.stuck = True                            # the device lock is held for good: the next press restarts
            print("mic: CoreAudio would not let go of the stream; abandoned it - the app restarts on the next press")

    def stop(self) -> np.ndarray:
        if not self.stream:
            return np.zeros(0, dtype="float32")
        self._drop()
        chunks = []
        while not self.q.empty():
            chunks.append(self.q.get())
        return np.concatenate(chunks).flatten() if chunks else np.zeros(0, dtype="float32")


def run_modal(dialog) -> int:
    """Every alert and file panel goes through here: the hidden test copy answers Cancel and shows nothing."""
    if store.TEST:
        print("dialog (not shown, answered Cancel):", type(dialog).__name__)
        return 0
    return dialog.runModal()


def NSApp_activate() -> None:
    if store.TEST:                                       # the test copy never comes to the front
        return
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
    if store.TEST:
        return
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
        role = str(role)
        if role in {"AXTextField", "AXTextArea", "AXComboBox", "AXSearchField", "AXWebArea", "AXStaticText"}:
            return True
        # Chromium / Electron apps (Chrome, Slack, Claude, VS Code, Cursor, Discord) mark the focused web input as
        # AXGroup / AXGenericElement / AXUnknown but still expose kAXValueAttribute (what you'd set to type into it).
        # Fall through to that check so these apps aren't silently routed to clipboard-only. 23 Oct, founder: "the app
        # knows which app I'm in but doesn't know I'm in a text box".
        try:
            from ApplicationServices import kAXValueAttribute
            err, _ = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
            if err == 0:
                return True
        except Exception:                     # noqa: BLE001
            pass
        return False
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


def utf16_chunks(text: str, most: int) -> list[str]:
    """
    `text` in pieces of at most `most` UTF-16 units - the limit one macOS key event can carry.

    Counted in UTF-16, not characters, because that is what the system counts: an emoji is two units, so a naive
    split by characters would cut one in half and type a broken character.
    """
    out, piece, used = [], [], 0
    for ch in text:
        size = len(ch.encode("utf-16-le")) // 2
        if used + size > most and piece:
            out.append("".join(piece))
            piece, used = [], 0
        piece.append(ch)
        used += size
    if piece:
        out.append("".join(piece))
    return out


class Typer:
    """
    Puts the text where the cursor is, without ever touching the clipboard - the phone's floating mic has to use the
    clipboard and that is its one real privacy cost.

    pynput sends two key events per character (`_darwin.py:225`). A long dictation into a text field was therefore
    hundreds of events pushed at once, and Chromium-based apps (Slack, Chrome, VS Code) drain that queue a frame at
    a time, so the words crawled in visibly in bursts (founder, 16 Oct). macOS lets one key event carry up to 20
    UTF-16 units of text instead, so the same paragraph is ~40x fewer events. If that path fails for any reason the
    old one still runs, because typing nothing at all is the worst outcome.
    """

    MAX = 20                                             # UTF-16 units one key event may carry (macOS limit)

    def __init__(self) -> None:
        self.kb = keyboard.Controller()

    def type(self, text: str) -> None:
        text += " "
        try:
            import Quartz
            for chunk in utf16_chunks(text, self.MAX):
                for down in (True, False):
                    e = Quartz.CGEventCreateKeyboardEvent(None, 0, down)
                    Quartz.CGEventKeyboardSetUnicodeString(e, len(chunk.encode("utf-16-le")) // 2, chunk)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
                time.sleep(0.002)                        # a breath between events; without it apps reorder them
        except Exception as e:                           # noqa: BLE001 - never lose the words over a fast path
            print("fast typing failed, falling back:", e)
            self.kb.type(text)

    @staticmethod
    def copy(text: str) -> None:
        """No text field to type into, so the words wait on the clipboard instead of disappearing."""
        subprocess.run("pbcopy", input=text, text=True, check=False)


# The logo's five voice bars (mac/brand/logo.svg: the middle bar is the "i", stem + dot), in SVG units
LOGO_BARS = [(262, 452, 64, 200), (370, 392, 64, 320), (480, 440, 64, 372), (590, 392, 64, 320), (698, 452, 64, 200)]


def menubar_icon():
    """indite's own mark for the menu bar, drawn here (no image file), as a template image: macOS colours it for a
    light or dark menu bar. Replaces the 🎙 emoji (DESIGN.md: our own line icons, never emoji)."""
    from AppKit import NSBezierPath, NSColor, NSImage, NSMakeRect, NSMakeSize
    size, top, scale = 18.0, 294.0, 15.0 / 518.0               # the bars span 518 units: ~15 pt tall
    left = (size - 500 * scale) / 2

    def draw(_rect):
        NSColor.blackColor().set()
        for x, y, w, h in LOGO_BARS:
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(left + (x - 262) * scale, 1.5 + (y - top) * scale, w * scale, h * scale),
                w * scale / 2, w * scale / 2).fill()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(left + (466 - 262) * scale, 1.5 + (294 - top) * scale,
                                                          92 * scale, 92 * scale)).fill()   # the dot of the i
        return True
    img = NSImage.imageWithSize_flipped_drawingHandler_(NSMakeSize(size, size), True, draw)
    img.setTemplate_(True)
    return img


def status_text(title: str) -> str:
    """What sits next to the icon: the old emoji titles become short text (⚠ permission, … busy, ● recording, 3/10)."""
    return {"🎙": "", "🔴": "●", "⏳": "…"}.get(title, title.replace("🎙", "").replace("📄 ", "").strip())


class Offstage:
    """
    The test copy's stand-in for the pill, the text card and the typer: nothing on screen, nothing typed or copied.
    Every call is written to <data>/offstage.jsonl, so a test can check what would have been shown or typed.
    """

    def __init__(self, who: str) -> None:
        import types
        self.who, self.view, self.on_action = who, types.SimpleNamespace(), None

    def __getattr__(self, name: str):
        def call(*args, **kw):
            if self.who == "pill":                       # 20 calls a second: not worth a line each
                return
            with open(store.DIR / "offstage.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"who": self.who, "call": name, "args": args, "kw": kw}, default=str) + "\n")
        return call


class InditeApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("indite", title="", quit_button=None)   # the icon is set once the menu bar exists
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
        # One private dictation: typed as usual, but never written to disk (note, audio, log, clipboard copy). It
        # switches itself off after one dictation (critic 18 Oct, D22: never a setting that silently stays on).
        self.no_save_next = False
        self.no_save_item = rumps.MenuItem("Don't save the next dictation", callback=self.toggle_no_save)
        self.ops: queue.Queue = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()
        self.relisten = False
        self.ai_busy: dict = {}
        self.ai_who: dict = {}
        self.ai_keys: dict = {}          # note id -> what the AI is doing for it
        self.ai_error = ""
        self.notice = ""                 # one line for the window: backup done, restore result
        self.job: dict | None = None     # a file being transcribed: name, parts done, parts in all
        self.file_error = ""
        self.pill = Offstage("pill") if store.TEST else Pill()           # the test copy: nothing on screen
        self.preview = Offstage("card") if store.TEST else Preview()
        self.player = Player()           # a note's recording, played inside the window (Listen)
        if store.TEST:
            self.typer, self.player.vol = Offstage("typer"), 0.0
        threading.Thread(target=lambda: print("audio of deleted notes removed:", store.drop_orphan_audio()),
                         daemon=True).start()
        for r in store.history():                        # nothing is recording yet: a LIVE left by a crash is stale
            if r.get("live"):
                store.update(r["id"], live=None)
        self.preview.on_action = self.card_action
        self.set_card_buttons()          # fixed until the next start or a Settings change: no button moves under your finger
        self.card_note = None            # the note the text card is showing, for its AI buttons
        self.card_job = None             # (note id, action) asked from the card: its answer goes back to the card
        self.pill.set_clear(self.prefs["pill_clear"])
        self.done_until = 0.0
        self.done_state = "done"
        # 20 times a second, on the main thread: the only place the pill is ever touched.
        rumps.Timer(self.paint, 0.05).start()
        self.menu = [
            rumps.MenuItem(f"Hold {HOTKEYS.get(self.prefs['hotkey'], 'Right ⌥')} and speak" if can_listen()
                           else "⚠ indite can’t notice your talk key. Open indite to fix it", callback=None),
            None,
            rumps.MenuItem("Open indite", callback=self.open_window, key="o"),
            rumps.MenuItem("Copy the last dictation", callback=self.copy_last),
            self.no_save_item,
            rumps.MenuItem("Edit Dictionary as a file\u2026", callback=self.edit_fixes),
            rumps.MenuItem("Transcribe a file\u2026", callback=self.open_files),
            self.meeting_item,
            None,
            rumps.MenuItem("Quit", callback=self.quit_all),
        ]
        problem = self.engine.ready()
        if problem:
            rumps.alert("indite can’t start", problem)
            sys.exit(1)
        bad_seal = signature_broken()
        if bad_seal:
            print("SIGNATURE BROKEN:", bad_seal)
            rumps.alert(
                "indite’s app file has been changed",
                "macOS checks indite's signature before it trusts it with the keyboard. That signature is no "
                "longer valid, so Accessibility will stop working - usually in the middle of a session, with no "
                "warning.\n\n"
                f"What changed: {bad_seal}\n\n"
                "Fix: run ./mac/build_app.sh again, then grant Accessibility and Screen Recording once more.",
            )
        if not can_listen() and not self.prefs.get("setup_done"):
            self.set_title("🎙⚠")                       # the setup sheet opens on its own and explains Accessibility
        elif not can_listen():
            self.set_title("🎙⚠")
            ask_to_listen()
            rumps.alert(
                "indite needs permission to see the hotkey",
                "macOS has not allowed indite to notice key presses yet, so holding the key does nothing.\n\n"
                "System Settings → Privacy & Security → Accessibility → switch on indite. If indite is not in the "
                "list, click + and pick indite from Applications.\n\n"
                "Then quit indite (menu bar icon → Quit) and open it again.",
            )
        # macOS slows a background app's timers down (App Nap). indite spends its whole working life in the
        # background, so the pill's animation and the level bars were being starved exactly when they matter.
        try:
            from Foundation import NSActivityUserInitiated, NSProcessInfo
            self._awake = NSProcessInfo.processInfo().beginActivityWithOptions_reason_(
                NSActivityUserInitiated, "dictation overlay must animate while another app is in front")
        except Exception as e:                           # noqa: BLE001 - a slower pill is better than no app
            print("could not switch off App Nap:", e)
        if CRASH.exists() and not store.TEST:            # own up to the last crash rather than let it go unnoticed
            try:
                what = CRASH.read_text(encoding="utf-8")
                CRASH.unlink()
                last = [l for l in what.strip().splitlines() if l.strip()][-1][:200]
                print("last run ended in a crash:", last)
                rumps.alert("indite stopped unexpectedly last time",
                            f"{what.splitlines()[0]}\n\n{last}\n\nIt is written to the log. "
                            "Nothing you had saved is affected.")
            except Exception as e:                       # noqa: BLE001 - never crash reporting a crash
                print("could not read the crash note:", e)
        if not store.TEST:               # the test copy never listens to the keyboard, nor watches for calls
            threading.Thread(target=self.listen, daemon=True).start()
            threading.Thread(target=self.watch_calls, daemon=True).start()
        threading.Thread(target=self.warm_up, daemon=True).start()
        # Opening the app shows its window, like any Mac app; a timer, so it is built on the main thread once the
        # run loop is going. ponytail: a second `open` while running does nothing; handle reopen if that annoys.
        self._activation = Activation.alloc().initWithApp_(self)
        self._first = rumps.Timer(self._show_on_launch, 0.5)
        self._first.start()

    def _show_on_launch(self, timer) -> None:            # noqa: ANN001
        timer.stop()
        self.open_window(None)
        if store.TEST:                   # no menu-bar icon, and nothing that brings it to the front
            from AppKit import NSStatusBar
            NSStatusBar.systemStatusBar().removeStatusItem_(self._nsapp.nsstatusitem)
            return
        try:
            button = self._nsapp.nsstatusitem.button()
            button.setImage_(menubar_icon())
            button.setImagePosition_(2)                  # NSImageLeft: the icon, then any status text
        except Exception as e:                           # noqa: BLE001 - a text title is better than no menu
            print("menu-bar icon:", e)
            self.title = "indite"
        # Opening indite again (Finder, Spotlight, Dock) only activates the running copy; nothing appeared, so it
        # looked as if it was not running (founder, 15 Oct). Show the window whenever the app is activated.
        from AppKit import NSNotificationCenter
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self._activation, "fire:", "NSApplicationDidBecomeActiveNotification", None)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self._activation, "resigned:", "NSApplicationDidResignActiveNotification", None)

    def warm_up(self) -> None:
        """Load the model now, not when the user is waiting with their finger on the key."""
        try:                                             # say plainly in the log whether meetings can hear calls
            import Quartz
            print("screen & system audio recording allowed:", bool(Quartz.CGPreflightScreenCaptureAccess()))
            print("key access (Accessibility) allowed:", can_listen())
        except Exception:                                # noqa: BLE001
            pass
        if not self.prefs.get("asked_screen") and not store.TEST:           # once: lets the meeting recorder hear the other people
            try:
                import Quartz
                if not Quartz.CGPreflightScreenCaptureAccess():
                    Quartz.CGRequestScreenCaptureAccess()  # macOS shows its own prompt and adds indite to the list
            except Exception:                            # noqa: BLE001
                pass
            store.set_pref("asked_screen", True)
        self.set_title("🎙…")
        self.engine_kind = "Starting the engine… the first start on a Mac can take a minute"
        self.refresh()
        ok = self.engine.start_server()
        self.engine_kind = "Fast engine ready." if ok else "Slower engine \u2014 the model reloads each time."
        self.set_title("🎙" if can_listen() else "🎙⚠")
        print("resident engine:", "ready" if ok else "not available - using the slower per-sentence path")

    def paint(self, _) -> None:                          # noqa: ANN001 - rumps' signature
        """Shows what is happening, in the place the eye already is: just above the Dock."""
        self.snap_tick = getattr(self, "snap_tick", 0) + 1
        if self.snap_tick % 5 == 0 and self.player.p and self.window:   # the playing time, 4 times a second
            st = self.player.state()
            if st["playing"] or getattr(self, "player_was", None) != st:
                self.player_was = st
                self.window.bridge.js(f"playerTick({json.dumps(st)})")
        if self.snap_tick % 200 == 0:                    # every 10 s at full speed; far less if macOS throttles us
            now = time.time()
            was = getattr(self, "_rate_at", now)
            self._rate_at = now
            if now > was:
                print(f"paint: {200 / (now - was):.1f} ticks a second (asked for 20)", flush=True)
        if self.snap_tick % 5 == 0 and DEMO_CMD.exists():
            self.demo_cmd()
        if self.snap_tick % 20 == 0 and SNAP_REQUEST.exists():
            if SNAP_REQUEST.read_text().startswith("preview:"):          # the text card, with this text
                self.preview.snapshot(SNAP_REQUEST)
            elif SNAP_REQUEST.read_text().startswith("pill:"):           # the pill at this transparency
                pct = int(SNAP_REQUEST.read_text()[5:].strip() or 60)
                self.pill.set_clear(pct)
                self.done_state, self.done_until = "done", time.time() + 3
                self.pill.snapshot(SNAP_REQUEST, f"snapshot-pill-{pct}.png")
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
        """
        The key listener, restarted whenever macOS switches it off (a slow moment anywhere can do that, and pynput
        never switches it back on). Watching costs nothing: macOS sends a "tap disabled" event first.
        """
        while True:
            self.relisten = False
            with keyboard.Listener(on_press=self._press, on_release=self._release,
                                   darwin_intercept=self._tap_event) as listener:
                self.listener = listener
                listener.join()
            if not self.relisten:
                return
            print("key listener was switched off by macOS - started again")
            time.sleep(0.2)

    def _tap_event(self, event_type, event):            # noqa: ANN001
        if event_type in (0xFFFFFFFE, 0xFFFFFFFF):       # kCGEventTapDisabledByTimeout / ByUserInput
            self.relisten = True
            threading.Thread(target=self.listener.stop, daemon=True).start()
        return event

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

    def do(self, fn) -> None:                            # noqa: ANN001
        """
        Microphone work, off the key handler. macOS silently switches off a key listener whose callback is slow, and
        opening a Bluetooth mic can take a while: after that no hotkey worked until a restart (founder, 15 Oct). So
        key handlers only change state; opening and closing the mic happens here, in order, on one worker thread.
        """
        if self.ops is None:                             # tests: run at once
            fn()
        else:
            self.ops.put(fn)

    def _worker(self) -> None:
        while True:
            fn = self.ops.get()
            try:
                fn()
            except Exception as e:                       # noqa: BLE001 - one failed step must not stop the worker
                print("mic step failed:", e)

    def start_listening(self) -> bool:
        """Listening starts now as far as the keys are concerned; the mic itself opens on the worker."""
        if getattr(self, "player", None) and self.player.p:   # the mic would hear the speakers: playback waits
            self.player.pause()
        self.started_at = time.time()
        self.set_title("🔴")

        self.preview.hide_now()      # an old card must never sit over the dictation you are starting now

        def open_mic() -> None:
            try:
                self.mic.start()
            except Exception as e:                       # noqa: BLE001
                self.started_at = 0.0
                self.locked = False
                self.set_title("🎙")
                self.mic_trouble(e)
        self.do(open_mic)
        return True

    def on_press(self, key) -> None:                     # noqa: ANN001 - pynput's signature
        if self.meeting.running:                          # the mic belongs to the meeting until it stops
            if key == self.hotkey() and self.prefs["sounds"]:
                chime("Funk")                            # heard, not shown: the pill already shows the meeting
            return
        if key == keyboard.Key.esc and self.started_at:   # cancel: nothing is written, the audio is dropped
            # ponytail: pynput cannot swallow the key on macOS, so Esc also reaches the app underneath
            self.started_at = 0.0
            self.locked = False
            self.do(self.mic.stop)
            self.set_title("🎙")
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
            self.do(self.mic.stop)
            self.set_title("🎙")
            return
        self.taps = 0
        self.finish()

    def finish(self) -> None:
        """Stop listening and write what was said. Ends a hold, a hands-free tap, and the hands-free time cap."""
        self.started_at = 0.0
        self.locked = False
        if self.prefs["sounds"]:
            chime("Pop")

        def close_and_write() -> None:
            audio = self.mic.stop()
            if len(audio) < RATE // 2:
                # Under half a second. Either a very quick press, or the microphone gave us nothing at all - and the
                # second one used to end in silence, which is indistinguishable from the app being broken.
                self.set_title("🎙")
                self.done_state = "nothing" if len(audio) else "failed"
                self.done_until = time.time() + 1.6
                if not len(audio):
                    print("mic produced no audio at all - the stream was open but silent")
                return
            self.set_title("⏳")
            self.busy = True
            threading.Thread(target=self.write_it, args=(audio,), daemon=True).start()
        self.do(close_and_write)

    def mic_trouble(self, err: Exception) -> None:
        """
        A microphone that will not open is either a permission macOS has not granted, or a device that is not there.
        Both are fixable by the user, and neither should be a silent nothing-happens (the lesson from the alarm
        switch, the API key and the hotkey: a thing that cannot work has to say so).

        Runs on the mic worker thread. The alerts MUST hop to the main thread: NSAlert → NSWindow._doOrderWindow,
        which asserts main-thread. Without the hop the alert never displays and the worker crashes with
        NSInternalInconsistencyException (seen 23 Oct). set_title / pill.show / threading.Timer are already safe.
        """
        print("mic: could not start:", repr(err))
        if isinstance(err, MicStuck):
            self.restart_for_stuck_mic(err)
            return
        self.pill.show("error")
        allowed = mic_allowed()
        from PyObjCTools import AppHelper
        if allowed is False:
            ask_mic()
            AppHelper.callAfter(rumps.alert,
                "indite cannot hear the microphone",
                "macOS has not given indite permission to use the microphone.\n\n"
                "System Settings → Privacy & Security → Microphone → turn on indite, then quit and open it again.",
            )
        else:
            AppHelper.callAfter(rumps.alert,
                "indite could not open any microphone",
                "Tried every input on this Mac and none of them opened.\n\n"
                "The usual cause is a Bluetooth headset that is switched off, or an iPhone microphone that is not "
                f"nearby. Connect a microphone, or turn Bluetooth off, and try again.\n\n({err})",
            )
        threading.Timer(2.0, self.pill.hide).start()

    def restart_for_stuck_mic(self, err: Exception) -> None:
        """
        A deadlocked CoreAudio (MicStuck) holds the microphone until this process ends, so indite starts itself
        again. It happens on the next press, not when the close sticks: by then the last dictation has been typed and
        a meeting's text saved. At most once in 10 minutes, so a Mac whose audio is broken outright gets a message,
        not a restart loop.
        """
        print("mic:", err)
        if store.TEST:                   # the test copy never opens the mic, and never restarts by itself
            return
        bundle = next((p for p in Path(sys.executable).parents if p.suffix == ".app"), None)
        if bundle is None or not restart_allowed(store.DIR / "mic-restart.last"):
            self.pill.show("error")
            # Also runs on the mic worker thread; see mic_trouble - the alert must hop to the main thread.
            from PyObjCTools import AppHelper
            AppHelper.callAfter(rumps.alert, "The microphone is stuck in macOS",
                        "macOS stopped answering indite about the microphone. Quit indite and open it again.\n\n"
                        "If it is stuck again straight away, restart the Mac.")
            threading.Timer(2.0, self.pill.hide).start()
            return
        for _ in range(120):                         # a meeting that is still saving its last words goes first
            if "finishing" not in self.ai_busy.values():
                break
            time.sleep(0.5)
        print("mic: restarting indite to get the microphone back")
        # A detached shell, so the old process is gone before the new one opens (two copies would both hear the keys).
        subprocess.Popen(["/bin/sh", "-c", 'osascript -e "display notification \\"The microphone got stuck in macOS. '
                          'indite is restarting. Try again in a few seconds.\\" with title \\"indite\\""; '
                          f'sleep 1; open -n "{bundle}"'], start_new_session=True)
        os._exit(0)                  # not sys.exit: sounddevice's exit hook calls Pa_Terminate, which waits on the lock

    # ---- the work ------------------------------------------------------------------------------------------
    def write_it(self, audio: np.ndarray) -> None:
        t0 = time.time()
        where, where_pid = front_app(), front_pid()              # asked before anything is typed, so the history says which app it went to
        try:
            heard = self.engine.transcribe(audio)
            text = self.tidy(heard)
            if junk(text, len(audio) / RATE):
                text = ""
        except Exception as e:                            # noqa: BLE001 - whatever went wrong, say so and carry on
            self.set_title("🎙")
            self.busy = False
            self.done_state = "failed"
            self.done_until = time.time() + 2.0
            print("dictation failed:", e)
            return
        self.busy = False
        self.set_title("🎙")
        if not text:
            self.done_state = "nothing"
            self.done_until = time.time() + 1.2
            return
        if focused_is_secret():          # every mode, "always type" included: never typed, copied or saved
            self.done_state = "secret"
            self.done_until = time.time() + 2.0
            print("password box focused - dictation dropped")
            return
        self.last = self.out(text)                      # what is typed, copied and previewed; the note keeps the real words
        # The pill says what happened. A notification was tried here and crashed the thread that had just produced
        # the text (rumps needs a bundle identifier it could not find), so the words landed with nothing said.
        private = self.no_save_next                     # "Don't save the next dictation": this one only
        mode = self.prefs["output"]
        if mode == "type" or (mode == "smart" and focused_is_text()):
            self.typer.type(self.last)
            if self.prefs.get("also_copy", True) and not private:   # typed by key events: the clipboard may hold it too
                self.typer.copy(self.last)
            self.done_state = "done"
        else:
            self.typer.copy(self.last)
            self.done_state = "copied"
            # A fallback nobody asked for: smart mode could not find a text box, so the words are on the clipboard
            # instead of where the cursor is. 7% of the founder's dictations ended this way (22 Oct). The card that
            # explains it is off by default, so this one case turns it on for itself - the only moment when the words
            # are not where the person is looking. Choosing "copy" in Settings is a different thing: that was asked
            # for, and it stays quiet.
            self.surprise_copy = mode == "smart"
        self.done_until = time.time() + 1.6
        took = time.time() - t0
        # Spoken into indite's own window (the Ask AI box, search, a rename): that's input to indite, not a note.
        if private:                                      # used once, then off again
            self.no_save_next = False
            self.no_save_item.state = 0
            self.set_title("")
        note = None if where_pid == os.getpid() or private else store.add(
            text, len(audio) / RATE, took, self.done_state, where,
            **({"raw": heard} if heard.strip() != text.strip() else {}))   # what the engine heard, so a fix can be undone
        if note and self.prefs.get("review"):
            threading.Thread(target=self.review, args=(note, audio, text), daemon=True).start()
        if note and self.prefs["keep_audio"]:            # off by default: a recording of everything said is a lot
            store.AUDIO.mkdir(parents=True, exist_ok=True)
            with wave.open(str(store.AUDIO / f"{note}.wav"), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(RATE)
                w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
        if note and self.prefs["keep_audio"]:
            gone, freed = store.trim_audio()             # kept audio had no limit at all and grew ~31 MB a day
            if gone:
                print(f"kept audio was over {store.AUDIO_CAP_MB} MB: dropped the {gone} oldest, freed {freed:.0f} MB")
        self.refresh()                   # the list grows while it is open, so a dictation shows up as it lands
        if self.prefs["preview"] or getattr(self, "surprise_copy", False):
            self.card_note = note
            told = (("Not saved.\n" if private else "")
                    + ("No text box here, so it is on the clipboard — paste with ⌘V.\n"
                       if getattr(self, "surprise_copy", False) else
                       "Copied. Paste with ⌘V.\n" if self.done_state == "copied" else ""))
            self.preview.show(told + self.last, buttons=(True if self.prefs.get("ai") else "todo") if note else False)
        self.surprise_copy = False
        print(f"{len(audio) / RATE:.1f}s of speech -> {took:.2f}s -> " + ("(private: not saved, not logged)" if private else text))

    # ---- menu ----------------------------------------------------------------------------------------------
    def reload_prefs(self) -> None:
        """Called by the window after a setting changes. The prefs are not cached anywhere else."""
        self.prefs = store.prefs()
        self.mic.chosen = self.prefs["mic"]
        self.pill.set_clear(self.prefs["pill_clear"])
        if self.card_pins != list(self.prefs.get("card_buttons") or []):
            self.set_card_buttons()                      # picked in Settings: show it at once

    def set_card_buttons(self) -> None:
        self.card_pins = list(self.prefs.get("card_buttons") or [])
        self.card_slots = card_slots(self.prefs.get("ai_uses") or {}, self.card_pins)
        self.preview.set_titles([slot_title(a, x) for a, x in self.card_slots])

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
            rumps.alert("indite is still on another file", f"{self.job['name']}: {self.job['done']} of "
                        f"{self.job['total']} parts done. It will appear in Files when it finishes.")
            return
        panel = NSOpenPanel.openPanel()
        panel.setTitle_("Transcribe a file")
        panel.setPrompt_("Transcribe")
        panel.setAllowsMultipleSelection_(False)
        NSApp_activate()
        if run_modal(panel) == 1 and panel.URLs():
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
        self.job_stop = False                            # Stop on the job card: keep what is done so far
        self.refresh()
        try:
            audio, _damaged = load_audio(path)
            parts = pieces(audio)
            self.job["total"] = len(parts)
            segments, at = [], 0.0
            for p in parts:
                if self.job_stop:
                    break
                text = self.tidy(self.engine.transcribe(p))
                if text:
                    segments.append({"start": round(at, 2), "end": round(at + len(p) / RATE, 2), "text": text})
                at += len(p) / RATE
                self.job["done"] += 1
                self.set_title(f"📄 {self.job['done']}/{self.job['total']}")
                self.refresh()
            body = "\n\n".join(s["text"] for s in segments)
            if body:
                stopped = self.job_stop and self.job["done"] < self.job["total"]
                note = store.add(body, at, time.time() - t0, "file", "", kind="file",
                                 title=path.name + (" (stopped)" if stopped else ""),
                          segments=segments, source=str(path))
            print(f"file {path.name}: {at:.0f}s of audio -> {time.time() - t0:.0f}s, {len(segments)} parts")
            if body and note and self.prefs["auto_speakers"] and at >= 20 and not self.job_stop:   # stopped: you asked to stop
                self.who_spoke(note)                     # by default: no click needed (founder, 15 Oct)
            self.done_state = "done" if body else "nothing"
        except Exception as e:                           # noqa: BLE001 - say so, keep the app alive
            print("file failed:", path, e)
            self.done_state = "failed"
            plain = ("indite can’t read this file as audio or video." if "Invalid data" in str(e) or "Errno" in str(e)
                     else str(e))                          # the raw error stays in the log, not the banner
            self.file_error = f"{path.name}: {plain}"
        finally:
            self.job = None
            self.set_title("🎙")
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
            where = ai.NAMES.get(self.prefs["ai_provider"], "Claude")
            alert.setInformativeText_(
                f"AI answers come from {where}. The note’s text leaves this Mac to get the answer; nothing else "
                "does. If the note is about work, check your company’s rules first.\n\nYou will not be asked "
                "again; change or turn off AI in Settings → AI.")
            alert.addButtonWithTitle_("Send")
            alert.addButtonWithTitle_("Cancel")
            if run_modal(alert) != NSAlertFirstButtonReturn:
                return
            store.set_pref("ai_ok", True)
            self.reload_prefs()
        row = next((r for r in store.history() if r["id"] == note_id), None)
        if not row or note_id in self.ai_busy:
            return
        if row.get("kind") in ("meeting", "file") and not self.prefs.get("ai_ok_meetings"):
            # other people's voices: ask every time, unless the person said not to (founder, 15 Oct)
            where = ai.NAMES.get(self.prefs["ai_provider"], "Claude")
            alert = NSAlert.alloc().init()
            alert.setMessageText_(f"Send what other people said to {where}?")
            alert.setInformativeText_(
                f"It includes what others said. Check they’re OK with it first.\n\n{where} gets the full text. "
                "Whether it is kept or used to train their AI depends on your account settings with them, not on "
                "indite.")
            alert.addButtonWithTitle_("Send")
            alert.addButtonWithTitle_("Cancel")
            alert.setShowsSuppressionButton_(True)
            alert.suppressionButton().setTitle_("Don’t ask again for meetings and files")
            if run_modal(alert) != NSAlertFirstButtonReturn:
                return
            if alert.suppressionButton().state():
                store.set_pref("ai_ok_meetings", True)
                self.reload_prefs()
        self.ai_error = ""                               # one app-wide error: an old one must not sit in a new answer
        if action != "custom":                           # counted, to pick the text card's two buttons
            uses = dict(self.prefs.get("ai_uses") or {})
            uses[f"{action}|{extra}"] = uses.get(f"{action}|{extra}", 0) + 1
            store.set_pref("ai_uses", uses)
            self.prefs["ai_uses"] = uses
        self.ai_busy[note_id] = ai.ACTIONS[action][0]
        self.refresh()
        threading.Thread(target=self._ai, args=(row, action, extra), daemon=True).start()


    def review(self, note: str, audio: np.ndarray, text: str) -> None:
        """
        After the words are typed: look for Dictionary words the engine may have misheard (mac/review.py). Runs on its
        own thread and asks the engine for per-word confidence, which costs about one more transcription - never on
        the typing path. A flag is only kept if its words are still in the saved text.
        """
        import review
        targets = [want for _, want in store.my_fixes()]
        if not targets:
            return
        try:
            found = review.on_text(text, self.engine.confidence(audio), targets)
        except Exception as e:                           # noqa: BLE001 - a review must never cost the dictation
            print("review failed:", e)
            return
        if found:
            store.update(note, flags=[{"heard": f["heard"], "want": f["want"]} for f in found])
            print(f"review: {len(found)} likely mistake(s) in {note}: " + ", ".join(f"{f['heard']} -> {f['want']}" for f in found))
            self.refresh()

    def line_up(self, note_id: str) -> None:
        """
        When each shown word was spoken, once per note, kept on the note as "wt" (mac/wordtimes.py). Runs on its own
        thread: about 4 s of engine time per 20 s of audio, so a 15-minute file takes ~3 minutes the first time.
        """
        import wordtimes
        from indite.core import load_audio
        row = next((r for r in store.history() if r["id"] == note_id), None)
        if not row or note_id in self.ai_busy:
            return
        self.ai_busy[note_id] = "lining up the words"
        self.refresh()
        try:
            files, segs, meet = store.audio_files(row), row.get("segments") or [], row.get("kind") == "meeting"
            wt = []
            for k, path in enumerate(files):
                lines = ([s for s in segs if store.track_of(s, meet) == k] if meet else segs) if segs \
                    else [{"start": 0.0, "text": row["text"]}]
                if not lines:
                    continue
                audio, _ = load_audio(path)
                timed = self.engine.word_times(audio)
                if self.engine.proc is None or self.engine.proc.poll() is not None:
                    raise RuntimeError("the engine is not running")   # save nothing, try next time
                words = [l["text"].split() for l in lines]
                floor = [float(l.get("start", 0)) for l in lines]
                times = wordtimes.align(words, timed, floor)
                if wordtimes.matched(words, timed) < 0.5 or not wordtimes.usable(times):   # estimate from the sound
                    print(f"word times: estimated for {note_id} (the engine matched too few words)")
                    times = wordtimes.spread(words, floor, [float(l.get("end", 0)) for l in lines], audio)
                wt += [{"s": float(l.get("start", 0)), "k": k, "t": t} for l, t in zip(lines, times)]
            now = next((r for r in store.history() if r["id"] == note_id), {})
            if (now.get("text"), now.get("segments")) != (row.get("text"), row.get("segments")):
                print(f"word times: {note_id} was edited meanwhile - not saved, lined up again next time")
                return
            store.update(note_id, wt=wt)
            print(f"word times: {sum(len(x['t']) for x in wt)} words lined up for {note_id}")
        except Exception as e:                           # noqa: BLE001 - the player still works by line without it
            print("word times failed:", e)
        finally:
            self.ai_busy.pop(note_id, None)
            self.refresh()

    def card_action(self, i: int) -> None:
        """
        A button on the text card (main thread). Ask AI opens that note's Ask AI panel; the other two run straight
        away, keep the card up while the AI works, then show the answer and put it on the clipboard (founder, 17 Oct).
        """
        note = self.card_note
        if not note:
            return
        if i == 3:                                       # To do: one tap, no AI, nothing leaves the Mac
            store.update(note, todo="open")
            self.refresh()
            self.preview.answer("✓ Added to To do")
            return
        if i == 0:
            from PyObjCTools import AppHelper
            fresh = self.window is None                  # a window built just now needs its page loaded first
            self.open_window(None)
            AppHelper.callLater(1.5 if fresh else 0.0, self.window.bridge.js,
                                f"go('home'); openDrawer({json.dumps(note)})")
            return
        action, extra = self.card_slots[i - 1]
        doing = f"{slot_title(action, extra)}…"
        self.card_job = (note, action)
        self.ask_ai(note, action, extra)                 # asks first if AI has never been used; may be cancelled
        if note in self.ai_busy:
            self.preview.working(doing)
        else:
            self.card_job = None

    def _ai(self, row: dict, action: str, extra: str) -> None:
        t0 = time.time()
        answer = None
        try:
            if action == "review":                       # AI review step 2: likely mistakes, never a rewrite
                if row.get("segments"):                  # a Fix edits the text; timed lines would no longer match
                    raise RuntimeError("Review with AI works on dictations for now, not on meetings or files")
                targets = [want for _, want in store.my_fixes()]
                mine = [f for f in row.get("flags") or [] if f.get("by") != "ai"]
                found = ai.review(row["text"], targets, mine, self.prefs["ai_provider"], self.prefs["ai_model"])
                found = [f for f in found if not any(f["heard"] == m["heard"] for m in mine)]
                store.update(row["id"], flags=mine + found or None)
                print(f"ai review: {len(found)} suggestion(s) for {row['id']} in {time.time() - t0:.1f}s")
                answer = ""
                if self.window:
                    from PyObjCTools import AppHelper
                    said = f"{len(found)} likely mistake{'s' if len(found) != 1 else ''} to check" if found else "Nothing looks wrong"
                    AppHelper.callAfter(self.window.bridge.js, f"toast({said!r})")
                return
            answer, usage = ai.run(action, row["text"], extra, self.prefs["ai_provider"], self.prefs["ai_model"])
            # cost fields are optional on the AiReply (new 24 Oct). None means "no cost reported" rather than $0,
            # so the UI can say so honestly - the Claude-via-CLI path never carries a number.
            cost = {k: usage[k] for k in ("model", "in_tok", "out_tok", "cost_usd") if usage.get(k) is not None}
            if action == "improve":
                store.update(row["id"], improved=answer, improved_cost=cost or None)
            else:
                label = (f"Asked: {extra}" if action == "custom" else
                         ai.ACTIONS[action][0] + (f" · {extra}" if extra else ""))
                answers = [a for a in row.get("ai", []) if a["label"] != label]
                store.update(row["id"], ai=answers + [{"action": action, "label": label, "text": answer,
                                                       "at": time.time(), **cost}])
            print(f"ai {action}: {time.time() - t0:.1f}s")
            secs = (list(self.prefs.get("ai_secs") or []) + [round(time.time() - t0, 1)])[-30:]
            store.set_pref("ai_secs", secs)              # the typical wait, shown while the next answer is coming
            self.prefs["ai_secs"] = secs
            if self.prefs.get("also_copy", True) or self.card_job == (row["id"], action):
                self.typer.copy(self.out(answer))        # on the clipboard the moment it is shown; masked like all output
                if self.window and self.card_job != (row["id"], action):
                    from PyObjCTools import AppHelper
                    AppHelper.callAfter(self.window.bridge.js, "toast('Answer copied. Paste it anywhere.')")
        except Exception as e:                           # noqa: BLE001 - not logged in, out of quota, offline...
            self.ai_error = str(e)
            print("ai failed:", e)
        finally:
            self.ai_busy.pop(row["id"], None)
            self.refresh()
            if self.card_job == (row["id"], action):     # asked from the text card: the answer goes back there
                self.card_job = None
                if answer:
                    shown = re.sub(r"\*\*(.+?)\*\*", r"\1", self.out(answer))   # plain text on the card, masked
                    self.preview.answer("Copied. Paste it anywhere.\n\n" + shown)
                else:
                    self.preview.failed("The AI did not answer: " + (self.ai_error or "no reply") +
                                        "\nPress the button again to retry.")

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
        if run_modal(panel) == 1 and panel.URL():
            n = store.backup(Path(str(panel.URL().path())), self.prefs["backup_scope"], self.prefs["backup_audio"])
            self.notice = f"Backed up {n} note{'s' if n != 1 else ''}."
            self.refresh()

    def restore(self) -> None:
        from AppKit import NSOpenPanel
        panel = NSOpenPanel.openPanel()
        panel.setPrompt_("Restore")
        NSApp_activate()
        if run_modal(panel) == 1 and panel.URLs():
            try:
                n = store.restore_zip(Path(str(panel.URLs()[0].path())))
                self.notice = f"Restored {n} note{'s' if n != 1 else ''}." if n else "Nothing new: every note in that backup is already here."
            except Exception as e:                       # noqa: BLE001 - not a backup, damaged, or too new
                import zipfile
                self.notice = ("Could not restore: that file is not an indite backup." if isinstance(e, zipfile.BadZipFile)
                               else f"Could not restore: {e}")
            self.refresh()

    def tidy(self, text: str) -> str:
        """Everything after the engine, in one place for dictation and files alike."""
        if self.prefs["spelling"]:
            text = apply_fixes(text, self.table)
        if self.prefs["digits"]:
            text = numbers.digits(text)
        return store.apply_my_fixes(text, store.my_fixes())   # yours last, and even with the others off
        # Swears are NOT masked here: this text is what gets saved. They are masked on the way out (out()).

    def out(self, text: str) -> str:
        """Text as it leaves indite - typed, copied, previewed, exported - with swears masked if that is switched on."""
        return store.mask_swears(text, self.prefs.get("my_swears")) if self.prefs.get("mask_swears") else text

    def toggle_no_save(self, _=None) -> None:            # noqa: ANN001
        self.no_save_next = not self.no_save_next
        self.no_save_item.state = int(self.no_save_next)   # a tick in the menu
        self.set_title("private" if self.no_save_next else "")

    def watch_calls(self) -> None:
        """Every 3 s: has a call app started using the mic? Then ask once (Settings → Ask to record calls)."""
        import calls
        while True:
            time.sleep(3)
            try:
                self.call_tick(calls.call_app())
            except Exception as e:                       # noqa: BLE001 - a missed question beats a dead watcher
                print("call watch:", e)
                time.sleep(60)

    def call_tick(self, app: str) -> None:
        """app: the call app on the mic now, or "". Asks at most once per call; never while recording or dictating."""
        if not app:
            self.call_asked = ""                         # the call ended: the next one may be asked about
            return
        if app == getattr(self, "call_asked", "") or self.meeting.running or self.started_at or self.busy \
                or not self.prefs.get("ask_calls", True):
            return
        self.call_asked = app
        print("call watch:", app, "is using the mic - asking")
        self.preview.ask(f"{app} is using the microphone. Record this call?", ["Record", "Not now"],
                         lambda i: i == 0 and not self.meeting.running and self.toggle_meeting())

    def toggle_meeting(self, _=None) -> None:            # noqa: ANN001
        """Start or stop a meeting recording (main thread)."""
        if self.meeting.running:
            # The old one finishes on its own thread; a fresh one is ready at once, so back-to-back calls never wait.
            old, self.meeting = self.meeting, Meeting(self, after=self.meeting)
            threading.Thread(target=old.stop, daemon=True).start()
            self.meeting_item.title = "Record a meeting"
            return
        if self.started_at or self.busy:
            return
        self.player.stop()                               # the meeting's mic must not record the playback
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
        # No warning here on purpose: working out who spoke is done on this Mac by mac/speakers.py. Nothing leaves
        # the machine, so there is nothing to ask about. (15 Oct the consent dialog was pasted in here as well as in
        # ask_ai; it asked about a send that never happens, and crashed - NSAlert is imported in ask_ai, not here -
        # which made every file say "file failed" after transcribing perfectly well.)
        self.ai_busy[note_id] = "finding who spoke"
        self.refresh()
        threading.Thread(target=self._who, args=(row, k), daemon=True).start()

    @staticmethod
    def _silent(path: Path, share: float = 0.03) -> bool:
        """True when a track has sound in under 3% of its tenths of a second (or does not exist)."""
        if not path.exists():
            return True
        x = np.fromfile(path, dtype=np.int16, offset=44).astype(np.float32) / 32768
        n = len(x) // 1600 * 1600
        return not n or float((np.abs(x[:n]).reshape(-1, 1600).max(axis=1) > 0.02).mean()) < share

    def _who(self, row: dict, k: int) -> None:
        import speakers
        t0 = time.time()
        try:
            sys.path.insert(0, str(ROOT))
            from indite.core import load_audio
            meet = row.get("kind") == "meeting"
            others = meet and row.get("others")              # the call's sound was captured: split only that track
            if others and self._silent(store.AUDIO / f"{row['id']}-others.wav"):
                # captured, but nobody spoke through it: an in-person conversation (18 Oct: everyone in the room came
                # out as "You"). Then the people are all on the mic, so split the mic track instead.
                print("speakers: the call's track is silent - splitting the microphone")
                others = False
            path = (store.AUDIO / f"{row['id']}-{'others' if others else 'you'}.wav") if meet else store.audio_of(row)
            if not path or not Path(path).exists():
                raise RuntimeError("the audio for this note is not on this Mac any more")
            audio, _ = load_audio(path)
            spans, n = speakers.turns(audio, k)
            if n == 1 and not others:
                # one voice: a file stays unlabelled; a mic-only meeting is just you
                if meet:
                    segs = [dict(s, speaker="You") for s in row.get("segments", [])]
                    store.update(row["id"], segments=segs, speakers=1, speakers_guessed=k == 0,
                                 text="\n".join(f"You: {s['text']}" for s in segs) or row["text"])
                else:
                    store.update(row["id"], speakers=1, speakers_guessed=k == 0)
                return
            label = (lambda i: f"Person {i + 1}") if others else (lambda i: f"Speaker {i + 1}")
            segs = [s for s in row.get("segments", []) if others and s.get("speaker") == "You"]
            for a, b, who in spans:
                at = a
                # 0.4 s of lead-in: the cut is found in 0.75 s steps and can land just after a turn's first word
                # (measured: "CleverTap wala" lost its first word without it; no repeated words with it)
                for p in pieces(audio[int(max(0.0, a - 0.4) * RATE):int(b * RATE)]):
                    text = self.tidy(self.engine.transcribe(p)) if float(np.sqrt(np.mean(p ** 2))) > 0.004 else ""
                    if text:
                        segs.append({"start": round(at, 2), "end": round(at + len(p) / RATE, 2),
                                     "speaker": label(who), "text": text, "k": 1 if others else 0})
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

    def demo_cmd(self) -> None:
        """Instructions from mac/demo.py, the demo-video runner (main thread). Only reads its own data folder."""
        lines = DEMO_CMD.read_text().splitlines()
        DEMO_CMD.unlink(missing_ok=True)
        for line in lines:
            verb, _, arg = line.partition(":")
            if verb == "open":
                self.open_window(None)
            elif verb == "private":                            # developer check: same as the menu item
                self.toggle_no_save()
            elif verb == "quit" and store.TEST:                # the test copy: mac/testcopy.py stop
                self.quit_all(None)
            elif verb == "place" and self.window:            # x,y,w,h in screen points, from the top-left
                from AppKit import NSScreen, NSMakeRect
                x, y, w, h = (float(v) for v in arg.split(","))
                top = NSScreen.screens()[0].frame().size.height
                self.window.win.setFrame_display_(NSMakeRect(x, top - y - h, w, h), True)
            elif verb == "js" and self.window:
                self.window.bridge.js(arg)
            elif verb == "eval" and self.window and self.window.bridge.web is not None:
                # developer check: a JS expression's value goes to eval.out - never the founder's clipboard (17 Oct)
                def done(result, error):
                    (store.DIR / "eval.out").write_text(str(error) if error else json.dumps(result, default=str))
                self.window.bridge.web.evaluateJavaScript_completionHandler_(f"JSON.stringify({arg})", done)
            elif verb == "file":
                threading.Thread(target=self.transcribe_file, args=(Path(arg),), daemon=True).start()
            elif verb == "ai":                                # on the newest dictation
                row = next((r for r in store.history() if (r.get("kind") or "dictation") == "dictation"), None)
                if row:
                    self.ai_busy[row["id"]] = ai.ACTIONS[arg][0]
                    self.refresh()
                    threading.Thread(target=self._ai, args=(row, arg, ""), daemon=True).start()
            elif verb == "confidence":                    # developer check: per-word confidence for a note's audio
                threading.Thread(target=self._confidence_check, args=(arg,), daemon=True).start()
            elif verb == "mictest":                       # developer check: the real Mic, for N seconds
                threading.Thread(target=self._mictest, args=(float(arg or 3),), daemon=True).start()
            elif verb == "type":                          # developer check: type into whatever is in front
                self.typer.type(arg)
            elif verb == "card":                          # developer check: card for the newest dictation, press button N
                row = next((r for r in store.history() if (r.get("kind") or "dictation") == "dictation"), None)
                if row:
                    self.card_note = row["id"]
                    self.preview.show(row["text"], buttons=True)
                    self.card_action(int(arg or 1))
            elif verb == "dictate":                       # developer check: a WAV through the real path after release
                with wave.open(arg) as w:
                    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
                self.busy = True
                threading.Thread(target=self.write_it, args=(audio,), daemon=True).start()
            elif verb == "pill":
                self.pill.set_clear(int(arg))
                self.done_state, self.done_until = "done", time.time() + 2.0
            elif verb == "pref":
                k, _, v = arg.partition("=")
                store.set_pref(k, json.loads(v))
                self.reload_prefs()
                self.refresh()
            elif verb == "rec":                               # rec:start:<path>:x,y,w,h  or  rec:stop
                from recorder import Recorder
                what, _, rest = arg.partition(":")
                if what == "start":
                    path, _, rect = rest.rpartition(":")
                    self.recorder = Recorder(Path(path), tuple(float(v) for v in rect.split(",")),
                                             store.DIR / "rec.state")
                    self.recorder.start()
                elif getattr(self, "recorder", None):
                    self.recorder.stop()
            elif verb == "run":                               # the runner, started from here so it has indite's
                subprocess.Popen([sys.executable, "-u", str(Path(__file__).parent / "demo.py")] + arg.split(),
                                 stdout=open(store.DIR / "demo.log", "a"), stderr=subprocess.STDOUT)

    def _confidence_check(self, note_id: str) -> None:
        """Writes every word and how sure the engine was, for the newest note or the one named."""
        sys.path.insert(0, str(ROOT))
        from indite.core import load_audio
        rows = store.history()
        row = next((r for r in rows if r["id"] == note_id), None) or next((r for r in rows if store.audio_of(r)), None)
        out = store.DIR / "confidence.json"
        try:
            path = store.audio_of(row) if row else None
            if not path:
                out.write_text(json.dumps({"error": "no note with audio kept"}))
                return
            audio, _ = load_audio(Path(path))
            t0 = time.time()
            words = self.engine.confidence(audio)
            out.write_text(json.dumps({"note": row["id"], "seconds": round(len(audio) / RATE, 1),
                                       "took": round(time.time() - t0, 2),
                                       "unsure": [[w, round(p, 2)] for w, p in words if p < 0.9],
                                       "words": [[w, round(p, 3)] for w, p in words]}, indent=1))
        except Exception as e:                            # noqa: BLE001
            out.write_text(json.dumps({"error": f"{type(e).__name__}: {e}"}))

    def _mictest(self, seconds: float) -> None:
        """Opens the microphone exactly as a key press does, and writes down what came back."""
        out, levels = store.DIR / "mictest.json", []
        try:
            self.mic.start()
            end = time.time() + seconds
            while time.time() < end:
                levels.append(round(self.mic.level, 4))
                time.sleep(0.1)
            audio = self.mic.stop()
            text = ""
            if len(audio) >= RATE // 2:
                text = self.tidy(self.engine.transcribe(audio))
            wav = store.DIR / "mictest.wav"              # kept, so the audio itself can be listened to and re-run
            with wave.open(str(wav), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(RATE)
                w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
            rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) else 0.0
            out.write_text(json.dumps({"mic": self.mic.using, "seconds": round(len(audio) / RATE, 2),
                                       "loudest": max(levels or [0]), "rms": round(rms, 5),
                                       "peak": round(float(np.abs(audio).max()) if len(audio) else 0.0, 4),
                                       "heard": text}, indent=1))
        except Exception as e:                            # noqa: BLE001
            out.write_text(json.dumps({"error": f"{type(e).__name__}: {e}"}, indent=1))

    def set_title(self, text: str) -> None:
        """
        The menu-bar title, set safely from any thread.

        rumps writes straight into AppKit, and AppKit's layout engine must only be touched on the main thread. Doing
        it from a worker killed the whole start-up thread once the main thread had drawn anything (16 Oct: warm_up
        died with NSInternalInconsistencyException, and the app sat there with no engine and a frozen pill).
        """
        text = status_text(text) or ("private" if getattr(self, "no_save_next", False) else "")   # the mark stays until used
        if threading.current_thread() is threading.main_thread():
            self.title = text
            return
        from PyObjCTools import AppHelper
        AppHelper.callAfter(lambda: setattr(self, "title", text))

    def show_pill(self) -> None:
        """Settings changed the pill's look: show it for a moment so the change can be seen."""
        if not (self.started_at or self.busy or self.meeting.running):
            self.done_state, self.done_until = "done", time.time() + 2.5

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
            body, ext = srt({"segments": store.named_segments(row)}), ".srt"
        else:
            body, ext = (row.get("improved") or row["text"]) if fmt == "improved" else store.named_text(row), ".txt"
        body = self.out(body)
        panel = NSSavePanel.savePanel()
        panel.setNameFieldStringValue_(name + ext)
        if run_modal(panel) == 1 and panel.URL():
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
    if "--selftest" in sys.argv:                         # uv run python mac/indite_mac.py --selftest
        assert apply_fixes("Thik hai. thik", {"thik": "theek"}) == "Theek hai. theek"   # a capital stays
        assert apply_fixes("PTM", {"ptm": "Paytm"}) == "Paytm"
        from pynput.keyboard import _darwin as kbd
        assert kbd.Listener._handle_message.__name__ == "handle_except_media"            # media keys never reach pynput
        assert kbd.Listener._handle_message(None, None, kbd.NSSystemDefined, None, None, False) is None
        assert [status_text(t) for t in ("🎙", "🎙⚠", "🎙…", "🔴", "⏳", "📄 3/10")] == ["", "⚠", "…", "●", "…", "3/10"]
        assert menubar_icon().isTemplate() and menubar_icon().size().width == 18
        assert utf16_chunks("", 20) == []
        assert utf16_chunks("hello", 20) == ["hello"]
        assert utf16_chunks("abcdef", 2) == ["ab", "cd", "ef"]
        long = "Kal ki meeting chaar baje hai, please sab ko reminder bhej dena. " * 8
        assert "".join(utf16_chunks(long, 20)) == long           # nothing added, nothing lost
        assert all(len(c.encode("utf-16-le")) // 2 <= 20 for c in utf16_chunks(long, 20))
        emoji = "a\U0001F600b"                                   # one emoji is 2 UTF-16 units
        for n in (1, 2, 3, 4):
            parts = utf16_chunks(emoji, n)
            assert "".join(parts) == emoji
            assert all(len(p.encode("utf-16-le")) // 2 <= max(n, 2) for p in parts), (n, parts)
        print("ok")
        sys.exit(0)
    if store.TEST:                                       # own log; a modal alert would appear on the founder's screen
        sys.stdout = sys.stderr = open(store.DIR / "indite.log", "a", buffering=1, encoding="utf-8")
        rumps.alert = lambda *a, **k: print("alert (not shown):", a, k)
    InditeApp().run()
