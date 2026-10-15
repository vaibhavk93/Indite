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


class Activation(NSObject):
    """
    Calls the app back when macOS activates it (an NSObject, because notifications need a selector). Lives here, not
    in indite_mac.py: that file is both the program and a module this one imports, so a class there is defined twice
    and Objective-C refuses the second ("overriding existing Objective-C class").
    """

    def initWithApp_(self, app):
        self = objc.super(Activation, self).init()
        if self is None:
            return None
        self.app = app
        return self

    def resigned_(self, _note):                          # noqa: N802
        """Another app is in front: back to menu-bar-only, so the pill may enter that app's full screen."""
        w = self.app.window
        if w is None or not (w.win.styleMask() & (1 << 14)):      # unless indite itself is full screen
            NSApp.setActivationPolicy_(1)

    def quitIndite_(self, _sender):                      # noqa: N802
        self.app.quit_all(None)

    def fire_(self, _note):                              # noqa: N802
        w = self.app.window
        if w is None or not w.win.isVisible():
            self.app.open_window(None)


def main_menu(app) -> None:
    """
    The menus a Mac app is expected to have. indite had none, so in full screen the top bar was empty (no Close or
    Minimize), and ⌘C / ⌘V / ⌘A did nothing in the window's text boxes - a web view takes those from the Edit menu.
    """
    from AppKit import NSMenu, NSMenuItem
    bar = NSMenu.alloc().init()

    def menu(title: str, items: list) -> None:
        m = NSMenu.alloc().initWithTitle_(title)
        for it in items:
            if it is None:
                m.addItem_(NSMenuItem.separatorItem())
                continue
            label, action, key, *mods = it
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(label, action, key)
            if mods:
                item.setKeyEquivalentModifierMask_(mods[0])
            m.addItem_(item)
        top = NSMenuItem.alloc().init()
        top.setSubmenu_(m)
        bar.addItem_(top)

    menu("indite", [("About indite", "orderFrontStandardAboutPanel:", ""), None,
                    ("Hide indite", "hide:", "h"), None, ("Quit indite", "quitIndite:", "q")])
    quit_item = bar.itemAtIndex_(0).submenu().itemWithTitle_("Quit indite")
    quit_item.setTarget_(app._activation)               # through indite's own quit, so the engine stops too
    menu("Edit", [("Undo", "undo:", "z"), ("Redo", "redo:", "Z"), None, ("Cut", "cut:", "x"),
                  ("Copy", "copy:", "c"), ("Paste", "paste:", "v"), ("Select All", "selectAll:", "a")])
    menu("Window", [("Minimize", "performMiniaturize:", "m"), ("Zoom", "performZoom:", ""),
                    ("Enter Full Screen", "toggleFullScreen:", "f", 1 << 18 | 1 << 20), None,
                    ("Close", "performClose:", "w")])
    NSApp.setMainMenu_(bar)


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
            "fixes_list": [list(f) for f in sorted(store.my_fixes(), key=lambda f: f[0].lower())],
            "ai_providers": __import__("ai").PROVIDERS,
            "ai_models": __import__("ai").DEFAULT_MODEL,
            "ai_status": self.app.ai_who,
            "ai_keys": self.app.ai_keys,
            "mics": __import__("indite_mac").mic_names(),
            "using": self.app.mic.using,
            "job": self.app.job,
            "meeting": {"running": self.app.meeting.running, "started": self.app.meeting.started,
                        "problem": self.app.meeting.problem, "note": self.app.meeting.note},
            "mic_ok": __import__("indite_mac").mic_allowed(),
            "ai_busy": self.app.ai_busy,
            "notice": self.app.notice,
            "ai_error": self.app.ai_error,
            "ai_actions": {k: v[:3] for k, v in __import__("ai").ACTIONS.items()},
            "ai_styles": __import__("ai").STYLES,
            "ai_langs": __import__("ai").LANGUAGES,
            "file_error": self.app.file_error,
        }

    @objc.python_method
    def js(self, code: str) -> None:
        if self.web is not None:
            self.web.evaluateJavaScript_completionHandler_(code, None)

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
            self.app.check_ai()
        elif act == "pref":
            store.set_pref(msg.get("key", ""), msg.get("value"))
            self.app.reload_prefs()
            if msg.get("key") == "theme" and self.app.window:
                self.app.window.theme()
        elif act == "copy":
            self.app.typer.copy(msg.get("text", ""))
        elif act == "note":                              # star / to-do / title: only these fields may change
            fields = {k: v for k, v in (msg.get("set") or {}).items() if k in ("star", "todo", "title")}
            store.update(str(msg.get("id", "")), **fields)
        elif act == "delete":
            self.undo = store.delete(str(msg.get("id", "")))
        elif act == "undo":
            if getattr(self, "undo", None):
                store.restore(self.undo)
                self.undo = None
        elif act == "export":
            self.app.export(str(msg.get("id", "")), str(msg.get("fmt", "txt")))
        elif act == "dismiss":
            self.app.file_error = ""
            self.app.ai_error = ""
        elif act == "mic_ask":
            from indite_mac import ask_mic, mic_allowed
            if mic_allowed() is False:                   # refused before: only System Settings can change it
                import subprocess
                subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"])
            else:
                ask_mic()
        elif act == "ax_open":
            import subprocess
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
        elif act == "status":
            pass                                         # the page polls while setup is open; push() below answers
        elif act == "fix_del":
            store.remove_fix(str(msg.get("heard", "")))
        elif act == "todo_add":
            t = " ".join(str(msg.get("text", "")).split())
            if t:
                store.add(t, 0, 0, "task", "", kind="task", todo="open")
        elif act == "ai_key":
            import ai
            ai.key_set(str(msg.get("provider", "")), str(msg.get("key", "")).strip())
            self.app.check_ai()
        elif act == "ai_login":
            import ai
            ai.claude_login()
            self.app.check_ai(later=True)
        elif act == "who":
            self.app.who_spoke(str(msg.get("id", "")), int(msg.get("k", 0) or 0))
        elif act == "meeting":
            self.app.toggle_meeting()
        elif act == "rename":                            # a speaker's name in one note: {"Others": "Rohit"}
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            old, new = str(msg.get("who", "")), " ".join(str(msg.get("name", "")).split())[:40]
            if row and old and new:
                names = dict(row.get("names") or {})
                names[old] = new
                store.update(row["id"], names=names)
        elif act == "backup":
            self.app.backup()
        elif act == "restore":
            self.app.restore()
        elif act == "notice_seen":
            self.app.notice = ""
        elif act == "ai":
            self.app.ask_ai(str(msg.get("id", "")), str(msg.get("act", "")), str(msg.get("extra", "")))
        elif act == "tasks":
            self.app.add_tasks(str(msg.get("id", "")), str(msg.get("label", "")))
        elif act == "ai_clear":                           # remove one AI answer, or the improved version
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            if row and msg.get("label") == "improved":
                store.update(row["id"], improved=None)
            elif row:
                store.update(row["id"], ai=[a for a in row.get("ai", []) if a["label"] != msg.get("label")] or None)
        elif act == "add_fix":
            store.add_fix(msg.get("heard", ""), msg.get("want", ""))
        elif act == "files":
            self.app.open_files(None)
        elif act == "fixes":
            self.app.edit_fixes(None)
        elif act == "clear":
            from AppKit import NSAlert, NSAlertFirstButtonReturn
            n = sum(1 for r in store.history() if not store.keep(r))
            alert = NSAlert.alloc().init()
            alert.setMessageText_(f"Delete {n} dictation{'s' if n != 1 else ''}?")
            alert.setInformativeText_("Starred notes, to-dos and transcribed files are kept. "
                                      "The rest is removed from this Mac and cannot be undone.")
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


