"""
The demo-video runner. Started BY indite (`run:` in demo.cmd), so it inherits indite's Accessibility and Screen
Recording permissions: it records the screen, presses the real hotkeys, and steers the window - a real run of the
app, not screenshots. Run it only against a demo profile (INDITE_DATA), never a person's real notes.

    python mac/demo.py <out_dir>     -> <out_dir>/screen.mov + timeline.json (then mac/demo_make.py makes the mp4)

The "speaker" is synthetic Hinglish speech (macOS voice Tara) fed into indite in place of the microphone; the
narrator (macOS voice Aman) is added afterwards from the timeline.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import Quartz
from AppKit import NSRunningApplication, NSWorkspace

import store

OUT = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), "/tmp/indite-demo"))
OUT.mkdir(parents=True, exist_ok=True)
CMD, FEED = store.DIR / "demo.cmd", store.DIR / "demo_feed.wav"
NARRATOR, SPEAKER = "Aman (English (India))", "Tara (English (India))"
ROOT = Path(__file__).resolve().parent.parent
timeline: list[dict] = []
T0 = 0.0


def log(*a) -> None:
    print(f"{time.time() - T0:6.1f}", *a, flush=True)


CLIPS: dict[str, tuple[Path, Path, float]] = {}


def render(text: str, voice: str, name: str) -> tuple[Path, Path, float]:
    """
    Speech to a 44.1 kHz WAV (soundtrack) and a 16 kHz WAV (for indite), with 0.35 s of silence in front so the
    first word is not clipped. Made BEFORE recording starts: `say` froze for 8 minutes once, mid-recording.
    """
    if (voice, text) in CLIPS:
        return CLIPS[(voice, text)]
    aiff = OUT / f"{name}.aiff"
    for _ in range(3):
        try:
            subprocess.run(["say", "-v", voice, "-r", "175", "-o", str(aiff), "[[slnc 350]] " + text], check=True,
                           timeout=60)
            break
        except subprocess.TimeoutExpired:
            continue
    hi, lo = OUT / f"{name}.wav", OUT / f"{name}-16k.wav"
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@44100", "-c", "1", str(aiff), str(hi)], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(aiff), str(lo)], check=True)
    import wave
    with wave.open(str(hi)) as w:
        CLIPS[(voice, text)] = (hi, lo, w.getnframes() / w.getframerate())
    return CLIPS[(voice, text)]


def cmd(*lines: str) -> None:
    with open(CMD, "a") as f:
        f.write("\n".join(lines) + "\n")
    time.sleep(0.6)                                   # the app reads it within 0.25 s


def say(text: str, gap: float = 0.4) -> None:
    """Narration: logged on the timeline, and the script waits as long as it lasts so pictures and words line up."""
    hi, _, dur = render(text, NARRATOR, f"n{len(CLIPS):02d}")
    timeline.append({"at": time.time() - T0, "wav": str(hi)})
    log("narrate:", text[:60])
    time.sleep(dur + gap)


def key(code: int, mask: int, down: bool) -> None:
    """A modifier key press as macOS sends it: a flags-changed event (what indite's key listener reads)."""
    e = Quartz.CGEventCreateKeyboardEvent(None, code, down)
    Quartz.CGEventSetType(e, Quartz.kCGEventFlagsChanged)
    Quartz.CGEventSetFlags(e, mask if down else 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


R_OPT, R_CMD = (61, Quartz.kCGEventFlagMaskAlternate | 0x40), (54, Quartz.kCGEventFlagMaskCommand | 0x10)


def speak_into_indite(text: str, name: str, hands_free: bool = False) -> None:
    """The user's part: hold Right ⌥ (or tap Right ⌘ three times), the speech plays into indite, then let go."""
    hi, lo, dur = render(text, SPEAKER, name)
    if hands_free:                                    # lock first, then the speech: the taps open and close the mic
        for i in range(3):
            if i == 2:
                (OUT / "feed.wav").write_bytes(lo.read_bytes())
                (OUT / "feed.wav").replace(FEED)     # the third tap's press is the one that keeps listening
            key(*R_CMD, True); time.sleep(0.08); key(*R_CMD, False); time.sleep(0.15)
    else:
        (OUT / "feed.wav").write_bytes(lo.read_bytes())
        (OUT / "feed.wav").replace(FEED)
        key(*R_OPT, True)
    time.sleep(0.25)
    timeline.append({"at": time.time() - T0, "wav": str(hi), "speech": True})
    log("speak:", text[:60])
    time.sleep(dur + 0.6)
    if hands_free:
        key(*R_CMD, True); time.sleep(0.08); key(*R_CMD, False)
    else:
        key(*R_OPT, False)


def display() -> tuple[float, float]:
    from AppKit import NSScreen
    f = NSScreen.screens()[0].frame()
    return f.size.width, f.size.height


def chord(*codes_masks) -> None:
    """Press keys together, release in reverse: e.g. ⌃⌘V for paste-last."""
    held = 0
    for code, mask in codes_masks:
        held |= mask
        e = Quartz.CGEventCreateKeyboardEvent(None, code, True)
        if mask:
            Quartz.CGEventSetType(e, Quartz.kCGEventFlagsChanged)
        Quartz.CGEventSetFlags(e, held)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
        time.sleep(0.05)
    for code, mask in reversed(codes_masks):
        held &= ~mask
        e = Quartz.CGEventCreateKeyboardEvent(None, code, False)
        if mask:
            Quartz.CGEventSetType(e, Quartz.kCGEventFlagsChanged)
        Quartz.CGEventSetFlags(e, held)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
        time.sleep(0.05)


L_CTRL, L_CMD, V, ESC = (59, Quartz.kCGEventFlagMaskControl | 0x1), (55, Quartz.kCGEventFlagMaskCommand | 0x8), (9, 0), (53, 0)


def pid_of(app_name: str) -> int:
    """By process name. NSWorkspace's app list goes stale in a process with no run loop, so ask the system."""
    if app_name == "indite":
        return os.getppid()                           # the runner is started by indite itself
    for _ in range(20):
        r = subprocess.run(["pgrep", "-x", app_name], capture_output=True, text=True)
        if r.stdout.strip():
            return int(r.stdout.split()[0])
        time.sleep(0.3)
    raise RuntimeError(f"{app_name} is not running")


def ax_place(app_name: str, x: float, y: float, w: float, h: float) -> None:
    """Move another app's front window with the Accessibility API (indite's permission; no Automation prompt)."""
    from ApplicationServices import (AXUIElementCreateApplication, AXUIElementCopyAttributeValue,
                                     AXUIElementSetAttributeValue, AXValueCreate, kAXPositionAttribute,
                                     kAXSizeAttribute, kAXValueCGPointType, kAXValueCGSizeType, kAXWindowsAttribute)
    el = AXUIElementCreateApplication(pid_of(app_name))
    wins = None
    for _ in range(40):                                  # an app that was hidden, or still opening, has no window yet
        NSRunningApplication.runningApplicationWithProcessIdentifier_(pid_of(app_name)).unhide()
        err, wins = AXUIElementCopyAttributeValue(el, kAXWindowsAttribute, None)
        if not err and wins:
            break
        time.sleep(0.3)
    if not wins:
        log(f"{app_name} has no window to place - carrying on without moving it")
        return
    win = wins[0]
    AXUIElementSetAttributeValue(win, kAXPositionAttribute, AXValueCreate(kAXValueCGPointType, Quartz.CGPoint(x, y)))
    AXUIElementSetAttributeValue(win, kAXSizeAttribute, AXValueCreate(kAXValueCGSizeType, Quartz.CGSize(w, h)))


def front(app_name: str) -> None:
    a = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid_of(app_name))
    if a:
        a.activateWithOptions_(1 << 1)


def main() -> None:
    global T0
    hidden: list = []
    rec = None
    try:
        prerender()
        stage(hidden)
        state = store.DIR / "rec.state"
        state.unlink(missing_ok=True)
        W, H = display()
        cmd(f"rec:start:{OUT / 'screen.mov'}:0,0,{W},{H}")              # the whole screen
        for _ in range(60):
            if state.exists() and state.read_text() != "starting":
                break
            time.sleep(0.25)
        if not state.exists() or state.read_text() != "recording":
            raise RuntimeError(f"screen recording did not start: {state.read_text() if state.exists() else 'no answer'}")
        rec = True
        time.sleep(0.5)
        T0 = time.time()
        if "--script" in sys.argv:
            show_script()
        elif "--short" in sys.argv:
            show_short()
        else:
            show()
    finally:
        if rec:
            cmd("rec:stop")
            for _ in range(40):
                if (store.DIR / "rec.state").read_text() == "stopped":
                    break
                time.sleep(0.25)
            time.sleep(1.0)
        (OUT / "timeline.json").write_text(json.dumps({"t0_lag": 1.5, "items": timeline}, indent=1))
        from Foundation import NSDate, NSRunLoop
        # 16 Oct: a crash in stage() left every hidden app hidden. unhide() only queues the request - it needs the
        # run loop to deliver it - so ask, pump, and check, until nothing is left hidden.
        for _ in range(5):
            left = []
            for pid in hidden:
                a = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
                if a and a.isHidden():
                    a.unhide()
                    left.append(a.localizedName())
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(1.5))
            if not left:
                break
        if left:
            log("still hidden after asking five times:", ", ".join(left))
        log("done")


