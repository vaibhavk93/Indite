"""
Cleans up a narration recording: tightens the pauses, lifts the hum out, evens the loudness.

    .venv/bin/python mac/polish.py N06            # one block -> N06-polished.wav, to listen to
    .venv/bin/python mac/polish.py --all          # every recording, written beside the originals

Nothing here is clever, and that is on purpose: a voice-over that sounds processed is worse than one that sounds
like a person in a room. The originals are never overwritten - every pass writes a new file - so a bad setting
costs nothing.

What it does, in order:
  1. a high-pass filter at 80 Hz, which is below the human voice and above nothing useful - takes out desk rumble,
     the fan, and the low roar a laptop microphone picks up from a room
  2. a gentle gate: stretches quieter than the speech floor are pushed further down, not cut to silence, because a
     hard cut makes a recording sound like a phone line dropping
  3. pauses longer than KEEP seconds are shortened to KEEP - the words keep their own rhythm, only the dead air goes
  4. light compression, so the quiet lines and the loud lines sit at the same level
  5. normalise to a peak of 0.89, which is loud without ever clipping
"""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

VOICES = Path.home() / "Documents/inditeflow-demo-voice"
RATE, LOW = 44100, 16000
KEEP = 0.45          # a pause longer than this is shortened to this - about a natural breath
GAP = 1.0            # what counts as "a pause worth shortening"
PEAK = 0.72          # final loudness. Higher than this just makes the room louder too


