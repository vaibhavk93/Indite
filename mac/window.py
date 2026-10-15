"""
The indite window: the part of the Mac app you can look at.

It is a WKWebView in a glass window. The reason is laziness with a straight face - a history list, a search box,
four settings and a stats strip is a few hundred lines of NSTableView plumbing in AppKit and about forty lines of
HTML, and the project already cares a lot about how things look. The web view draws no background of its own, so
the real macOS blur behind it shows through, the same material the pill uses.

The web page can only do four things: read the state, change a setting, copy a line, and empty the history. There
is no network in the page and no file access - everything goes through `Bridge` below.
"""

from __future__ import annotations

import json
from pathlib import Path

import objc
from AppKit import (
    NSApp,
    NSBackingStoreBuffered,
    NSColor,
    NSMakeRect,
    NSView,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialUnderWindowBackground,
    NSVisualEffectStateActive,
    NSVisualEffectView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskFullSizeContentView,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject, NSURL
from WebKit import WKUserContentController, WKWebView, WKWebViewConfiguration

import store

PAGE = Path(__file__).resolve().parent / "ui/app.html"
W, H = 920.0, 660.0


def front_app() -> str:
    """Which app the words went into, so the history reads like a memory instead of a log."""
    try:
        from AppKit import NSWorkspace
        a = NSWorkspace.sharedWorkspace().frontmostApplication()
        return str(a.localizedName()) if a else ""
    except Exception:       # noqa: BLE001
        return ""


class Bridge(NSObject):
    """Everything the page is allowed to ask for. Anything not listed here is ignored."""

    def initWithApp_(self, app):
        self = objc.super(Bridge, self).init()
        if self is None:
            return None
        self.app = app
        self.web = None
        return self

    def state(self) -> dict:
        from indite_mac import can_listen, HOTKEYS
        return {
            "prefs": store.prefs(),
            "history": store.history(),
            "listening": bool(can_listen()),
            "hotkeys": HOTKEYS,
            "engine": self.app.engine_kind,
            "fixes": len(store.my_fixes()),
            "mics": __import__("indite_mac").mic_names(),
            "using": self.app.mic.using,
        }

    def push(self) -> None:
        if self.web is None:
            return
        js = "window.push(%s)" % json.dumps(json.dumps(self.state()))
        self.web.evaluateJavaScript_completionHandler_(js, None)

    def userContentController_didReceiveScriptMessage_(self, _controller, message):
        try:
            msg = json.loads(str(message.body()))
        except Exception:   # noqa: BLE001
            return
        act = msg.get("action")
        if act == "ready":
            pass
        elif act == "pref":
            store.set_pref(msg.get("key", ""), msg.get("value"))
            self.app.reload_prefs()
        elif act == "copy":
            self.app.typer.copy(msg.get("text", ""))
        elif act == "add_fix":
            store.add_fix(msg.get("heard", ""), msg.get("want", ""))
        elif act == "files":
            self.app.open_files(None)
        elif act == "fixes":
            self.app.edit_fixes(None)
        elif act == "clear":
            from AppKit import NSAlert, NSAlertFirstButtonReturn
            n = len(store.history())
            alert = NSAlert.alloc().init()
            alert.setMessageText_(f"Delete all {n} saved dictation{'s' if n != 1 else ''}?")
            alert.setInformativeText_("They are removed from this Mac. This cannot be undone.")
            alert.addButtonWithTitle_("Delete")
            alert.addButtonWithTitle_("Cancel")
            alert.buttons()[0].setHasDestructiveAction_(True)
            if alert.runModal() == NSAlertFirstButtonReturn:
                store.clear()
        elif act == "permission":
            from indite_mac import ask_to_listen
            ask_to_listen()
        elif act == "quit":
            self.app.quit_all(None)
            return
        self.push()


class DragStrip(NSView):
    """
    The top of the window, where a title bar would be. The page covers the whole window (the title bar is
    transparent), and a web view never lets the window be dragged - so this invisible strip sits above it and moves
    the window, and a double-click zooms it, like any Mac title bar.
    """

    def mouseDown_(self, event):        # noqa: N802 - AppKit's name
        if event.clickCount() == 2:
            self.window().performZoom_(None)
        else:
            self.window().performWindowDragWithEvent_(event)


class Window:
    """Made once, on the main thread, the first time the user opens it."""

    def __init__(self, app) -> None:
        self.bridge = Bridge.alloc().initWithApp_(app)
        self.win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, W, H),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskResizable | NSWindowStyleMaskFullSizeContentView,
            NSBackingStoreBuffered, False,
        )
        self.win.setTitle_("indite")
        self.win.setTitlebarAppearsTransparent_(True)       # the page draws its own header, under the traffic lights
        self.win.setMinSize_((700.0, 480.0))
        self.win.center()
        self.win.setReleasedWhenClosed_(False)              # closing hides it; the app lives in the menu bar

        glass = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, W, H))
        glass.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
        glass.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        glass.setState_(NSVisualEffectStateActive)
        glass.setAutoresizingMask_(18)                      # width | height

        content = WKUserContentController.alloc().init()
        content.addScriptMessageHandler_name_(self.bridge, "indite")
        cfg = WKWebViewConfiguration.alloc().init()
        cfg.setUserContentController_(content)
        self.web = WKWebView.alloc().initWithFrame_configuration_(NSMakeRect(0, 0, W, H), cfg)
        self.web.setValue_forKey_(False, "drawsBackground")  # so the glass behind actually shows
        self.web.setAutoresizingMask_(18)
        self.web.loadFileURL_allowingReadAccessToURL_(
            NSURL.fileURLWithPath_(str(PAGE)), NSURL.fileURLWithPath_(str(PAGE.parent)))
        self.bridge.web = self.web

        glass.addSubview_(self.web)
        strip = DragStrip.alloc().initWithFrame_(NSMakeRect(0, H - 38, W, 38))
        strip.setAutoresizingMask_(2 | 8)                   # width sizable | stays pinned to the top
        glass.addSubview_(strip)
        self.win.setContentView_(glass)
        self.win.setBackgroundColor_(NSColor.clearColor())

    def show(self) -> None:
        NSApp.activateIgnoringOtherApps_(True)              # a menu-bar app has to ask for focus
        self.win.makeKeyAndOrderFront_(None)
        self.bridge.push()                                  # fresh history every time it opens
