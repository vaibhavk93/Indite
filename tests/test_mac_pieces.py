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
