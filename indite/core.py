"""Audio loading, the shared transcript format, and speech-to-text engines.

Every engine is a function: (samples, model, progress) -> list of segments.
A segment is {"start": seconds, "end": seconds, "text": str}. Output is Roman-script Hinglish.
progress(stage, fraction, new_lines, audio_seconds) is called as work moves on; if it raises, the job stops.
"""
import io
import json
import os
import re
import subprocess
import tempfile
import time
import wave
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

SR = 16_000  # every engine gets 16 kHz mono


def _quiet(*_args, **_kw):
    pass


@dataclass
class Transcript:
    engine: str
    model: str
    audio_seconds: float
    elapsed_seconds: float
    segments: list[dict] = field(default_factory=list)
    damaged_packets: int = 0  # unreadable bits of the file that were skipped

    @property
    def text(self) -> str:
        return " ".join(s["text"].strip() for s in self.segments if s["text"].strip())

    def to_dict(self) -> dict:
        return asdict(self) | {"text": self.text}


def load_audio(path) -> tuple[np.ndarray, int]:
    """Any audio or video file -> (float32 mono samples at 16 kHz, number of damaged packets skipped).

    Damaged packets are skipped like a media player would, instead of failing the whole file.
    """
    import av

    out, damaged = [], 0
    with av.open(str(path)) as container:
        if not container.streams.audio:
            raise ValueError("This file has no audio track.")
        stream = container.streams.audio[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=SR)
        for packet in container.demux(stream):
            try:
                frames = packet.decode()
            except av.error.InvalidDataError:
                damaged += 1
                continue
            for frame in frames:
                out += [f.to_ndarray().reshape(-1) for f in resampler.resample(frame)]
        out += [f.to_ndarray().reshape(-1) for f in resampler.resample(None)]
    if not out:
        raise ValueError("No readable audio found in this file.")
    return np.concatenate(out).astype(np.float32) / 32768.0, damaged


def wav_bytes(samples: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def chunks(samples: np.ndarray, seconds: float):
    """Yield (start_seconds, piece) windows of fixed length."""
    step = int(seconds * SR)
    for i in range(0, len(samples), step):
        yield i / SR, samples[i : i + step]


# ---------- engines ----------

SARVAM_URL = "https://api.sarvam.ai/speech-to-text"


def sarvam(samples: np.ndarray, model: str = "saaras:v3", progress=_quiet) -> list[dict]:
    """Sarvam REST API, 'translit' mode = Roman-script output.

    ponytail: the REST endpoint only takes ~30 s, so we cut fixed 25 s windows.
    Words at window edges can be split. Upgrade path: Sarvam Batch API (also gives speaker labels).
    """
    import httpx

    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise SystemExit("SARVAM_API_KEY is not set. Put it in .env and run with: uv run --env-file .env indite ...")
    segments, total = [], len(samples) / SR
    import ssl

    import truststore

    tls = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # system certificates, so company networks work
    with httpx.Client(timeout=120, verify=tls) as client:
        for start, piece in chunks(samples, 25):
            r = client.post(
                SARVAM_URL,
                headers={"api-subscription-key": key},
                files={"file": ("chunk.wav", wav_bytes(piece), "audio/wav")},
                data={"model": model, "mode": "translit", "language_code": "hi-IN"},
            )
            if r.status_code != 200:
                raise SystemExit(f"Sarvam error {r.status_code}: {r.text[:300]}")
            end = start + len(piece) / SR
            segments.append({"start": start, "end": end, "text": r.json().get("transcript") or ""})
            progress("transcribing", end / total, [segments[-1]["text"]], total)
    return segments


TOOLS = Path(__file__).resolve().parents[1] / ".tools"
WHISPER_CLI = TOOLS / "whisper.cpp/build/bin/whisper-cli"
LOCAL_MODEL = str(TOOLS / "models/ggml-apex-q5_0.bin")   # Apex: Whisper large-v3-turbo, Roman Hinglish, ~0.8 GB RAM
BEST_MODEL = str(TOOLS / "models/ggml-prime-q5_0.bin")   # Prime: Whisper large-v3, slower, ~2 GB RAM
_LINE = re.compile(r"^\[[\d:.]+ --> [\d:.]+\]\s*(.*)")
_NAN = re.compile(r"(?<![\w'])nan(?![\w'])")


def cut_at_pauses(speech: list[tuple[float, float]], total: float, max_len: float = 25.0, pad: float = 0.2):
    """Group speech into pieces of at most max_len seconds, cut where people pause.

    Transcribing pieces separately stops one bad stretch (a loop) from spreading into the next.
    On the 56-min test this cut loop words 73 -> 7 and ran 35% faster.
    """
    pieces, cur = [], None
    for a, b in speech:
        if cur and b - cur[0] <= max_len:
            cur[1] = b
            continue
        if cur:
            pieces.append(cur)
        cur = [a, b]
        while cur[1] - cur[0] > max_len:  # long speech with no pause: hard cut
            pieces.append([cur[0], cur[0] + max_len])
            cur = [cur[0] + max_len, cur[1]]
    if cur:
        pieces.append(cur)
    return [(max(0.0, a - pad), min(total, b + pad)) for a, b in pieces]


def _bad(text: str) -> bool:
    from .guards import has_loop

    return not text.strip() or has_loop(text, times=4) or bool(_NAN.search(text.lower()))


def _whisper(paths: list[Path], model: str, args: list[str], on_line=lambda line: None) -> list[str]:
    """One whisper-cli run over many files (model loads once). Returns the text of each file."""
    cmd = [str(WHISPER_CLI), "-m", model, "-l", "en", "-oj", "-np", *args]
    for p in paths:
        cmd += ["-f", str(p)]
    # errors="replace": whisper.cpp can print a character split across two tokens; never crash on it
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                            encoding="utf-8", errors="replace")
    log = []
    try:
        for line in proc.stdout:
            log.append(line)
            on_line(line)
        proc.wait()
    finally:
        if proc.poll() is None:  # stopped early (job cancelled): don't leave whisper running
            proc.kill()
            proc.wait()
    if proc.returncode:
        raise SystemExit(f"whisper.cpp failed: {''.join(log).strip()[-300:]}")
    out = []
    for p in paths:
        j = Path(f"{p}.json")
        out.append(" ".join(c["text"].strip() for c in json.loads(j.read_text(errors="replace"))["transcription"]) if j.exists() else "")
    return out


