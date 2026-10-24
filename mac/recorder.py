"""
Records part of the screen to a .mov with ScreenCaptureKit (SCRecordingOutput, macOS 15+). Used only by the demo
video: it runs INSIDE Inditeflow, because macOS gives the Screen Recording permission to Inditeflow and not to a program
inditeflow starts (`screencapture -v` exited 1 with no message; a child process got "user declined").
"""

from __future__ import annotations

from pathlib import Path

import objc
from Foundation import NSObject


class _StreamWatch(NSObject):
    """
    Hears ScreenCaptureKit when it gives up.

    Both the stream and the recording output take a delegate, and both were None, so a stream that stopped on its
    own - the machine busy transcribing a file, in the one take we had - simply ended the video early and said
    nothing. Whatever it reports now lands in the state file, where the runner and the log can see it.
    """

    def initWithSay_(self, say):                         # noqa: N802 - Objective-C naming
        self = objc.super(_StreamWatch, self).init()
        self._say = say
        return self

    def stream_didStopWithError_(self, stream, error) -> None:   # noqa: N802
        self._say(f"error: the screen recording stopped early - {error}")

    def recordingOutput_didFailWithError_(self, out, error) -> None:   # noqa: N802
        self._say(f"error: writing the video failed - {error}")

    def recordingOutputDidFinishRecording_(self, out) -> None:   # noqa: N802
        self._say("stopped")


class Recorder:
    def __init__(self, path: Path, rect: tuple[float, float, float, float], state: Path) -> None:
        self.path, self.rect, self.state = path, rect, state
        self.stream = None

    def _say(self, text: str) -> None:
        self.state.write_text(text)

    def start(self) -> None:
        """Returns at once; writes "recording" (or the error) into the state file when ScreenCaptureKit answers."""
        import CoreMedia as CM
        import Quartz
        import ScreenCaptureKit as SC
        from Foundation import NSURL
        self._say("starting")

        def got(content, err):
            if err is not None or content is None:
                self._say(f"error: {err}")
                return
            filt = SC.SCContentFilter.alloc().initWithDisplay_excludingWindows_(content.displays()[0], [])
            cfg = SC.SCStreamConfiguration.alloc().init()
            x, y, w, h = self.rect
            cfg.setSourceRect_(Quartz.CGRectMake(x, y, w, h))
            scale = min(2.0, 1920 / w)                    # sharp, but a full screen stays 1920 wide
            cfg.setWidth_(int(w * scale) // 2 * 2)
            cfg.setHeight_(int(h * scale) // 2 * 2)
            cfg.setMinimumFrameInterval_(CM.CMTimeMake(1, 30))
            cfg.setShowsCursor_(True)
            # 16 Oct: a take ended at 52 s of a 116 s run with no message at all, because both delegates were None
            # and ScreenCaptureKit reports a stream dying through them. Never record blind again.
            self._delegate = _StreamWatch.alloc().initWithSay_(self._say)
            self.stream = SC.SCStream.alloc().initWithFilter_configuration_delegate_(filt, cfg, self._delegate)
            rc = SC.SCRecordingOutputConfiguration.alloc().init()
            rc.setOutputURL_(NSURL.fileURLWithPath_(str(self.path)))
            self.out = SC.SCRecordingOutput.alloc().initWithConfiguration_delegate_(self._delegate, None)
            ok, e = self.stream.addRecordingOutput_error_(self.out, None)
            if not ok:
                self._say(f"error: {e}")
                return
            self.stream.startCaptureWithCompletionHandler_(
                lambda e2: self._say(f"error: {e2}" if e2 else "recording"))

        SC.SCShareableContent.getShareableContentWithCompletionHandler_(got)

    def stop(self) -> None:
        if self.stream is None:
            self._say("stopped")
            return
        self.stream.stopCaptureWithCompletionHandler_(lambda e: self._say("stopped"))
