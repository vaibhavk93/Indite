"""The Mac app cuts long holds into pieces: every sample kept, none over 20 s, the cut in the quiet."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mac"))
from indite_mac import RATE, pieces  # noqa: E402


def test_long_hold_is_cut_in_the_quiet_and_loses_nothing():
    rng = np.random.default_rng(0)
    audio = rng.normal(0, 0.3, 65 * RATE).astype(np.float32)
    audio[int(17 * RATE):int(17.5 * RATE)] = 0          # one pause, inside the 15-20 s search range
    out = pieces(audio)
    assert sum(len(p) for p in out) == len(audio)
    assert np.array_equal(np.concatenate(out), audio)
    assert all(len(p) <= 20 * RATE for p in out)
    assert 17 * RATE <= len(out[0]) <= 17.5 * RATE      # the first cut landed in the pause


def test_short_hold_is_untouched():
    audio = np.zeros(8 * RATE, dtype=np.float32)
    assert len(pieces(audio)) == 1


def test_a_stuck_coreaudio_is_noticed_and_restarts_at_most_once_in_10_minutes(tmp_path, monkeypatch):
    import threading
    from indite_mac import Mic, MicStuck, restart_allowed
    m = Mic()
    monkeypatch.setattr(m, "_start", threading.Event().wait)   # an open that never comes back, like the deadlock
    for _ in range(2):                                           # the second press fails at once, without waiting
        try:
            m.start(wait=0.2)
            raise AssertionError("a stuck open must raise MicStuck")
        except MicStuck:
            pass
    assert m.stuck
    mark = tmp_path / "mic-restart.last"
    assert restart_allowed(mark) and not restart_allowed(mark)


def test_the_text_cards_two_ai_buttons_follow_use():
    from indite_mac import card_slots, slot_title
    assert card_slots({}) == [("prompt", ""), ("rewrite", "Formal English")]                 # nothing asked yet
    assert card_slots({"translate|Hindi (Devanagari)": 3, "summary|": 2, "prompt|": 1}) == [
        ("translate", "Hindi (Devanagari)"), ("summary", "")]                                # most asked first
    assert card_slots({"rewrite|Polite": 2, "rewrite|Formal English": 1}) == [("rewrite", "Polite"), ("prompt", "")]
    used = {"summary|": 5, "prompt|": 3}
    assert card_slots(used, ["translate|Hindi (Devanagari)", ""]) == [("translate", "Hindi (Devanagari)"), ("summary", "")]
    assert card_slots(used, ["", "summary|"]) == [("prompt", ""), ("summary", "")]                 # a pin keeps its own place
    assert card_slots(used, ["summary|", "summary|"]) == [("summary", ""), ("prompt", "")]         # never the same twice
    assert card_slots(used, ["gone|x", "custom|hi"]) == [("summary", ""), ("prompt", "")]          # a bad pin = automatic
    assert slot_title("translate", "Hindi (Devanagari)") == "Translate · Hindi"
    assert slot_title("prompt", "") == "Make it a prompt"


def test_a_card_button_picked_in_settings_shows_at_once(tmp_path, monkeypatch):
    import indite_mac as m
    monkeypatch.setattr(m.store, "PREFS", tmp_path / "prefs.json")
    a = m.InditeApp.__new__(m.InditeApp)
    titles = []
    a.preview = type("P", (), {"set_titles": lambda s, t: titles.append(t)})()
    a.mic = type("M", (), {"chosen": ""})()
    a.pill = type("Pi", (), {"set_clear": lambda s, v: None})()
    a.prefs = m.store.prefs()
    a.set_card_buttons()
    m.store.set_pref("card_buttons", ["summary|", ""])
    a.reload_prefs()
    assert titles[-1][0] == "Summary" and len(titles) == 2
    a.reload_prefs()                                       # nothing changed: the buttons stay as they are
    assert len(titles) == 2