class PageEvents(NSObject):
    """
    Watches the page inside the window. A web view whose content process dies shows an empty window and never says
    why (founder, 15 Oct: "UI bekaar hai" - the window was blank, still at about:blank). Log it, and load it again.
    """

    def initWithWindow_(self, owner):
        self = objc.super(PageEvents, self).init()
        if self is None:
            return None
        self.owner = owner
        return self

    def webView_didFinishNavigation_(self, web, _nav):                          # noqa: N802
        print("window page loaded:", str(web.URL())[-40:])

    def webView_didFailProvisionalNavigation_withError_(self, web, _nav, err):  # noqa: N802
        print("window page failed to load:", err)
        self.owner.load()

    def webView_didFailNavigation_withError_(self, web, _nav, err):             # noqa: N802
        print("window page failed:", err)

    def webViewWebContentProcessDidTerminate_(self, web):                       # noqa: N802
        print("window page crashed - loading it again")
        self.owner.load()


class WindowEvents(NSObject):
    """
    Full screen, done properly. A menu-bar-only app ("accessory") cannot own a full-screen Space: macOS zoomed the
    window over whatever app was in front and left the menu bar and Dock gaps (founder, 15 Oct). So while the window
    is open indite becomes a normal app with a Dock icon, and goes back to living in the menu bar when it closes.
    """

    def initWithBridge_(self, bridge):
        self = objc.super(WindowEvents, self).init()
        if self is None:
            return None
        self.bridge = bridge
        return self

    def windowWillClose_(self, _note):              # noqa: N802
        NSApp.setActivationPolicy_(1)                 # accessory: menu bar only, no Dock icon

    def windowDidBecomeKey_(self, _note):           # noqa: N802
        NSApp.setActivationPolicy_(0)                 # in front: a normal app, so the green button gives a Space

    # (Going back to menu-bar-only when another app comes to the front is in Activation.resigned_. Doing it here, on
    # "window lost focus", fired in the middle of leaving full screen and left the window with grey, dead buttons.)

    def windowDidEnterFullScreen_(self, _note):     # noqa: N802
        self.bridge.js("document.body.classList.add('fs')")    # no traffic lights to clear: drop the top gap

    def windowDidExitFullScreen_(self, _note):      # noqa: N802
        self.bridge.js("document.body.classList.remove('fs')")


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
        self.win.setCollectionBehavior_(1 << 7)             # FullScreenPrimary: the green button gives it its own Space
        self.events = WindowEvents.alloc().initWithBridge_(self.bridge)
        self.win.setDelegate_(self.events)

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
        self.page_events = PageEvents.alloc().initWithWindow_(self)
        self.web.setNavigationDelegate_(self.page_events)
        self.load()
        self.bridge.web = self.web

        glass.addSubview_(self.web)
        strip = DragStrip.alloc().initWithFrame_(NSMakeRect(0, H - 38, W, 38))
        strip.setAutoresizingMask_(2 | 8)                   # width sizable | stays pinned to the top
        glass.addSubview_(strip)
        self.win.setContentView_(glass)
        self.win.setBackgroundColor_(NSColor.clearColor())
        self.theme()
        main_menu(app)

    def load(self) -> None:
        self.web.loadFileURL_allowingReadAccessToURL_(
            NSURL.fileURLWithPath_(str(PAGE)), NSURL.fileURLWithPath_(str(PAGE.parent)))

    def snapshot(self, request) -> None:
        """
        Saves a picture of this window (only this window) next to the request file, after showing the tab named in
        it. For checking the real UI, which a browser preview cannot show (glass, fonts, the Mac's own controls).
        Needs Screen & System Audio Recording permission; does nothing without it.
        """
        import Quartz
        tab = request.read_text().strip() or "home"
        request.unlink(missing_ok=True)
        self.show()
        wait = 0.8
        if tab == "cmd:fs":                                 # switch full screen, then picture it
            self.win.toggleFullScreen_(None)
            wait = 2.5
        if not tab.startswith("cmd:"):
            self.bridge.js(f"go({tab!r}.split(':')[0]); " + (f"sgo({tab.split(':')[1]!r})" if ":" in tab else ""))
        self.web.evaluateJavaScript_completionHandler_(
            "JSON.stringify({ready: document.readyState, text: document.body ? document.body.innerText.length : -1, "
            "err: window.__err || '', size: [innerWidth, innerHeight], url: location.href.slice(-30)})",
            lambda result, error: print("snapshot page state:", result, error))

        def shoot():
            img = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow,
                                                 self.win.windowNumber(), Quartz.kCGWindowImageBoundsIgnoreFraming)
            if img is None:
                return
            from AppKit import NSBitmapImageRep, NSPNGFileType
            rep = NSBitmapImageRep.alloc().initWithCGImage_(img)
            out = request.parent / f"snapshot-{tab.replace(':', '-')}.png"
            rep.representationUsingType_properties_(NSPNGFileType, None).writeToFile_atomically_(str(out), True)
        from PyObjCTools import AppHelper
        AppHelper.callLater(wait, shoot)

    def theme(self) -> None:
        """The sidebar glass follows the same choice as the page, or the two halves disagree."""
        from AppKit import NSAppearance
        name = {"light": "NSAppearanceNameAqua", "dark": "NSAppearanceNameDarkAqua"}.get(store.prefs()["theme"])
        self.win.setAppearance_(NSAppearance.appearanceNamed_(name) if name else None)

    def show(self) -> None:
        if str(self.web.URL() or "").startswith("about:") or self.web.URL() is None:
            self.load()                                     # never show an empty window
        NSApp.setActivationPolicy_(0)                       # a normal app while the window is open (see WindowEvents)
        NSApp.activateIgnoringOtherApps_(True)              # a menu-bar app has to ask for focus
        self.win.makeKeyAndOrderFront_(None)
        self.bridge.push()                                  # fresh history every time it opens
