"""
Turns the demo runner's screen recording and timeline into the finished video: the screen as recorded, with the
narration and the spoken Hinglish laid on one soundtrack at the moments they happened.

    python mac/demo_make.py <out_dir> [lag_seconds]   -> <out_dir>/indite-demo.mp4

lag = how long after the recording started the runner's clock began (it waits ~1.5 s for screencapture to start).
"""

from __future__ import annotations

import json
import sys
import wave
from fractions import Fraction
from pathlib import Path

import av
import numpy as np

OUT = Path(sys.argv[1])
LAG = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
RATE = 44100

src = av.open(str(OUT / "screen.mov"))
vin = src.streams.video[0]
length = float(vin.duration * vin.time_base) if vin.duration else float(src.duration) / 1e6
track = np.zeros(int((length + 2) * RATE), dtype=np.float32)
for item in json.loads((OUT / "timeline.json").read_text())["items"]:
    with wave.open(item["wav"]) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    i = int((item["at"] + LAG) * RATE)
    gain = 0.75 if item.get("speech") else 1.0           # the "user" a touch quieter than the narrator
    track[i:i + len(x)] += x[: max(0, len(track) - i)] * gain
track = np.clip(track, -1, 1)

dst = av.open(str(OUT / "indite-demo.mp4"), "w")
vout = dst.add_stream("h264_videotoolbox", rate=60)
vout.width, vout.height = vin.codec_context.width - vin.codec_context.width % 2, vin.codec_context.height - vin.codec_context.height % 2
vout.pix_fmt = "yuv420p"
vout.bit_rate = 6_000_000
aout = dst.add_stream("aac", rate=RATE)
aout.layout = "mono"

for frame in src.decode(vin):
    f = frame.reformat(width=vout.width, height=vout.height, format="yuv420p")
    f.pts = int(frame.time * 60) if frame.time is not None else None
    f.time_base = Fraction(1, 60)
    for p in vout.encode(f):
        dst.mux(p)
for p in vout.encode():
    dst.mux(p)

pcm = (track * 32767).astype(np.int16).reshape(1, -1)
for i in range(0, pcm.shape[1], 1024):
    af = av.AudioFrame.from_ndarray(pcm[:, i:i + 1024], format="s16", layout="mono")
    af.sample_rate = RATE
    af.pts = i
    for p in aout.encode(af):
        dst.mux(p)
for p in aout.encode():
    dst.mux(p)
dst.close()
print(f"made {OUT / 'indite-demo.mp4'}: {length:.0f} s")