SCRIPT_N = N = [
    "This is indite. It turns spoken Hinglish into text, right on your Mac. No internet, and no account.",
    "Click into any app. Hold the right Option key, and just speak.",
    "The pill above the Dock listens, then writes. About a second for a sentence like that, and the "
    "words are typed - chaar baje became four, in digits.",
    "For longer thoughts, tap the right Command key three times, and talk hands free.",
    "One tap ends it. The whole thought is typed, and a card shows exactly what was written.",
    "Changed your mind? Press Escape while speaking, and nothing is typed.",
    "And Control Command V types your last dictation again, wherever you are.",
    "Every dictation is saved here, privately, on this Mac.",
    "Ask AI works on any note: improve it, summarise it, pull out action items, rewrite or translate it - "
    "or turn a rambling thought into a clean prompt for any other AI.",
    "Improve keeps your original right next to the new version, so nothing you said is lost.",
    "Every note AI has touched keeps a gold edge, so you can find your AI work at a glance, "
    "and open it again any time.",
    "Have a recording already? Drop in a call or a voice note.",
    "indite writes it down, and works out who spoke, without a single click.",
    "Meetings work live. Your microphone is you, and the call's sound is everyone else, even on headphones.",
    "When you stop, the other voices are told apart, and you can rename them.",
    "Anything can become a to-do, from a note or from AI's action items.",
    "The dictionary teaches indite the words it gets wrong, like your company names.",
    "Insights shows how much you dictate, how fast you speak, the time you save, and what you asked AI for.",
    "The pill can be as clear or as frosted as you like.",
    "AI is off until you turn it on, with your own Claude login or your own key.",
    "And Help lists every shortcut, and what to do if something is off.",
    "indite. Speak Hinglish, get text, and keep it all on your Mac.",
]
SCRIPT_S = [
    ("Kal ki meeting chaar baje hai, please sab ko reminder bhej dena.", "s1"),
    ("Aur haan, client ke saath call ke baad, deck mein last quarter ke numbers update karne hain, aur Rohit ko "
     "Friday tak final version bhejna hai.", "s2"),
    ("Arre nahi, yeh mat likho.", "s3"),
    ("Chalo shuru karte hain, aaj ka agenda dashboard aur budget hai.", "s4"),
]


