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

    def stop(self):
        return []                                   # [(arrival time, samples)], like SystemAudio


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


def test_the_others_keep_the_meetings_clock_through_silence(tmp_path, monkeypatch):
    # the Mac sends nothing while nobody plays sound: 1 s of talk at 0 s, then 1 s at 10 s must be stamped 10 s
    monkeypatch.setattr(store, "HISTORY", tmp_path / "h.jsonl")
    monkeypatch.setattr(store, "AUDIO", tmp_path / "audio")
    monkeypatch.setattr(meeting, "SystemAudio", FakeSys)
    app = App()
    app.engine.gate.set()
    m = meeting.Meeting(app)
    m.start()
    m.running = False                                                    # no background loop: pumped by hand below
    t0, s = m.t0, np.full(meeting.RATE, 0.2, np.float32)
    m.sys.q.put((t0 + 1.0, s))
    m.sys.q.put((t0 + 11.0, s))
    while not m.sys.q.empty():
        m.others(*m.sys.q.get())
    m.pump(force=True)
    starts = [x["start"] for x in m.segments if x["speaker"] == "Others"]
    assert starts == [0.0, 10.0], starts
    m.them.wav.close()
    with __import__("wave").open(str(store.AUDIO / f"{m.note}-others.wav")) as w:
        assert abs(w.getnframes() / meeting.RATE - 11.0) < 0.01          # the file is as long as the meeting
