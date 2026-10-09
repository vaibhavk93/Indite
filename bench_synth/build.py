"""Build the synthetic Hinglish benchmark from sentences.tsv using macOS `say`.

Run:  cd bench_synth && uv run --with numpy --with soundfile python build.py
Makes: clean/, noisy10/, noisy5/ (+ noisy_manifest.tsv), dialogue_2spk.wav, dialogue_same_gender.wav,
       dialogue_turns.tsv, dialogue_same_gender_turns.tsv, long_15min.wav, long_15min_ref.tsv.
Voices: A = Lekha (hi_IN, reads the Devanagari column). B = Rishi (en_IN male, reads the Roman column).
        Same-gender dialogue: B = Tara (en_IN female). Long file pass 3: A = Tara.
"""
import csv
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 16000
HERE = Path(__file__).parent
TTS = HERE / "out/tts"
rng = np.random.default_rng(7)  # fixed seed: same files every build

rows = list(csv.DictReader(open(HERE / "sentences.tsv"), delimiter="\t"))


def tts(voice: str, text: str, name: str) -> np.ndarray:
    wav = TTS / voice / f"{name}.wav"
    if not wav.exists():
        wav.parent.mkdir(parents=True, exist_ok=True)
        aiff = wav.with_suffix(".aiff")
        subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(aiff), str(wav)], check=True)
        aiff.unlink()
    x, _ = sf.read(wav, dtype="float32")
    return trim(x)


def trim(x, thr=0.01, pad=0.1):
    idx = np.flatnonzero(np.abs(x) > thr)
    if not len(idx):
        return x
    p = int(pad * SR)
    return x[max(0, idx[0] - p): idx[-1] + p]


def roman_for_say(t: str) -> str:
    return re.sub(r"₹\s?(\d+)", r"\1 rupees", t)  # en_IN voices: speak amounts in a known form


def clip(row, voice):
    text = row["devanagari_for_tts"] if voice == "Lekha" else roman_for_say(row["roman_text"])
    return tts(voice, text, row["id"])


# ---------- noise ----------
def colored(n, power):  # power 1 = pink, 2 = brown
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.arange(len(spec)); f[0] = 1
    x = np.fft.irfft(spec / f ** (power / 2), n)
    return (x / np.std(x)).astype("float32")


def fan(n):
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * 100 * k * t + rng.uniform(0, 6.28)) / k for k in range(1, 6))
    x = x * (1 + 0.1 * np.sin(2 * np.pi * 0.5 * t)) + 0.3 * colored(n, 1)  # hum + slight wobble + air
    return (x / np.std(x)).astype("float32")