def prerender() -> None:
    if "--script" in sys.argv:
        missing = [n for n, _ in script_lines() if not human(n)]
        log(f"recorded: {len(script_lines()) - len(missing)} of {len(script_lines())}"
            + (f"; synthetic for {', '.join(missing[:8])}{'...' if len(missing) > 8 else ''}" if missing else ""))
        return
    if "--short" in sys.argv:
        for i, t in enumerate(SHORT_N):
            render(t, NARRATOR, f"s{i:02d}")
        for t, n in SHORT_S:
            render(t, SPEAKER, n)
        log(f"{len(CLIPS)} voice clips ready (short cut)")
        return
    for i, t in enumerate(SCRIPT_N):
        render(t, NARRATOR, f"n{i:02d}")
    for t, n in SCRIPT_S:
        render(t, SPEAKER, n)
    log(f"{len(CLIPS)} voice clips ready")


def stage(hidden: list) -> None:
    """Only TextEdit and indite on screen; every other app hidden (main() shows them again at the end)."""
    for a in NSWorkspace.sharedWorkspace().runningApplications():
        if a.activationPolicy() == 0 and a.localizedName() not in ("indite", "TextEdit", "Finder", "python3", "Python"):
            if not a.isHidden() and a.hide():
                hidden.append(a.processIdentifier())
    note = OUT / "Message to the team.txt"
    note.write_text("")
    for _ in range(10):                                  # TextEdit with no document shows no window at all
        subprocess.run(["open", "-a", "TextEdit", str(note)])
        time.sleep(1.5)
        r = subprocess.run(["osascript", "-e", 'tell application "TextEdit" to count documents'],
                           capture_output=True, text=True)
        if (r.stdout.strip() or "0") != "0":
            break
    else:
        log("TextEdit would not open a document")
    # The meeting/file -> AI warning is a modal: in a demo it would stop the take dead. Answer it up front, the
    # same way a user who ticked "don't ask again" would have (the warning itself is shown in the Ask AI scene).
    cmd('pref:ai_ok_meetings=true')
    W, H = display()
    if {"--short", "--script"} & set(sys.argv):                   # these fill the screen per beat instead
        cmd("open", "js:go('home')")
        ax_place("TextEdit", 0, 25, W, H - 25)
    else:
        ax_place("TextEdit", 0, 25, W / 2, H - 25)                # split: TextEdit left, indite right
        cmd("open", f"place:{W / 2},{25},{W / 2},{H - 25}", "js:go('home')")
    time.sleep(1.5)




