"""
What the Mac is playing - the other people in a call - captured with ScreenCaptureKit (macOS 13+).

A meeting recording keeps two tracks: the microphone (you) and this (them). On headphones the mic never hears the
others at all, which is why a mic-only recorder misses half of every online call. Needs the Screen Recording
permission (System Settings → Privacy & Security → Screen & System Audio Recording); no picture is ever kept -
the video side is set to 2 x 2 pixels, once a minute, and thrown away.
"""

from __future__ import annotations

import queue
import threading
import time

import numpy as np

RATE = 16_000
_Out = None


def _output_class():
    """
    The receiver for ScreenCaptureKit's audio, defined once per process. Objective-C refuses a second class with the
    same name, so defining it inside start() made every meeting after the first in a session fail to start
    ("Out is overriding existing Objective-C class", 16 Oct). Each recording points its own instance at itself.
    """
    global _Out
    if _Out is None:
        import ScreenCaptureKit as SC
        import CoreMedia as CM
        from Foundation import NSObject

        class Out(NSObject):
            def stream_didOutputSampleBuffer_ofType_(self, _stream, buf, kind):   # noqa: N802
                if kind != SC.SCStreamOutputTypeAudio:
                    return
                block = CM.CMSampleBufferGetDataBuffer(buf)
                if block is None:
                    return
                n = CM.CMBlockBufferGetDataLength(block)
                err, data = CM.CMBlockBufferCopyDataBytes(block, 0, n, None)
                if err == 0 and data:
                    x = np.frombuffer(bytes(data), dtype=np.float32)
                    x = x[: len(x) // 3 * 3].reshape(-1, 3).mean(axis=1)       # 48 kHz -> 16 kHz
                    self.me.last = time.time()
                    self.me.q.put((self.me.last, x.astype(np.float32)))  # stamped: a restart leaves a gap to fill
                    self.me.level = float(np.sqrt(np.mean(x ** 2)) * 12) if len(x) else 0.0

            def stream_didStopWithError_(self, _stream, error):                 # noqa: N802
                self.me.error = str(error)
                print("system audio stopped:", error, flush=True)

        _Out = Out
    return _Out


class SystemAudio:
    def __init__(self) -> None:
        self.q: queue.Queue[np.ndarray] = queue.Queue()
        self.stream = None
        self.error = ""
        self.level = 0.0
        self.last = time.time()       # when the last sound arrived (silence arrives too, as long as capture runs)

    def start(self, timeout: float = 5.0) -> bool:
        """True once audio is flowing; False with self.error set (usually: permission not given)."""
        import ScreenCaptureKit as SC
        import CoreMedia as CM

        ready = threading.Event()
        self.out = _output_class().alloc().init()
        self.out.me = self                                  # where this recording's audio goes

        def got(content, error):
            if error is not None or content is None:
                self.error = str(error or "no screen to capture")
                ready.set()
                return
            filt = SC.SCContentFilter.alloc().initWithDisplay_excludingWindows_(content.displays()[0], [])
            cfg = SC.SCStreamConfiguration.alloc().init()
            cfg.setCapturesAudio_(True)
            cfg.setExcludesCurrentProcessAudio_(True)       # never record Inditeflow's own sounds
            cfg.setSampleRate_(48000)
            cfg.setChannelCount_(1)
            cfg.setWidth_(2)
            cfg.setHeight_(2)
            cfg.setMinimumFrameInterval_(CM.CMTimeMake(60, 1))
            self.stream = SC.SCStream.alloc().initWithFilter_configuration_delegate_(filt, cfg, self.out)
            ok, err = self.stream.addStreamOutput_type_sampleHandlerQueue_error_(
                self.out, SC.SCStreamOutputTypeAudio, None, None)
            if not ok:
                self.error = str(err)
                ready.set()
                return

            def started(e):
                if e is not None:
                    self.error = str(e)
                ready.set()
            self.stream.startCaptureWithCompletionHandler_(started)

        SC.SCShareableContent.getShareableContentWithCompletionHandler_(got)
        ready.wait(timeout)
        if not ready.is_set():
            self.error = "macOS did not answer (is the Screen Recording permission waiting for you?)"
        return not self.error

    def stop(self) -> np.ndarray:
        if self.stream is not None:
            done = threading.Event()
            self.stream.stopCaptureWithCompletionHandler_(lambda e: done.set())
            done.wait(3.0)
            self.stream = None
        chunks = []
        while not self.q.empty():
            chunks.append(self.q.get())
        return chunks                                            # [(arrival time, samples)], like the queue


if __name__ == "__main__":       # play a sound, capture it: python mac/system_audio.py
    import subprocess
    import time
    s = SystemAudio()
    print("start:", s.start(), s.error)
    subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
    time.sleep(2.5)
    a = np.concatenate([x for _, x in s.stop()] or [np.zeros(0, np.float32)])
    print(f"captured {len(a) / RATE:.1f} s, peak {float(np.abs(a).max()) if len(a) else 0:.3f}")
