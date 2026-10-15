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
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialHUDWindow,
    NSVisualEffectStateActive,
    NSVisualEffectView,
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
        self.bars = [0.12] * 5
        self.shown = [0.12] * 5      # what is drawn: eased toward `bars`, so the bars breathe rather than flicker
        return self

    def drawRect_(self, rect):          # noqa: N802 - AppKit's name
        # The background is real glass (NSVisualEffectView behind this view), so nothing is painted here except
        # a hairline edge - without it the blur floats with no boundary and reads as a smudge.
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(rect)
        edge = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(0.5, 0.5, W - 1, H - 1), (H - 1) / 2, (H - 1) / 2)
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.16).set()
        edge.setLineWidth_(1.0)
        edge.stroke()

        if self.state == "listening":
            self._draw_bars()
        else:
            self._draw_word({
                "writing": "writing…",
                "done": "✓ typed in",
                "copied": "✓ copied",
                "nothing": "nothing heard",
                "failed": "didn't work",
            }.get(self.state, "✓ copied"))

    def _draw_bars(self) -> None:
        """Five bars, newest on the right, each eased toward the real level so a quiet moment looks quiet."""
        self.shown = [a + (b - a) * 0.35 for a, b in zip(self.shown, self.bars)]
        r, g, b = ACCENT
        n = len(self.shown)
        bw, gap = 5.0, 7.0
        total = n * bw + (n - 1) * gap
        x = (W - total) / 2
        for i, v in enumerate(self.shown):
            # the newest bar is the brightest, so the eye reads left-to-right as "then … now"
            NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 0.55 + 0.45 * (i / (n - 1))).set()
            h = max(5.0, min(H - 14, 5 + v * (H - 20)))
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(x, (H - h) / 2, bw, h), bw / 2, bw / 2).fill()
            x += bw + gap

    def _draw_word(self, word: str) -> None:
        r, g, b = ACCENT
        colour = (NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 1.0) if self.state != "writing"
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
        # Real macOS glass: it blurs what is actually behind the pill, so it sits on a bright document and a dark
        # terminal equally well. A painted panel cannot do that - it looks pasted on one of them.
        glass = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
        glass.setMaterial_(NSVisualEffectMaterialHUDWindow)
        glass.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        glass.setState_(NSVisualEffectStateActive)
        glass.setWantsLayer_(True)
        glass.layer().setCornerRadius_(H / 2)
        glass.layer().setMasksToBounds_(True)
        self.view = PillView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
        glass.addSubview_(self.view)
        self.panel.setContentView_(glass)
        self.panel.setHasShadow_(True)
        self.panel.setAlphaValue_(0.0)
        self.visible = False

    def show(self, state: str) -> None:
        self.view.state = state
        if not self.visible:
            self.panel.orderFrontRegardless()         # front, but never focused
            self.visible = True
        if self.panel.alphaValue() < 1.0:             # ~120 ms fade in, called from the 20 Hz timer
            self.panel.setAlphaValue_(min(1.0, self.panel.alphaValue() + 0.18))
        self.view.setNeedsDisplay_(True)

    def hide(self) -> None:
        if not self.visible:
            return
        a = self.panel.alphaValue() - 0.12            # ~400 ms fade out, so it leaves rather than blinks off
        if a <= 0.0:
            self.panel.setAlphaValue_(0.0)
            self.panel.orderOut_(None)
            self.visible = False
        else:
            self.panel.setAlphaValue_(a)

    def level(self, value: float) -> None:
        """Push the newest microphone level; the bars scroll left so silence looks like silence."""
        self.view.bars = self.view.bars[1:] + [max(0.0, min(1.0, value))]
        self.view.setNeedsDisplay_(True)

    def tick_writing(self) -> None:
        """A gentle pulse while the engine works, so a slow sentence does not look like a frozen app."""
        self.view.phase = (self.view.phase + 0.12) % (2 * math.pi)
        self.view.setNeedsDisplay_(True)