def show() -> None:
    import wave
    call = OUT / "client-call.wav"                         # the file: the first 75 s of a two-person test call
    with wave.open(str(ROOT / "bench_synth/dialogue_2spk.wav")) as src, wave.open(str(call), "wb") as dst:
        dst.setparams(src.getparams())
        dst.writeframes(src.readframes(75 * src.getframerate()))
    them = OUT / "meeting-them.wav"                        # what the other people say in the live meeting
    with wave.open(str(ROOT / "bench_synth/dialogue_2spk.wav")) as src, wave.open(str(them), "wb") as dst:
        src.setpos(120 * src.getframerate())
        dst.setparams(src.getparams())
        dst.writeframes(src.readframes(22 * src.getframerate()))

    # 1 - dictation, live
    say(N[0])
    front("TextEdit")
    say(N[1])
    speak_into_indite(*SCRIPT_S[0])
    time.sleep(2.0)
    say(N[2])
    # 2 - hands-free, live
    say(N[3])
    speak_into_indite(*SCRIPT_S[1], hands_free=True)
    time.sleep(3.0)
    say(N[4])
    # 3 - cancel and paste-last, live
    say(N[5])
    hi, lo, dur = render(*SCRIPT_S[2][:1], SPEAKER, SCRIPT_S[2][1])
    (OUT / "feed.wav").write_bytes(lo.read_bytes()); (OUT / "feed.wav").replace(FEED)
    key(*R_OPT, True); time.sleep(0.25)
    timeline.append({"at": time.time() - T0, "wav": str(hi), "speech": True})
    time.sleep(min(dur, 2.2))
    chord(ESC); key(*R_OPT, False)
    time.sleep(1.5)
    say(N[6])
    chord(L_CTRL, L_CMD, V)
    time.sleep(2.0)
    # 4 - the notes, AI, live
    front("indite")
    cmd("js:go('home')")
    say(N[7])
    cmd("js:openDrawer(S.history.find(r => (r.kind || 'dictation') === 'dictation').id)")
    say(N[8])
    cmd("ai:improve")
    time.sleep(9.0)
    say(N[9])
    cmd("js:closeDrawer()")
    say(N[10])                                         # the gold edge is on the row, so the drawer is shut first
    # 5 - a file, live, with who spoke
    cmd("js:go('files')", f"file:{call}")
    say(N[11])
    time.sleep(12.0)
    say(N[12])
    # 6 - a meeting, live: the mic says one line, the call (played through the Mac) is the others
    cmd("js:go('meetings')")
    say(N[13])
    hi, lo, dur = render(*SCRIPT_S[3][:1], SPEAKER, SCRIPT_S[3][1])
    (OUT / "feed.wav").write_bytes(lo.read_bytes()); (OUT / "feed.wav").replace(FEED)
    cmd("js:document.querySelector('#meet').click()")
    timeline.append({"at": time.time() - T0 + 0.6, "wav": str(hi), "speech": True})
    time.sleep(dur + 1.0)
    play = subprocess.Popen(["afplay", str(them)])
    timeline.append({"at": time.time() - T0, "wav": str(them), "speech": True})
    play.wait()
    time.sleep(2.5)
    cmd("js:document.querySelector('#meet').click()")
    say(N[14])
    time.sleep(6.0)
    # 7 - the rest, a short tour
    cmd("js:go('todo')"); say(N[15])
    cmd("js:go('dict')"); say(N[16])
    cmd("js:go('insights')"); say(N[17])
    cmd("js:go('settings'); sgo('pill')"); say(N[18])
    for p in (30, 70, 100, 60):
        cmd(f"pill:{p}")
        time.sleep(0.8)
    cmd("js:sgo('ai')"); say(N[19])
    cmd("js:go('help')"); say(N[20])
    say(N[21], gap=1.5)


