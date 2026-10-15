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
import time

import AppKit
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
    NSFontWeightMedium,
    NSGradient,
    NSGraphicsContext,
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

GLASS = 0.45                    # how much of the frosted glass shows: 1 = Apple's default, 0 = none
W, H = 116.0, 30.0              # small on purpose: it sits over whatever you are reading (was 168 x 44)
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
        self.since = 0.0                # when the current state began, for the fade-in
        self.locked = False             # hands-free: a small dot on the left says "you can let go"
        self.liquid = False             # True on macOS 26+, where the pill sits in real Liquid Glass
        return self

    def drawRect_(self, rect):          # noqa: N802 - AppKit's name
        # The background is real glass (NSVisualEffectView behind this view), so nothing is painted here except
        # a hairline edge - without it the blur floats with no boundary and reads as a smudge.
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(rect)
        if self.liquid:                 # Liquid Glass brings its own light; only the border is added
            self._draw_border()
            self._draw_content()
            return
        # The glass sheen: light falling on the top half, fading out by the middle, the way a curved glass bead
        # catches a window. Then a rim that is brighter on top than below, so the edge reads as glass, not a line.
        shine = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(1.5, H / 2, W - 3, H / 2 - 1.5), (H - 3) / 2, (H - 3) / 2)
        NSGradient.alloc().initWithStartingColor_endingColor_(
            NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.0),
            NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.22)).drawInBezierPath_angle_(shine, 90)
        edge = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            NSMakeRect(0.5, 0.5, W - 1, H - 1), (H - 1) / 2, (H - 1) / 2)
        edge.setLineWidth_(1.0)
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.35).set()
        NSGraphicsContext.saveGraphicsState()
        NSBezierPath.clipRect_(NSMakeRect(0, H / 2, W, H / 2))     # bright rim on top
        edge.stroke()
        NSGraphicsContext.restoreGraphicsState()
        NSGraphicsContext.saveGraphicsState()
        NSBezierPath.clipRect_(NSMakeRect(0, 0, W, H / 2))         # faint rim below
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.12).set()
        edge.stroke()
        NSGraphicsContext.restoreGraphicsState()
        self._draw_border()
        self._draw_content()

    def _draw_border(self) -> None:
        """
        A two-tone rim: a dark hairline outside, a light one just inside. Clear glass over a page of the same grey
        disappeared (founder, 15 Oct); one of the two lines always contrasts, on white, black or anything between.
        """
        for inset, white, alpha in ((0.5, 0.0, 0.28), (1.5, 1.0, 0.55)):
            edge = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(inset, inset, W - 2 * inset, H - 2 * inset), H / 2 - inset, H / 2 - inset)
            edge.setLineWidth_(1.0)
            NSColor.colorWithCalibratedWhite_alpha_(white, alpha).set()
            edge.stroke()

    def _draw_content(self) -> None:
        if self.state == "listening":
            self._draw_bars()
        elif self.state == "writing":
            self._draw_writing()
        else:
            self._draw_word({
                "writing": "writing…",
                "done": "✓ typed in",
                "copied": "✓ copied",
                "nothing": "nothing heard",
                "failed": "didn't work",
                "cancelled": "cancelled",
                "secret": "password box",
            }.get(self.state, "✓ copied"))

    def _draw_bars(self) -> None:
        """Five bars, newest on the right, each eased toward the real level so a quiet moment looks quiet."""
        self.shown = [a + (b - a) * 0.35 for a, b in zip(self.shown, self.bars)]
        r, g, b = ACCENT
        n = len(self.shown)
        bw, gap = 3.0, 4.0
        total = n * bw + (n - 1) * gap
        x = (W - total) / 2
        if self.locked:
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.85, 0.2, 0.15, 0.95).set()
            NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(12, H / 2 - 3, 6, 6)).fill()
        for i, v in enumerate(self.shown):
            # the newest bar is the brightest, so the eye reads left-to-right as "then … now"
            NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, 0.55 + 0.45 * (i / (n - 1))).set()
            h = max(3.0, min(H - 10, 3 + v * (H - 12)))
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(x, (H - h) / 2, bw, h), bw / 2, bw / 2).fill()
            x += bw + gap

    def _enter(self) -> float:
        """0 -> 1 over the first 0.2 s of a state, so each new word fades in and settles instead of cutting in."""
        return min(1.0, (time.time() - self.since) / 0.2)

    def _attrs(self, alpha: float = 1.0) -> dict:
        colour = NSColor.labelColor() if self.liquid else NSColor.colorWithCalibratedWhite_alpha_(0.92, 1.0)
        return {NSFontAttributeName: NSFont.systemFontOfSize_weight_(11.5, NSFontWeightMedium),
                NSForegroundColorAttributeName: colour.colorWithAlphaComponent_(alpha)}

    def _draw_writing(self) -> None:
        """
        "writing" and three dots that light up one after another, sitting on the text's baseline. No underline or
        glint: drawn under a word with a descender it read as a glitch (founder, 15 Oct).
        """
        a = self._enter()
        attrs = self._attrs(a)
        s = NSString.stringWithString_("writing")
        size = s.sizeWithAttributes_(attrs)
        font = attrs[NSFontAttributeName]
        dot, gap = 3.2, 3.0
        x = (W - (size.width + 5 + 3 * dot + 2 * gap)) / 2
        y = (H - size.height) / 2 - (1 - a) * 3
        s.drawAtPoint_withAttributes_((x, y), attrs)
        r, g, b = ACCENT
        base = y - font.descender()                                  # the baseline, where the dots sit
        for i in range(3):
            wave = max(0.0, math.sin(self.phase - i * 1.1))          # each dot a beat behind the one before
            NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a * (0.3 + 0.7 * wave)).set()
            cx = x + size.width + 5 + i * (dot + gap)
            NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx, base + wave * 1.5, dot, dot)).fill()

    def _draw_word(self, word: str) -> None:
        """A state word. A leading tick is drawn in orange, the rest in the system text colour - no shadow, it blurred."""
        a = self._enter()
        attrs = self._attrs(a)
        tick = word.startswith("✓ ")
        rest = NSString.stringWithString_(word[2:] if tick else word)
        size = rest.sizeWithAttributes_(attrs)
        r, g, b = ACCENT
        tick_attrs = {NSFontAttributeName: NSFont.systemFontOfSize_weight_(12.0, AppKit.NSFontWeightBold),
                      NSForegroundColorAttributeName: NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)}
        t = NSString.stringWithString_("✓ ")
        tw = t.sizeWithAttributes_(tick_attrs).width if tick else 0.0
        x = (W - size.width - tw) / 2
        y = (H - size.height) / 2 - (1 - a) * 3
        if tick:
            t.drawAtPoint_withAttributes_((x, y), tick_attrs)
        rest.drawAtPoint_withAttributes_((x + tw, y), attrs)


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
        self.view = PillView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
        Liquid = getattr(AppKit, "NSGlassEffectView", None)
        if Liquid is not None:
            # macOS 26 Liquid Glass, Clear style, and then faded further (founder, twice: "more transparent").
            # The glass and the drawing are siblings, not parent and child, so fading the glass leaves the text and
            # bars at full strength - only the frosted body becomes see-through.
            holder = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
            glass = Liquid.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
            glass.setCornerRadius_(H / 2)
            glass.setStyle_(getattr(AppKit, "NSGlassEffectViewStyleClear", 1))
            glass.setAlphaValue_(GLASS)
            holder.addSubview_(glass)
            holder.addSubview_(self.view)
            self.glass = glass
            self.view.liquid = True
            self.panel.setHasShadow_(False)           # the glass brings its own depth
            glass = holder
        else:
            glass = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
            glass.setMaterial_(NSVisualEffectMaterialHUDWindow)
            glass.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            glass.setState_(NSVisualEffectStateActive)
            glass.setWantsLayer_(True)
            glass.layer().setCornerRadius_(H / 2)
            glass.layer().setMasksToBounds_(True)
            glass.addSubview_(self.view)
            self.panel.setHasShadow_(True)
        self.panel.setContentView_(glass)
        if not hasattr(self, "glass"):
            self.glass = None
        self.panel.setAlphaValue_(0.0)
        self.visible = False

    def set_glass(self, amount: float) -> None:
        """Settings → Pill transparency. Only the frosted body fades; the text and border stay solid."""
        if self.glass is not None:
            self.glass.setAlphaValue_(max(0.0, min(1.0, amount)))

    def show(self, state: str) -> None:
        if state != self.view.state:
            self.view.since = time.time()
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
        self.view.phase = (self.view.phase + 0.32) % (2 * math.pi)     # ~1 wave a second at 20 Hz
        self.view.setNeedsDisplay_(True)