def babble(n, exclude):
    pool = [r for r in rows if r["id"] != exclude]
    x = np.zeros(n, "float32")
    for r in rng.choice(pool, 4, replace=False):
        c = clip(r, "Tara")
        c = np.tile(c, n // len(c) + 1)[:n]
        x += np.roll(c, rng.integers(n))
    return x / np.std(x)


def noise(kind, n, exclude=""):
    return {"pink": lambda: colored(n, 1), "brown": lambda: colored(n, 2), "fan": lambda: fan(n),
            "babble": lambda: babble(n, exclude)}[kind]()


def mix(speech, kind, snr_db, rid):
    n = noise(kind, len(speech), rid)
    p_s = np.mean(speech[np.abs(speech) > 0.01] ** 2)  # power over voiced samples only
    n *= np.sqrt(p_s / 10 ** (snr_db / 10))
    return speech + n


def save(path, x):
    x = np.asarray(x, "float32")
    peak = np.max(np.abs(x))
    if peak > 0.99:
        x = x * 0.99 / peak
    sf.write(HERE / path, x, SR, subtype="PCM_16")


def voice_for(row, b_voice, a_voice="Lekha"):
    return a_voice if row["speaker"] == "A" else b_voice


# ---------- a. clean + b. noisy ----------
for d in ("clean", "noisy10", "noisy5"):
    (HERE / d).mkdir(exist_ok=True)
kinds = ["pink", "brown", "fan", "babble"]
with open(HERE / "noisy_manifest.tsv", "w") as man:
    man.write("id\tnoise\tsnr_db\n")
    for i, r in enumerate(rows):
        x = clip(r, voice_for(r, "Rishi"))
        save(f"clean/{r['id']}.wav", x)
        k = kinds[i % 4]
        for snr in (10, 5):
            save(f"noisy{snr}/{r['id']}.wav", mix(x, k, snr, r["id"]))
            man.write(f"{r['id']}\t{k}\t{snr}\n")


# ---------- c. dialogues ----------
def dialogue(b_voice, a_voice="Lekha", gap_lo=0.3, gap_hi=1.5):
    parts, turns, t = [], [], 0.5
    parts.append(np.zeros(int(0.5 * SR), "float32"))
    for r in rows:
        if turns:  # pause before each turn; quick replies come fast
            short = len(r["roman_text"].split()) <= 3
            gap = rng.uniform(0.15, 0.4) if short else rng.uniform(gap_lo, gap_hi)
            parts.append(np.zeros(int(gap * SR), "float32"))
            t += int(gap * SR) / SR
        x = clip(r, voice_for(r, b_voice, a_voice))
        turns.append((round(t, 3), round(t + len(x) / SR, 3), r["speaker"], r["roman_text"], r["id"]))
        parts.append(x)
        t += len(x) / SR
    return np.concatenate(parts), turns


def write_turns(path, turns):
    with open(HERE / path, "w") as f:
        f.write("start\tend\tspeaker\troman_text\tid\n")
        for tr in turns:
            f.write("\t".join(map(str, tr)) + "\n")


x, turns = dialogue("Rishi")
save("dialogue_2spk.wav", x + 0.002 * colored(len(x), 1))  # faint room noise
write_turns("dialogue_turns.tsv", turns)
x, turns = dialogue("Tara")
save("dialogue_same_gender.wav", x + 0.002 * colored(len(x), 1))
write_turns("dialogue_same_gender_turns.tsv", turns)

# ---------- d. long file: 3 passes over the sentences, with no-speech stretches ----------
passes = [("Lekha", "Rishi"), ("Lekha", "Tara"), ("Tara", "Rishi")]
breaks = {20: ("fan", 20), 45: ("pink", 15), 80: ("silence", 10), 110: ("brown", 15), 150: ("fan", 20)}
parts, ref, t, k = [np.zeros(SR, "float32")], [], 1.0, 0
for a_v, b_v in passes:
    for r in rows:
        x = clip(r, voice_for(r, b_v, a_v))
        ref.append((round(t, 3), round(t + len(x) / SR, 3), "speech", r["speaker"], r["roman_text"], r["id"]))
        parts.append(x); t += len(x) / SR
        gap = np.zeros(int(rng.uniform(0.5, 2.0) * SR), "float32")
        parts.append(gap); t += len(gap) / SR
        k += 1
        if k in breaks:
            kind, sec = breaks[k]
            n = int(sec * SR)
            y = np.zeros(n, "float32") if kind == "silence" else 0.05 * noise(kind, n)
            ref.append((round(t, 3), round(t + n / SR, 3), kind, "-", "", "-"))
            parts.append(y); t += n / SR
            parts.append(np.zeros(SR, "float32")); t += 1.0
x = np.concatenate(parts)
save("long_15min.wav", x + 0.002 * colored(len(x), 1))
with open(HERE / "long_15min_ref.tsv", "w") as f:
    f.write("start\tend\tkind\tspeaker\troman_text\tid\n")
    for tr in ref:
        f.write("\t".join(map(str, tr)) + "\n")
print(f"long_15min.wav: {len(x) / SR / 60:.1f} min; dialogue_2spk end {turns[-1][1] / 60:.1f} min")