# ---- the short cut (docs/DEMO_PLAN.md §8): 8 beats, ~3:20, for leadership --------------------------------------
# The long run above stays as the detailed walkthrough. This one drops 12 scenes and merges 2: the hero starts at
# second zero and the problem is spoken over it, the Wi-Fi-off menu bar does the privacy claim without a word of
# marketing, a real error gets fixed on camera, and the live meeting is cut because its permission is the one thing
# still unproven in a real call.
SHORT_N = [
    # 1 - hero, with the problem spoken over it
    "Typing Hinglish is slow. You think in two languages and your keyboard only knows one. So: hold a key, and talk.",
    # 2 - the claim the screen proves by itself
    "That was this Mac alone. The Wi-Fi is off, there is no account, and nothing was uploaded. "
    "Chaar baje came out as four, in digits.",
    # 3 - a long, real thought, hands free
    "For a longer thought, tap the right Command key three times and keep your hands free.",
    "One tap ends it, and the whole thing is typed where you were already working.",
    # 4 - honest accuracy
    "It gets about one word in seven wrong today, and company names are the usual casualty. "
    "So you teach it once, in the dictionary, and it stops getting that word wrong.",
    # 5 - a recording, and who said what
    "It also takes a recording you already have - a call, a voice note - and writes it down.",
    "And it works out who said what, without being told how many people there were.",
    # 6 - your own AI, your own account
    "AI is optional, and it runs on your own account, not ours. Ask it to improve a note and your original stays "
    "beside it, so nothing you actually said is lost.",
    # 7 - what it is
    "indite. Speak Hinglish, get text, and keep every word on your own Mac.",
    # 8 - the ask
    "It works today, on this machine. What it needs next is a handful of people willing to use it for a week.",
]

SHORT_S = [
    ("Kal ki meeting chaar baje hai, please sab ko reminder bhej dena.", "h1"),
    ("Client ke saath call ke baad, deck mein last quarter ke numbers update karne hain, "
     "aur Rohit ko Friday tak final version bhejna hai.", "h2"),
]


def fill(app_name: str) -> None:
    """
    Brings an app to the front and makes its window fill the screen, below the menu bar.

    Not macOS full screen (the green button): a Dock app's panels cannot appear over another app's full screen, so
    the pill - the thing this whole video is about - would be invisible. A maximised window looks the same on camera
    and keeps the pill, and leaves the menu bar in shot, where the Wi-Fi being off is the privacy claim.
    """
    front(app_name)
    w, h = display()
    if app_name == "indite":
        cmd(f"place:0,{MENUBAR},{w},{h - MENUBAR}")
    else:
        ax_place(app_name, 0, MENUBAR, w, h - MENUBAR)
    time.sleep(0.8)