def local(samples: np.ndarray, model: str = LOCAL_MODEL, progress=_quiet, speech=None) -> list[dict]:
    """Free, on this machine: whisper.cpp + an Oriserve Hindi2Hinglish model (Roman script).

    1. cut the audio at pauses into pieces of <= 25 s
    2. transcribe all pieces in one whisper.cpp run
    3. re-run only the pieces that looped, came back empty or with "nan", with different settings
       (no carried-over text, warmer sampling), and keep whichever version loops less
    Set up with: sh scripts/setup_local.sh   (add --best for the Prime model)
    """
    if not WHISPER_CLI.exists() or not Path(model).exists():
        raise SystemExit("Local engine not set up. Run: sh scripts/setup_local.sh")
    total = len(samples) / SR
    if speech is None:
        from .guards import speech_ranges

        speech = speech_ranges(samples, SR)
    pieces = cut_at_pauses(speech, total)
    if not pieces:
        return []
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for i, (a, b) in enumerate(pieces):
            p = Path(d) / f"{i:05}.wav"
            p.write_bytes(wav_bytes(samples[int(a * SR): int(b * SR)]))
            paths.append(p)
        spoken = sum(b - a for a, b in pieces)

        def on_line(line):
            if m := _LINE.match(line):
                done = sum(b - a for (a, b), p in zip(pieces, paths) if Path(f"{p}.json").exists())
                progress("transcribing", min(done / spoken, 0.99), [m.group(1)], total)

        texts = _whisper(paths, model, [], on_line)
        bad = [i for i, t in enumerate(texts) if _bad(t)]
        if bad:
            progress("retrying", 0.99, [], total)
            again = _whisper([paths[i] for i in bad], model, ["-mc", "0", "-tp", "0.4"])
            from .guards import has_loop

            for i, t in zip(bad, again):
                if t.strip() and (not texts[i].strip() or not _bad(t) or (has_loop(texts[i], 4) and not has_loop(t, 4))):
                    texts[i] = t
    return [{"start": round(a, 2), "end": round(b, 2), "text": t} for (a, b), t in zip(pieces, texts)]


def local_best(samples, model=BEST_MODEL, progress=_quiet, speech=None):
    return local(samples, model, progress, speech)


ENGINES = {
    "sarvam": (sarvam, "saaras:v3"),
    "local": (local, LOCAL_MODEL),
    "local-best": (local_best, BEST_MODEL),
}

# Rupees per audio hour, for the cost column in bench. Sarvam figure is from its pricing page (Oct 2026); confirm before relying on it.
COST_PER_HOUR = {"sarvam": 30.0, "local": 0.0, "local-best": 0.0}


def available() -> dict[str, str | None]:
    """Engine -> None if ready, else the reason it can't run."""
    built = WHISPER_CLI.exists()
    return {
        "local": None if built and Path(LOCAL_MODEL).exists() else "run scripts/setup_local.sh",
        "local-best": None if built and Path(BEST_MODEL).exists() else "run scripts/setup_local.sh --best",
        "sarvam": None if os.environ.get("SARVAM_API_KEY") else "add SARVAM_API_KEY to .env",
    }


def transcribe(path, engine: str = "local", model: str | None = None, progress=_quiet) -> Transcript:
    from .guards import flag, speech_ranges

    fn, default_model = ENGINES[engine]
    model = model or default_model
    progress("reading", 0.0, [], 0)
    samples, damaged = load_audio(path)
    total = round(len(samples) / SR, 2)
    progress("finding", 0.0, [], total)
    speech = speech_ranges(samples, SR)  # found once: used to cut pieces and to flag invented text
    progress("transcribing", 0.0, [], total)
    t0 = time.perf_counter()
    segments = fn(samples, model, progress, speech=speech) if engine.startswith("local") else fn(samples, model, progress)
    elapsed = round(time.perf_counter() - t0, 2)
    progress("checking", 1.0, [], total)
    return Transcript(engine, model, total, elapsed, flag(segments, speech), damaged)
