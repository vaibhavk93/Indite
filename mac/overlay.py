"""
The floating pill: a small window near the bottom of the screen that shows what indite is doing while you dictate.

Three rules it must obey, and all three are easy to get wrong:
  1. It must never take focus. The whole point is to type into the app you are already in - if the pill steals
     focus, the text goes nowhere. Hence a non-activating panel.
  2. It must ignore the mouse, so it can never swallow a click meant for the window underneath.
  3. Every AppKit call has to happen on the main thread. The hotkey runs on another thread, so the app polls this
     from a timer instead of calling in directly.
"""

from __future__ import annotations

import math

import objc

from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSMakeRect,
    NSPanel,
    NSScreen,
    NSString,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)

W, H = 168.0, 44.0
ACCENT = (0.886, 0.463, 0.106)      # the indite orange, the same one the phone uses


class PillView(NSView):
    """Draws the pill: a dark rounded bar with five bars that move with your voice, or a word for the other states."""

    def initWithFrame_(self, frame):
        self = objc.super(PillView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.state = "listening"        # listening · writing · done
        self.level = 0.0                # 0..1, the microphone right now
        self.phase = 0.0                # for the writing animation
        self.bars = [0.15] * 5
        return self

    def drawRect_(self, rect):          # noqa: N802 - AppKit's name
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(rect)

        body = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(0, 0, W, H), H / 2, H / 2)
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.09, 0.08, 0.07, 0.92).set()
        body.fill()

        if self.state == "listening":
            self._draw_bars()
        else:
            self._draw_word("writing…" if self.state == "writing" else "✓ typed in")

    def _draw_bars(self) -> None:
        """Five bars, the newest on the right, so a quiet moment is visibly quiet."""
        r, g, b = ACCENT
        NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0).set()
        n = len(self.bars)
        bw, gap = 6.0, 8.0
        total = n * bw + (n - 1) * gap
        x = (W - total) / 2
        for v in self.bars:
            h = max(6.0, min(H - 16, 6 + v * (H - 22)))
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(x, (H - h) / 2, bw, h), bw / 2, bw / 2).fill()
            x += bw + gap

    def _draw_word(self, word: str) -> None:
        r, g, b = ACCENT
        colour = (NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0) if self.state == "done"
                  else NSColor.colorWithCalibratedWhite_alpha_(0.85, 1.0))
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(14.0),
            NSForegroundColorAttributeName: colour,
        }
        s = NSString.stringWithString_(word)
        size = s.sizeWithAttributes_(attrs)
        s.drawAtPoint_withAttributes_(((W - size.width) / 2, (H - size.height) / 2), attrs)


class Pill:
    """The window around the view. Created once, shown and hidden as the state changes."""

    def __init__(self) -> None:
        screen = NSScreen.mainScreen().frame()
        x = screen.origin.x + (screen.size.width - W) / 2
        y = screen.origin.y + 96                      # above the Dock, where the eye already is
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, W, H),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered, False,
        )
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setLevel_(25)                      # above normal windows, below the menu bar
        self.panel.setIgnoresMouseEvents_(True)       # never swallow a click
        self.panel.setHidesOnDeactivate_(False)
        self.panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary)
        self.view = PillView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
        self.panel.setContentView_(self.view)
        self.visible = False

    def show(self, state: str) -> None:
        self.view.state = state
        if not self.visible:
            self.panel.orderFrontRegardless()         # front, but never focused
            self.visible = True
        self.view.setNeedsDisplay_(True)

    def hide(self) -> None:
        if self.visible:
            self.panel.orderOut_(None)
            self.visible = False

    def level(self, value: float) -> None:
        """Push the newest microphone level; the bars scroll left so silence looks like silence."""
        self.view.bars = self.view.bars[1:] + [max(0.0, min(1.0, value))]
        self.view.setNeedsDisplay_(True)

    def tick_writing(self) -> None:
        """A gentle pulse while the engine works, so a slow sentence does not look like a frozen app."""
        self.view.phase = (self.view.phase + 0.12) % (2 * math.pi)
        self.view.setNeedsDisplay_(True)