MENUBAR = 25.0


def show_short() -> None:
    """The 3:20 cut. Same real app, same real engine - only fewer scenes."""
    S = SHORT_N
    call = OUT / "client-call.wav"
    import wave
    with wave.open(str(ROOT / "bench_synth/dialogue_2spk.wav")) as src, wave.open(str(call), "wb") as dst:
        dst.setparams(src.getparams())
        dst.writeframes(src.readframes(75 * src.getframerate()))

    # 1 + 2 - the hero, unbroken, with the menu bar (and the Wi-Fi state) in frame
    fill("TextEdit")
    say(S[0])
    speak_into_indite(*SHORT_S[0])
    time.sleep(2.5)
    say(S[1])
    # 3 - hands free, a real sentence
    say(S[2])
    speak_into_indite(*SHORT_S[1], hands_free=True)
    time.sleep(3.0)
    say(S[3])
    # 4 - the error, and the dictionary that fixes it
    fill("indite")
    cmd("js:go('dict')")
    say(S[4])
    time.sleep(2.0)
    # 5 - a recording, and who spoke
    cmd("js:go('files')", f"file:{call}")
    say(S[5])
    time.sleep(12.0)
    say(S[6])
    # 6 - AI on your own account, original kept
    cmd("js:go('home')")
    cmd("js:openDrawer(S.history.find(r => (r.kind || 'dictation') === 'dictation').id)")
    cmd("ai:improve")
    say(S[7])
    time.sleep(6.0)
    cmd("js:closeDrawer()")
    # 7 + 8 - what it is, and the ask
    say(S[8])
    say(S[9], gap=1.5)


# ---- the scripted run: docs/DEMO_SCRIPT.md, in the founder's own voice ------------------------------------------
# The words live in the script file and nowhere else, so editing the script changes the video. A line recorded by
# mac/narrate.py is used as it is; anything not recorded yet falls back to a synthetic voice, which is fine for a
# rehearsal and NOT fine for the real take (take 1: the engine wrote "Tier cloist amok p acting" for a sentence it
# gets right every time from a person).
VOICES = Path("/tmp/indite-demo-voice")

# Which lines are spoken hands-free, and how long the screen holds after a line before anything moves. The founder's
# note on take 1: "everything is running so fast that the user is not able to track it" - so results sit still.
HANDS_FREE = {"S02"}
HOLD = {"S01": 5.0, "S02": 6.0, "S03": 5.0, "S04": 5.0, "S05": 4.0,
        "N07": 2.5, "N14": 2.0, "N18": 3.0, "N24": 3.0, "N25": 2.5, "N26": 2.0, "N32": 3.0, "N36": 2.0}


def human(name: str) -> tuple[Path, Path, float] | None:
    """The founder's own recording of this line, if it has been made."""
    hi, lo = VOICES / f"{name}.wav", VOICES / f"{name}-16k.wav"
    if not (hi.exists() and lo.exists()):
        return None
    import wave
    with wave.open(str(hi)) as w:
        return hi, lo, w.getnframes() / w.getframerate()


def line_audio(name: str, words: str, narration: bool) -> tuple[Path, Path, float]:
    got = human(name)
    if got:
        return got
    log(f"{name}: no recording - falling back to a synthetic voice")
    return render(words, NARRATOR if narration else SPEAKER, name.lower())


def say_line(name: str, words: str) -> None:
    hi, _lo, dur = line_audio(name, words, True)
    timeline.append({"at": time.time() - T0, "wav": str(hi)})
    log("narrate:", name, words[:55])
    time.sleep(dur + 0.4)


