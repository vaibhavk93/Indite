"""The hotkey state machine: hold, tap, double-tap to lock, tap to finish, Esc to cancel."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mac"))
import indite_mac as m  # noqa: E402


class FakeMic:
    def __init__(self):
        self.open = False
        self.level = 0.0

    def start(self):
        self.open = True

    def stop(self):
        self.open = False
        return np.zeros(m.RATE * 2, dtype=np.float32)       # 2 s of "speech"


def app():
    a = m.InditeApp.__new__(m.InditeApp)                    # no menu bar, no engine: just the key logic
    a.mic, a.busy, a.started_at, a.locked, a.last_tap = FakeMic(), False, 0.0, False, 0.0
    a.taps, a.hf_down = 0, 0.0
    a.meeting = type("M", (), {"running": False})()
    a.preview = type("P", (), {"hide_now": lambda s: None})()   # the text card is cleared when listening starts
    a.ops = None                                            # mic steps run at once in tests
    a.prefs = {"hotkey": "alt_r", "sounds": False, "hf_key": "", "hf_taps": 2}
    a.written = []
    a.write_it = a.written.append
    a.done_state, a.done_until = "", 0.0
    m.threading.Thread = lambda target, args, daemon: type("T", (), {"start": lambda s: target(*args)})()
    return a


K = m.keyboard.Key.alt_r


def test_hold_writes_once():
    a = app()
    a.on_press(K); a.started_at -= 2; a.on_release(K)
    assert len(a.written) == 1 and not a.mic.open


def test_single_tap_writes_nothing():
    a = app()
    a.on_press(K); a.on_release(K)
    assert a.written == [] and not a.mic.open and not a.locked


def test_double_tap_locks_then_tap_finishes():
    a = app()
    a.on_press(K); a.on_release(K)                          # tap 1
    a.on_press(K); a.on_release(K)                          # tap 2: locked, still listening
    assert a.locked and a.mic.open and a.written == []
    a.on_press(K); a.on_release(K)                          # tap 3: finish
    assert not a.locked and not a.mic.open and len(a.written) == 1


def test_esc_cancels_hands_free():
    a = app()
    a.on_press(K); a.on_release(K); a.on_press(K); a.on_release(K)
    a.on_press(m.keyboard.Key.esc)
    assert not a.locked and not a.mic.open and a.written == []


def test_slow_second_tap_is_just_a_tap():
    a = app()
    a.on_press(K); a.on_release(K)
    a.last_tap -= 1.0                                       # a second later
    a.on_press(K); a.on_release(K)
    assert not a.locked and not a.mic.open


def test_triple_tap_setting():
    a = app()
    a.prefs["hf_taps"] = 3
    for _ in range(2):
        a.on_press(K); a.on_release(K)
    assert not a.locked
    a.on_press(K); a.on_release(K)
    assert a.locked and a.mic.open


def test_separate_hands_free_key():
    a = app()
    a.prefs["hf_key"] = "cmd_r"
    R = m.keyboard.Key.cmd_r
    a.on_press(R); a.on_release(R)
    assert not a.mic.open
    a.on_press(R); a.on_release(R)                          # second tap of the other key: locked
    assert a.locked and a.mic.open
    a.on_press(R); a.on_release(R)                          # one tap stops it
    assert not a.locked and len(a.written) == 1
    a.on_press(K); a.started_at -= 2; a.on_release(K)       # holding the talk key still works as before
    assert len(a.written) == 2


if __name__ == "__main__":
    for name, f in list(globals().items()):
        if name.startswith("test_"):
            f()
    print("ok")