def read(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a, w.getframerate()


def write(path: Path, audio: np.ndarray, rate: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())


def high_pass(a: np.ndarray, rate: int, hz: float = 80.0) -> np.ndarray:
    b, aa = signal.butter(2, hz / (rate / 2), btype="high")
    return signal.filtfilt(b, aa, a).astype(np.float32)


def speech_mask(a: np.ndarray, rate: int) -> np.ndarray:
    """
    True where there is speech, judged on 20 ms blocks against this recording's own quiet level.

    A take shorter than one block has nothing to judge - an empty array, or a stray Enter that caught a few
    samples - and the maths below raised IndexError on it, which killed a whole --all run part-way through and left
    the founder re-recording blind (22 Oct). Something that short is all speech or all nothing; either way, keeping
    it whole is right and costs nothing.
    """
    win = max(1, int(0.02 * rate))
    n = len(a) // win
    if n < 1:
        return np.ones(len(a), dtype=bool)
    level = np.abs(a[: n * win].reshape(n, win)).max(axis=1)
    floor = float(np.percentile(level, 20))
    peak = float(np.percentile(level, 95))
    gate = max(floor * 2.5, peak * 0.03)   # conservative: better to keep breath than lose a word
    loud = level > gate
    # don't chop the quiet start or end of a word: a block counts as speech if a neighbour is speech
    pad = np.convolve(loud.astype(float), np.ones(7), mode="same") > 0
    mask = np.repeat(pad, win)
    if len(mask) < len(a):                               # the last partial block: treat it like its neighbour
        mask = np.concatenate([mask, np.full(len(a) - len(mask), mask[-1] if len(mask) else True)])
    return mask[: len(a)]


def denoise(a: np.ndarray, rate: int, speech: np.ndarray, over: float = 2.0, floor: float = 0.08) -> np.ndarray:
    """
    Takes the room out, by learning what the room sounds like and subtracting it.

    A gate only turns the hiss down between words; while someone is talking the hiss is still there, underneath. The
    fix is to measure the noise's own shape - its spectrum - during the quiet stretches, and subtract that shape from
    every moment, speech included. What is left is the voice.

    `over` subtracts a bit more than measured, because noise moves about; `floor` is how much is always left behind,
    since subtracting all of it makes the famous underwater warble. Both are deliberately mild: this recording's
    noise is 45 dB below the voice, so there is not much to take and plenty to spoil.
    """
    nfft = 1024
    f, t, Z = signal.stft(a, rate, nperseg=nfft, noverlap=nfft * 3 // 4)
    mag, phase = np.abs(Z), np.angle(Z)
    # the noise's shape, learned from the frames with no speech in them
    step = len(a) / max(len(t), 1)
    quiet_frame = np.array([not speech[min(int(i * step), len(speech) - 1)] for i in range(len(t))])
    if quiet_frame.sum() < 4:                            # hardly any silence: fall back to the quietest frames
        energy = mag.sum(axis=0)
        quiet_frame = energy <= np.percentile(energy, 10)
    noise = np.median(mag[:, quiet_frame], axis=1, keepdims=True)
    clean = np.maximum(mag - over * noise, floor * mag)
    _, out = signal.istft(clean * np.exp(1j * phase), rate, nperseg=nfft, noverlap=nfft * 3 // 4)
    return out[: len(a)].astype(np.float32)


def duck(a: np.ndarray, speech: np.ndarray, by: float = 0.45) -> np.ndarray:
    """Push the non-speech down instead of cutting it, with a 50 ms slope so it is never heard happening."""
    g = np.where(speech, 1.0, by)
    k = np.ones(int(0.05 * RATE)) / int(0.05 * RATE)
    return a * np.convolve(g, k, mode="same")


def tighten(a: np.ndarray, speech: np.ndarray, rate: int) -> tuple[np.ndarray, int]:
    """
    Shorten every silence longer than GAP to KEEP, and report how many speech samples survived.

    The count is structural, not measured again afterwards: re-running the detector on the shortened audio judges it
    against different levels and reports speech as missing when none was touched (16 Oct). Here, a speech run is
    copied whole or not at all, so the number is exact.
    """
    out, gap, keep, kept = [], int(GAP * rate), int(KEEP * rate), 0
    if not len(a):                                       # nothing to walk: empty in, empty out, nothing kept
        return a, 0
    # np.diff marks the sample BEFORE a change, so the boundary is one later. Without the +1 a run was labelled by
    # its neighbour's state, and whole words were trimmed as if they were silence (16 Oct).
    edges = np.flatnonzero(np.diff(speech.astype(np.int8))) + 1
    runs, start = [], 0
    for e in list(edges) + [len(speech)]:
        runs.append((start, e, bool(speech[start])))
        start = e
    for s, e, is_speech in runs:
        chunk = a[s:e]
        if is_speech:
            kept += len(chunk)                           # speech runs are copied whole, never trimmed
        elif len(chunk) > gap:
            head = chunk[: keep // 2]
            tail = chunk[-(keep - keep // 2):]
            chunk = np.concatenate([head, tail])
        out.append(chunk)
    return (np.concatenate(out) if out else a), kept


def compress(a: np.ndarray, rate: int, threshold: float = 0.18, ratio: float = 2.5) -> np.ndarray:
    """Light compression on a 150 ms envelope: the quiet sentences come up, the loud ones stay put."""
    env = np.abs(a)
    k = np.ones(int(0.15 * rate)) / int(0.15 * rate)
    env = np.convolve(env, k, mode="same") + 1e-6
    over = np.maximum(env / threshold, 1.0)
    return a / over ** (1 - 1 / ratio)


def polish(path: Path) -> tuple[Path, float, float]:
    a, rate = read(path)
    before = len(a) / rate
    a = high_pass(a, rate)
    speech = speech_mask(a, rate)                        # computed ONCE: ducking moves the levels the mask is
    want = int(speech.sum())
    a = denoise(a, rate, speech)                         # take the room out before anything is made louder
    a = duck(a, speech)
    a, kept = tighten(a, speech, rate)
    if kept != want:                                     # the one rule: only silence may ever be removed
        raise RuntimeError(f"{path.stem}: {(want - kept) / rate:.2f}s of speech was dropped")
    a = compress(a, rate)
    a = a / max(float(np.abs(a).max()), 1e-6) * PEAK
    out = path.with_name(path.stem + "-polished.wav")
    write(out, a, rate)
    lo = signal.resample_poly(a, LOW, rate).astype(np.float32)
    write(path.with_name(path.stem + "-polished-16k.wav"), lo, LOW)
    return out, before, len(a) / rate


def main() -> None:
    names = [x for x in sys.argv[1:] if not x.startswith("--")]
    if "--all" in sys.argv:
        names = sorted(p.stem for p in VOICES.glob("*.wav")
                       if not p.stem.endswith(("-16k", "-polished")) and "-polished" not in p.stem)
    if not names:
        sys.exit("which one? e.g. mac/polish.py N06   (or --all)")
    total_before = total_after = 0.0
    bad: list[str] = []
    for name in names:
        src = VOICES / f"{name}.wav"
        if not src.exists():
            print(f"  {name}: not recorded")
            continue
        try:
            out, before, after = polish(src)
        except Exception as e:                           # noqa: BLE001 - one bad take must not end the run
            bad.append(name)
            print(f"  {name:5} SKIPPED - {type(e).__name__}: {e}")
            continue
        total_before += before
        total_after += after
        print(f"  {name:5} {before:6.1f}s -> {after:6.1f}s  ({before - after:4.1f}s of dead air removed)")
    if len(names) > 1:
        print(f"\n  total {total_before/60:.1f} min -> {total_after/60:.1f} min")
    if bad:                                              # said once, at the end, where it cannot be scrolled past
        print(f"  ⚠ {len(bad)} could not be tidied and still have their raw take: {' '.join(bad)}")
        print(f"    record them again:  .venv/bin/python mac/narrate.py --blocks {' '.join(bad)}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:                         # .venv/bin/python mac/polish.py --selftest
        rate = RATE
        word = np.sin(np.arange(int(0.5 * rate)) * 2 * np.pi * 220 / rate) * 0.3
        quiet = np.zeros(int(2.0 * rate), dtype=np.float32)      # a 2 s pause: longer than GAP
        a = np.concatenate([word, quiet, word, quiet, word]).astype(np.float32)
        mask = speech_mask(a, rate)
        out, kept = tighten(a, mask, rate)
        assert kept == int(mask.sum()), (kept, int(mask.sum()))  # speech is never trimmed
        assert len(out) < len(a), "the pauses were not shortened"
        assert len(out) > 3 * len(word) * 0.9, "it cut into the words"
        # the boundary bug: a run must be labelled by its own state, not its neighbour's
        flips = np.flatnonzero(np.diff(mask.astype(np.int8))) + 1
        assert all(mask[i] != mask[i - 1] for i in flips), "run boundaries are off by one"
        for tiny in (np.zeros(0, dtype=np.float32), np.array([0.5], dtype=np.float32),
                     np.zeros(int(0.005 * rate), dtype=np.float32)):
            m = speech_mask(tiny, rate)                  # used to raise IndexError and end a whole --all run
            assert len(m) == len(tiny), (len(m), len(tiny))
            got, kept = tighten(tiny, m, rate)
            assert len(got) == len(tiny) and kept == int(m.sum())
        print(f"ok - {len(a)/rate:.1f}s -> {len(out)/rate:.1f}s, no speech touched; short takes survive")
        sys.exit(0)
    main()