def dictate(name: str, words: str) -> None:
    """Hold the hotkey and play this line into indite in place of the microphone."""
    hi, lo, dur = line_audio(name, words, False)
    hands = name in HANDS_FREE
    if hands:
        for i in range(3):
            if i == 2:
                (OUT / "feed.wav").write_bytes(lo.read_bytes())
                (OUT / "feed.wav").replace(FEED)
            key(*R_CMD, True); time.sleep(0.08); key(*R_CMD, False); time.sleep(0.15)
    else:
        (OUT / "feed.wav").write_bytes(lo.read_bytes())
        (OUT / "feed.wav").replace(FEED)
        key(*R_OPT, True)
    time.sleep(0.25)
    timeline.append({"at": time.time() - T0, "wav": str(hi), "speech": True})
    log("speak:", name, words[:55])
    time.sleep(dur + 0.6)
    if hands:
        key(*R_CMD, True); time.sleep(0.08); key(*R_CMD, False)
    else:
        key(*R_OPT, False)


def script_lines() -> list[tuple[str, str]]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import narrate
    return narrate.lines()


def before(name: str, call: Path) -> None:
    """What has to be on screen before this line is spoken."""
    if name == "N01":
        fill("TextEdit")
    elif name == "N13":                                  # the mistake is made in a real app, not in indite
        fill("TextEdit")
    elif name == "N14":                                  # teach the word, on camera
        fill("indite")
        cmd("js:go('dict')")
        time.sleep(1.5)
    elif name == "S04":
        fill("TextEdit")
    elif name == "N17":
        fill("indite")
        cmd("js:go('files')", f"file:{call}")
    elif name == "N21":
        cmd("js:go('todo')")
    elif name == "N23":
        cmd("js:go('home')")
        cmd("js:openDrawer(S.history.find(r => (r.kind || 'dictation') === 'dictation').id)")
    elif name == "N25":
        cmd("ai:improve")
    elif name == "N30":
        cmd("js:closeDrawer()", "js:go('insights')")
    elif name == "N31":
        fill("TextEdit")
    elif name == "N36":
        fill("indite")
        cmd("js:go('home')")


# The word indite gets wrong in section 3, and what it should be. Filled in after testing the founder's own S03
# recording - never guessed, because a demo that fakes its own mistake is worse than one that has none. Written by
# tools/check_fix.py into this file's sibling so the take and the test cannot drift apart.
FIX_FILE = Path("/tmp/indite-demo-voice/fix.txt")


def teach_the_word() -> None:
    """Type the fix into the Dictionary, on camera, the way a person would."""
    if not FIX_FILE.exists():
        log("no fix.txt - section 3 will show the mistake but not the cure")
        return
    heard, _, want = FIX_FILE.read_text().strip().partition("=")
    heard, want = heard.strip(), want.strip()
    if not (heard and want):
        log("fix.txt is not 'heard = want'; skipping the Dictionary beat")
        return
    cmd(f"js:(()=>{{const h=document.querySelector('#dh'),w=document.querySelector('#dw');"
        f"h.focus();h.value={heard!r};w.value={want!r};}})()")
    time.sleep(1.6)                                      # the words sit there long enough to be read
    cmd("js:document.querySelector('#dadd').click()")
    log(f"taught: {heard} -> {want}")
    time.sleep(2.0)


def show_script() -> None:
    """The whole video, driven by docs/DEMO_SCRIPT.md."""
    import wave as _wave
    call = OUT / "client-call.wav"
    with _wave.open(str(ROOT / "bench_synth/dialogue_2spk.wav")) as src, _wave.open(str(call), "wb") as dst:
        dst.setparams(src.getparams())
        dst.writeframes(src.readframes(75 * src.getframerate()))

    state = store.DIR / "rec.state"
    for name, words in script_lines():
        # A take that quietly stops recording halfway is worse than one that fails: you only find out afterwards.
        if state.exists() and state.read_text().startswith("error"):
            log("STOPPING -", state.read_text())
            raise RuntimeError(state.read_text())
        before(name, call)
        if name.startswith("S"):
            dictate(name, words)
        else:
            say_line(name, words)
        if name == "N14":                                # the cure, right after the line that promises it
            teach_the_word()
        time.sleep(HOLD.get(name, 1.2))                  # the screen holds still long enough to be read


if __name__ == "__main__":
    main()
