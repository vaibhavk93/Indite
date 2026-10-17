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
    NSObject,
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

# macOS 13+: may also appear inside another app's full-screen Space. Without it the pill vanished over a full-screen
# Terminal and came back on any other window (founder, 15 Oct).
JOIN_ALL_APPS = getattr(AppKit, "NSWindowCollectionBehaviorCanJoinAllApplications", 0)
CLEAR = 60                      # pill transparency in %, 0-100 in steps of 10 (Settings → Look & sounds)
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
        self.since = 0.0
        self.fill = 0.34                # tint behind the text, from Settings → Pill transparency
        self.label = ""                 # free text for the meeting state                # when the current state began, for the fade-in
        self.locked = False             # hands-free: a small dot on the left says "you can let go"
        self.liquid = False             # True on macOS 26+, where the pill sits in real Liquid Glass
        return self

    def drawRect_(self, rect):          # noqa: N802 - AppKit's name
        # The background is real glass (NSVisualEffectView behind this view), so nothing is painted here except
        # a hairline edge - without it the blur floats with no boundary and reads as a smudge.
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(rect)
        if self.liquid:                 # Liquid Glass brings its own light; only the tint and the border are added
            if self.fill > 0:
                NSColor.windowBackgroundColor().colorWithAlphaComponent_(self.fill).set()
                NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                    NSMakeRect(0.5, 0.5, W - 1, H - 1), (H - 1) / 2, (H - 1) / 2).fill()
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
        elif self.state == "meeting":                             # a red dot that breathes, and the time so far
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.86, 0.2, 0.15, 0.55 + 0.45 * abs(math.sin(self.phase))).set()
            NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(16, H / 2 - 3.5, 7, 7)).fill()
            self._draw_word(self.label)
        else:
            self._draw_word({
                "writing": "writing…",
                "done": "✓ typed in",
                "copied": "✓ copied",
                "nothing": "nothing heard",
                "failed": "didn’t work",
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


def bottom_centre(width: float, lift: float) -> tuple[float, float]:
    """Where a panel goes: centred at the bottom of the screen the pointer is on (two monitors: not always the main
    one, which was fixed once at start-up - UI review P3), `lift` points above the bottom edge."""
    from AppKit import NSEvent, NSMouseInRect
    at = NSEvent.mouseLocation()
    screen = next((sc.frame() for sc in NSScreen.screens() if NSMouseInRect(at, sc.frame(), False)),
                  NSScreen.mainScreen().frame())
    return screen.origin.x + (screen.size.width - width) / 2, screen.origin.y + lift


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
        self.panel.setCanHide_(False)                 # "Hide indite" (⌘H) must not take the pill with it
        self.panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | JOIN_ALL_APPS)
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
            # The glass itself always stays at full strength: fading it (the old way) froze its view of what is
            # behind, so the background stuck while you scrolled (founder, 15 Oct). Transparency is a tint drawn
            # under the text instead - see PillView.fill.
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

    def snapshot(self, request, name: str) -> None:
        """A picture of the pill as it is on screen, glass and all (developer check)."""
        import Quartz
        request.unlink(missing_ok=True)

        def shoot():
            f = self.panel.frame()                        # the screen around the pill, so what is behind it shows
            top = NSScreen.screens()[0].frame().size.height
            rect = Quartz.CGRectMake(f.origin.x - 40, top - f.origin.y - f.size.height - 20, f.size.width + 80,
                                     f.size.height + 40)
            img = Quartz.CGWindowListCreateImage(rect, Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID,
                                                 Quartz.kCGWindowImageDefault)
            if img is not None:
                rep = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(img)
                rep.representationUsingType_properties_(AppKit.NSPNGFileType, None).writeToFile_atomically_(
                    str(request.parent / name), True)
        from PyObjCTools import AppHelper
        AppHelper.callLater(1.0, shoot)

    def set_clear(self, percent: int) -> None:
        """Settings → Pill transparency, 0-100 %. 100 = Apple's clear glass alone; lower adds a tint behind the text."""
        self.view.fill = (100 - max(0, min(100, int(percent)))) / 100 * 0.85
        self.view.setNeedsDisplay_(True)

    def show(self, state: str) -> None:
        changed, was = state != self.view.state, self.view.state
        if changed:
            self.view.since = time.time()
        self.view.state = state
        # Ask the window, not our own flag: hiding or minimising indite takes the panel off screen behind our back,
        # and the flag then said "showing" forever - the pill never came back (founder, 15 Oct)
        if not self.visible or not self.panel.isVisible():
            self.panel.setFrameOrigin_(bottom_centre(W, 96))   # on the screen you are working on
            self.panel.orderFrontRegardless()         # front, but never focused
            self.visible = True
        # Full strength at once, not a fade. The fade added 0.18 an frame and assumed 20 frames a second, which is
        # true only while indite is the app in front. In real use - the founder in Chrome, holding the key - macOS
        # throttles a background app's timers, and the log showed the pill still at alpha 0.40 after a SIX SECOND
        # dictation: on screen, and all but invisible. That is every "the pill is not there" report (16 Oct).
        if self.panel.alphaValue() < 1.0:
            self.panel.setAlphaValue_(1.0)
        self.view.setNeedsDisplay_(True)
        if changed:
            # Reported after the window work, not before: measured first, every line said alpha 0 and not on screen,
            # which is simply what is true a microsecond before it is ordered front. The founder has said "the pill
            # is not there" four times and a forced snapshot cannot answer it - this can.
            f = self.panel.frame()
            print(f"pill: {was or 'hidden'} -> {state} | on screen={bool(self.panel.isVisible())} "
                  f"alpha={self.panel.alphaValue():.2f} at ({f.origin.x:.0f},{f.origin.y:.0f}) "
                  f"{f.size.width:.0f}x{f.size.height:.0f} level={self.panel.level()}", flush=True)

    def hide(self) -> None:                               # logged only when it was actually up, to keep the log quiet
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


class CardTarget(NSObject):
    """Receives the card's button clicks (an Objective-C target has to be an NSObject) and hands them to Python."""

    def click_(self, sender):                                    # noqa: N802
        self.handler(sender.tag())


class Preview:
    """
    The words just written, in a small glass card above the pill, for a few seconds (Settings → Show the words).
    Off by default: the words are already where you typed them. On, it lets you check a dictation without looking
    away - and it is the only place to see one that went to the clipboard. Click-through and never focused, like
    the pill. Called from any thread; all AppKit work is handed to the main thread.
    """

    PW, PH = 460.0, 66.0              # width fixed; the height grows with the text (founder: one line + "…" hid it)
    MAX_H = 320.0                     # about 14 lines; text longer than this keeps its END and loses its start
    CAP = 6.0                         # never on screen longer than this, however long the text (founder, 16 Oct)
    ACTIONS = ("Ask AI", "", "", "To do")   # Ask AI fixed; the app names 2 and 3 (set_titles); on_action(index)
    BH = 34.0                         # the strip the buttons sit in

    def __init__(self) -> None:
        screen = NSScreen.mainScreen().frame()
        x = screen.origin.x + (screen.size.width - self.PW) / 2
        y = screen.origin.y + 96 + H + 10                 # just above the pill
        self.panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, self.PW, self.PH),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel, NSBackingStoreBuffered, False)
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setLevel_(25)
        self.panel.setIgnoresMouseEvents_(True)
        self.panel.setCanHide_(False)
        self.panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | JOIN_ALL_APPS)
        box = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, self.PW, self.PH))
        Liquid = getattr(AppKit, "NSGlassEffectView", None)
        if Liquid is not None:
            glass = Liquid.alloc().initWithFrame_(NSMakeRect(0, 0, self.PW, self.PH))
            glass.setCornerRadius_(14.0)
        else:
            glass = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, self.PW, self.PH))
            glass.setMaterial_(NSVisualEffectMaterialHUDWindow)
            glass.setState_(NSVisualEffectStateActive)
            glass.setWantsLayer_(True)
            glass.layer().setCornerRadius_(14.0)
            glass.layer().setMasksToBounds_(True)
        box.addSubview_(glass)
        self.glass, self.box, self.base_y = glass, box, y
        self.label = AppKit.NSTextField.wrappingLabelWithString_("")
        self.label.setFrame_(NSMakeRect(16, 10, self.PW - 32, self.PH - 20))
        self.label.setFont_(NSFont.systemFontOfSize_(13.0))
        self.label.setTextColor_(NSColor.labelColor())
        self.label.setMaximumNumberOfLines_(0)                    # every line, wrapped at words
        self.label.setLineBreakMode_(AppKit.NSLineBreakByWordWrapping)
        self.label.setPreferredMaxLayoutWidth_(self.PW - 32)
        box.addSubview_(self.label)
        box.setWantsLayer_(True)
        box.layer().setCornerRadius_(14.0)
        box.layer().setBorderWidth_(1.0)
        box.layer().setBorderColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.18).CGColor())
        self.panel.setContentView_(box)
        self.shown_at = 0.0
        self.on_action = None         # set by the app: on_action(index); None = no buttons at all
        self.with_buttons = False
        self.busy = False             # an AI answer is on its way: the card stays until it lands
        self.armed_from = None        # pointer position when the card appeared; clicks wait until it moves
        self.target = CardTarget.alloc().init()
        self.asking = None            # ask(): a one-off question ("Record this call?") owns the buttons until answered
        self.titles = list(self.ACTIONS)
        self.target.handler = lambda i: self.asking(i) if self.asking else (self.on_action and self.on_action(i))
        self.buttons = []
        x = 16.0
        for i, title in enumerate(self.ACTIONS):
            b = AppKit.NSButton.buttonWithTitle_target_action_(title, self.target, "click:")
            b.setBezelStyle_(AppKit.NSBezelStyleRounded)
            b.setControlSize_(AppKit.NSControlSizeSmall)
            b.setFont_(NSFont.systemFontOfSize_(11.0))
            b.setTag_(i)
            b.sizeToFit()
            b.setFrameOrigin_((x, 6))
            x += b.frame().size.width + 6
            b.setHidden_(True)
            box.addSubview_(b)
            self.buttons.append(b)

    def set_titles(self, titles: list[str]) -> None:
        """Names the 2nd and 3rd buttons and lays the row out again (main thread, at start-up)."""
        self.titles = [self.ACTIONS[0], *titles, self.ACTIONS[3]]
        self._lay(self.titles)

    def _lay(self, titles: list[str]) -> None:
        x = 16.0
        for b, title in zip(self.buttons, titles):
            b.setTitle_(title)
            b.sizeToFit()
            b.setFrameOrigin_((x, 6))
            x += b.frame().size.width + 6

    def show(self, text: str, buttons: bool | str = False) -> None:
        """buttons: True = the AI actions and To do; "todo" = To do only (AI off); False = none (not a saved note)."""
        from PyObjCTools import AppHelper
        AppHelper.callAfter(self._show, text, buttons)

    def ask(self, text: str, choices: list[str], on_choice) -> None:
        """A question with its own buttons (at most 4), e.g. "Record this call?" [Record] [Not now]."""
        from PyObjCTools import AppHelper

        def go():
            self.asking = lambda i: (setattr(self, "asking", None), self._lay(self.titles), self.hide_now(), on_choice(i))
            self._lay(choices + self.titles[len(choices):])
            self._show(text, len(choices))
        AppHelper.callAfter(go)

    def working(self, text: str) -> None:
        """An AI answer is on its way: say so, drop the buttons, and stay up until answer() or failed()."""
        from PyObjCTools import AppHelper
        self.busy = True
        AppHelper.callAfter(self._show, text, False)

    def answer(self, text: str) -> None:
        """The answer has landed (and is on the clipboard): show it, then leave on the normal clock."""
        from PyObjCTools import AppHelper
        self.busy = False
        AppHelper.callAfter(self._show, text, False, True)

    def failed(self, text: str) -> None:
        """The answer did not come: say why, and put the buttons back so the same one is the retry."""
        from PyObjCTools import AppHelper
        self.busy = False
        AppHelper.callAfter(self._show, text, True, True)

    def _show(self, text: str, buttons: bool | str = False, head: bool = False) -> None:
        """head: when too long, keep the start (an answer: its "copied" line), not the end (a dictation: newest)."""
        asked = buttons if isinstance(buttons, int) and not isinstance(buttons, bool) else 0   # ask(): how many
        if self.asking and not asked:                             # anything else replaces an unanswered question
            self.asking = None
            self._lay(self.titles)
        self.with_buttons = bool(asked or (buttons and self.on_action))
        for i, b in enumerate(self.buttons):
            b.setHidden_(not self.with_buttons or (buttons == "todo" and i != 3) or (asked and i >= asked))
        extra = self.BH if self.with_buttons else 0.0
        self.label.setStringValue_(text)
        tw = self.PW - 32
        self.label.setPreferredMaxLayoutWidth_(tw)
        need = self.label.cell().cellSizeForBounds_(NSMakeRect(0, 0, tw, 10_000)).height
        h = min(self.MAX_H, max(self.PH, need + 22)) + extra
        if need + 22 > self.MAX_H and head:                      # a long answer: wrap, keep its start, cut the end
            self.label.setLineBreakMode_(AppKit.NSLineBreakByWordWrapping)
            self.label.cell().setTruncatesLastVisibleLine_(True)
            self.label.setMaximumNumberOfLines_(int((self.MAX_H - 22) // 17))
        elif need + 22 > self.MAX_H:                             # a long dictation: keep the end, which is newest
            self.label.setLineBreakMode_(AppKit.NSLineBreakByTruncatingHead)
            self.label.setMaximumNumberOfLines_(int((self.MAX_H - 22) // 17))
        else:
            self.label.setLineBreakMode_(AppKit.NSLineBreakByWordWrapping)
            self.label.setMaximumNumberOfLines_(0)
        f = self.panel.frame()
        if not self.panel.isVisible() or self.panel.alphaValue() <= 0.0:   # appearing: on the screen you are on
            x, self.base_y = bottom_centre(self.PW, 96 + H + 10)
            f.origin.x = x
        self.panel.setFrame_display_(NSMakeRect(f.origin.x, self.base_y, self.PW, h), True)   # grows upward
        for v in (self.box, self.glass):
            v.setFrame_(NSMakeRect(0, 0, self.PW, h))
        self.label.setFrame_(NSMakeRect(16, 11 + extra, tw, h - 22 - extra))
        self.panel.setAlphaValue_(1.0)
        self.panel.setIgnoresMouseEvents_(True)
        self.panel.orderFrontRegardless()
        self.shown_at = t = time.time()
        from PyObjCTools import AppHelper
        if self.with_buttons:
            import AppKit as AK
            self.armed_from = AK.NSEvent.mouseLocation()     # where the pointer was when the card appeared
            self._track(t)
        # Long enough to read: 4 s plus about a quarter second a word - but never more than CAP, because a card that
        # sits over your work is worse than one that leaves too early (founder, 16 Oct). If you want longer, keep the
        # pointer on it: _maybe_hide puts the timer back for as long as the mouse is inside the card.
        AppHelper.callLater(min(self.CAP, 4.0 + 0.25 * len(text.split())), self._maybe_hide, t)

    def hovered(self) -> bool:
        """
        Is the pointer on the card right now?

        Asked, not listened for: the panel deliberately ignores mouse events (overlay rule 2 - never swallow a click
        meant for the window underneath), so a tracking area would mean taking clicks back. Reading the pointer's
        position costs nothing and breaks nothing.
        """
        if self.panel.alphaValue() <= 0.0:
            return False
        import AppKit as AK
        return AK.NSMouseInRect(AK.NSEvent.mouseLocation(), self.panel.frame(), False)

    def _track(self, t: float) -> None:
        """
        The card takes clicks only while the pointer rests on it. Everywhere else it stays click-through, so a click
        meant for the app underneath is never swallowed (overlay rule 2) - the buttons work because you are on them.
        """
        if t != self.shown_at:
            return
        import AppKit as AK
        here = AK.NSEvent.mouseLocation()
        if self.armed_from and (abs(here.x - self.armed_from.x) > 3 or abs(here.y - self.armed_from.y) > 3):
            self.armed_from = None                          # it moved: from now on, being on the card means you came to it
        self.panel.setIgnoresMouseEvents_(self.armed_from is not None or not self.hovered())
        from PyObjCTools import AppHelper
        AppHelper.callLater(0.1, self._track, t)

    def _maybe_hide(self, t: float) -> None:
        """Hide, unless the pointer is on the card or an answer is on its way - then ask again shortly."""
        if self.hovered() or self.busy:
            from PyObjCTools import AppHelper
            AppHelper.callLater(0.3, self._maybe_hide, t)
            return
        self._hide(t)

    def hide_now(self) -> None:
        """Take it away at once - used when the next dictation starts, so an old card never sits over a new one."""
        from PyObjCTools import AppHelper
        AppHelper.callAfter(self._hide, self.shown_at)

    def snapshot(self, request) -> None:
        """Shows the card with the request's text and saves a picture of it beside the request (developer check)."""
        import Quartz
        text = request.read_text()[len("preview:"):].strip()
        request.unlink(missing_ok=True)
        self._show(text.lstrip("+"), buttons=text.startswith("+"))     # "preview:+…" shows the AI buttons too

        def shoot():
            img = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow,
                                                 self.panel.windowNumber(), Quartz.kCGWindowImageBoundsIgnoreFraming)
            if img is not None:
                rep = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(img)
                rep.representationUsingType_properties_(AppKit.NSPNGFileType, None).writeToFile_atomically_(
                    str(request.parent / "snapshot-preview.png"), True)
        from PyObjCTools import AppHelper
        AppHelper.callLater(0.6, shoot)

    def _hide(self, t: float) -> None:
        if t == self.shown_at:                            # a newer dictation restarts the clock
            self.panel.setIgnoresMouseEvents_(True)
            self.panel.orderOut_(None)
