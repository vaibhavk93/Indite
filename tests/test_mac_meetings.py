"""Back-to-back meetings: the next one starts while the last is finishing, and neither gets the other's audio."""
import queue
import sys
import threading
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mac"))
import meeting  # noqa: E402
import store    # noqa: E402


class FakeMic:
    def __init__(self):
        self.q = queue.Queue()

    def start(self):
        self.q = queue.Queue()                      # like Mic.start: a new queue per recording

    def stop(self):
        out = []
        while not self.q.empty():
            out.append(self.q.get())
        return np.concatenate(out).flatten() if out else np.zeros(0, np.float32)


class FakeSys(FakeMic):
    def start(self):
        return True


class Engine:
    def __init__(self):
        self.gate = threading.Event()

    def transcribe(self, piece):
        self.gate.wait(5)                           # a slow last piece: A is still finishing while B starts
        return "baat"


class App:
    def __init__(self):
        self.mic, self.engine, self.ai_busy, self.prefs = FakeMic(), Engine(), {}, {"auto_speakers": False}

    def tidy(self, t):
        return t

    def refresh(self):
        pass


def test_next_meeting_starts_while_the_last_one_finishes(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "HISTORY", tmp_path / "h.jsonl")
    monkeypatch.setattr(store, "AUDIO", tmp_path / "audio")
    monkeypatch.setattr(meeting, "SystemAudio", FakeSys)
    app = App()
    a = meeting.Meeting(app)
    a.start()
    app.mic.q.put(np.full((meeting.RATE * 3, 1), 0.2, np.float32))      # 3 s of A's voice, not yet pumped

    b = meeting.Meeting(app, after=a)
    stopping = threading.Thread(target=a.stop)
    stopping.start()
    b.start()                                                            # waits only until A has let go of the mic
    assert app.ai_busy.get(a.note) == "finishing"                        # A's row and the tab show it is working
    first = np.full((meeting.RATE * 2, 1), 0.3, np.float32)
    app.mic.q.put(first)                                                 # B's first 2 s
    app.engine.gate.set()
    stopping.join(10)
    a.pump()                                                             # a late tick of A's loop must not take it
    assert app.mic.q.qsize() == 1                                        # B's first 2 s are still there for B
    assert len(a.you.buf) == 0 and a.you.at == 3.0                       # A kept all of its own 3 s, and wrote them
    assert a.note not in app.ai_busy
    b.running = False
