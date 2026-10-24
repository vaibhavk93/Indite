"""
Notice a call starting, so Inditeflow can ASK "Record this call?" (roadmap Mac later; never records by itself).

A call = one of the known call apps is using the microphone. macOS 14+ says which processes use audio input
(CoreAudio's process objects), so nothing here needs a new permission: no screen reading, no window titles.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import struct

# bundle id -> the name to show. Browsers are not here: they use the mic for much more than calls, so they are asked
# about only after BROWSER_SECS of steady use (BROWSERS below; founder's decision, 24 Oct: Meet and Zoom run in a tab).
CALL_APPS = {
    "us.zoom.xos": "Zoom",
    "com.microsoft.teams2": "Teams", "com.microsoft.teams": "Teams",
    "com.tinyspeck.slackmacgap": "Slack",
    "com.apple.FaceTime": "FaceTime",
    "net.whatsapp.WhatsApp": "WhatsApp", "desktop.WhatsApp": "WhatsApp",
    "com.cisco.webexmeetingsapp": "Webex", "Cisco-Systems.Spark": "Webex",
    "com.hnc.Discord": "Discord", "com.skype.skype": "Skype",
}

BROWSERS = {
    "com.google.Chrome": "Chrome", "com.apple.Safari": "Safari", "org.mozilla.firefox": "Firefox",
    "com.microsoft.edgemac": "Edge", "company.thebrowser.Browser": "Arc", "com.brave.Browser": "Brave",
    "com.operasoftware.Opera": "Opera", "com.vivaldi.Vivaldi": "Vivaldi",
}
BROWSER_SECS = 60        # a call lasts; a voice search or a dictation tab does not

_ca = None


class _Addr(ctypes.Structure):
    _fields_ = [("sel", ctypes.c_uint32), ("scope", ctypes.c_uint32), ("elem", ctypes.c_uint32)]


def _cc(s: str) -> int:
    return struct.unpack(">I", s.encode())[0]


def _get(obj: int, sel: str, size: int) -> bytes | None:
    global _ca
    _ca = _ca or ctypes.CDLL(ctypes.util.find_library("CoreAudio"))
    a, n = _Addr(_cc(sel), _cc("glob"), 0), ctypes.c_uint32(size)
    buf = ctypes.create_string_buffer(size)
    if _ca.AudioObjectGetPropertyData(ctypes.c_uint32(obj), ctypes.byref(a), 0, None, ctypes.byref(n), buf):
        return None
    return buf.raw[:n.value]


def _app_of(pid: int) -> str:
    """The bundle id of a process, or of the app it belongs to (helpers: "com.microsoft.teams2.helper")."""
    from AppKit import NSRunningApplication
    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
    return str(app.bundleIdentifier() or "") if app else ""


def mic_users() -> list[str]:
    """Bundle ids of the processes using the microphone right now (macOS 14+; [] when it cannot tell)."""
    raw = _get(1, "prs#", 4 * 512)                        # kAudioHardwarePropertyProcessObjectList
    out = []
    for (obj,) in struct.iter_unpack("I", raw or b""):
        on = _get(obj, "piri", 4)                         # kAudioProcessPropertyIsRunningInput
        pid = _get(obj, "ppid", 4)                        # kAudioProcessPropertyPID
        if on and pid and struct.unpack("I", on)[0]:
            out.append(_app_of(struct.unpack("i", pid)[0]))
    return out


def _match(users: list[str], table: dict[str, str]) -> str:
    return next((name for b in users for app, name in table.items() if b == app or b.startswith(app + ".")), "")


def call_app() -> str:
    """The name of a call app using the mic now, or ""."""
    return _match(mic_users(), CALL_APPS)


def mic_now() -> tuple[str, str]:
    """(call app, browser) using the mic now; "" for each that is not. One look at the mic, so both agree."""
    users = mic_users()
    return _match(users, CALL_APPS), _match(users, BROWSERS)


if __name__ == "__main__":       # python mac/calls.py  - what is using the mic right now
    print("using the mic:", mic_users() or "nothing")
    print("call app:", call_app() or "none", "| browser:", mic_now()[1] or "none")
    assert _match(["com.google.Chrome.helper"], BROWSERS) == "Chrome" and _match(["com.google.Chromex"], BROWSERS) == ""
    assert all(isinstance(v, str) and v for v in CALL_APPS.values())
    print("ok")
