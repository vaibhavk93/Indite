"""
The Inditeflow window: the part of the Mac app you can look at.

It is a WKWebView in a glass window. The reason is laziness with a straight face - a history list, a search box,
four settings and a stats strip is a few hundred lines of NSTableView plumbing in AppKit and about forty lines of
HTML, and the project already cares a lot about how things look. The web view draws no background of its own, so
the real macOS blur behind it shows through, the same material the pill uses.

The web page can only do four things: read the state, change a setting, copy a line, and empty the history. There
is no network in the page and no file access - everything goes through `Bridge` below.
"""

from __future__ import annotations

import json
import subprocess
import threading
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


def front_pid() -> int:
    """The process of the app in front; Inditeflow's own window is this very process."""
    try:
        from AppKit import NSWorkspace
        a = NSWorkspace.sharedWorkspace().frontmostApplication()
        return int(a.processIdentifier()) if a else 0
    except Exception:       # noqa: BLE001
        return 0


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
    in inditeflow_mac.py: that file is both the program and a module this one imports, so a class there is defined twice
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
        if w is None or not (w.win.styleMask() & (1 << 14)):      # unless Inditeflow itself is full screen
            NSApp.setActivationPolicy_(1)

    def quitInditeflow_(self, _sender):                      # noqa: N802
        self.app.quit_all(None)

    def openSettings_(self, _sender):                    # noqa: N802 - Inditeflow menu → Settings… ⌘,
        self.app.open_window(None)
        self.app.window.bridge.js("go('settings')")

    def openFile_(self, _sender):                        # noqa: N802 - File → Transcribe a file… ⌘O
        self.app.open_files(None)

    def fire_(self, _note):                              # noqa: N802
        w = self.app.window
        if w is None or not w.win.isVisible():
            self.app.open_window(None)


def main_menu(app) -> None:
    """
    The menus a Mac app is expected to have. Inditeflow had none, so in full screen the top bar was empty (no Close or
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

    menu("Inditeflow", [("About Inditeflow", "orderFrontStandardAboutPanel:", ""), None,
                    ("Settings…", "openSettings:", ","), None,
                    ("Hide Inditeflow", "hide:", "h"), None, ("Quit Inditeflow", "quitInditeflow:", "q")])
    menu("File", [("Transcribe a file…", "openFile:", "o")])
    for title in ("Quit Inditeflow", "Settings…"):             # through Inditeflow itself (quit also stops the engine)
        bar.itemAtIndex_(0).submenu().itemWithTitle_(title).setTarget_(app._activation)
    bar.itemAtIndex_(1).submenu().itemWithTitle_("Transcribe a file…").setTarget_(app._activation)
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
        from inditeflow_mac import can_listen, HOTKEYS
        audio_idx = store.audio_counts()                  # one directory listing, not one disk check per note
        return {
            "prefs": store.prefs(),
            "history": [dict(r, audio=store.audio_count(r, audio_idx), wt=r.get("wt") if store.wt_fits(r) else None) for r in
                        ([store.masked(r, self.app.prefs.get("my_swears")) for r in store.history()] if self.app.prefs.get("mask_swears")
                         else store.history())],
            "listening": bool(can_listen()),
            "hotkeys": HOTKEYS,
            "engine": self.app.engine_kind,
            "fixes_list": [list(f) for f in store.my_fixes()],              # file order (newest last); the page sorts
            "fix_counts": store.fix_counts(),
            "ai_providers": __import__("ai").PROVIDERS,
            "ai_models": __import__("ai").DEFAULT_MODEL,
            "ai_catalog": __import__("models").catalog(),    # models + effort levels to offer, live or built-in
            "ai_status": self.app.ai_who,
            "ai_keys": self.app.ai_keys,
            "mics": __import__("inditeflow_mac").mic_names(),
            "using": self.app.mic.using,
            "job": self.app.job,
            "meeting": {"running": self.app.meeting.running, "started": self.app.meeting.started,
                        "problem": self.app.meeting.problem, "note": self.app.meeting.note,
                        "mic": getattr(self.app.mic, "using", "") if self.app.meeting.running else ""},
            "mic_ok": __import__("inditeflow_mac").mic_allowed(),
            "ai_busy": self.app.ai_busy,
            "ai_cost_month": store.ai_cost_month(),           # (usd_total, with_cost_count, no_cost_count) — commit 4
            "notice": self.app.notice,
            "ai_error": self.app.ai_error,
            "ai_actions": {k: v[:3] for k, v in __import__("ai").ACTIONS.items()
                           if k != "review" or self.app.prefs.get("ai_review")},   # step 2: only while being tested
            "ai_styles": __import__("ai").STYLES,
            "ai_style_groups": __import__("ai").STYLE_GROUPS,
            "ai_langs": __import__("ai").LANGUAGES,
            "ai_names": __import__("ai").NAMES,
            "version": (Path(__file__).with_name("VERSION").read_text().strip()
                        if Path(__file__).with_name("VERSION").exists() else ""),
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
        try:
            self.handle(msg)
        except Exception:   # noqa: BLE001 - one bad action must never take the whole app down (17 Oct: it did)
            import traceback
            print("window action failed:", msg.get("action"))
            traceback.print_exc()
            self.js("toast('That didn’t work. The details are in the log.')")

    @objc.python_method
    def handle(self, msg: dict) -> None:
        act = msg.get("action")
        if act == "ready":
            self.app.check_ai()
        elif act == "pref":
            store.set_pref(msg.get("key", ""), msg.get("value"))
            self.app.reload_prefs()
            if msg.get("key") == "pill_clear":
                self.app.show_pill()
            if msg.get("key") == "theme" and self.app.window:
                self.app.window.theme()
        elif act == "models_refresh":                    # ask the provider which models and efforts it has (needs a key)
            def go() -> None:
                from PyObjCTools import AppHelper
                try:
                    import models
                    said = f"Model list updated: {models.refresh(msg.get('provider', ''))} models"
                except Exception as e:                       # noqa: BLE001 - say why, in a sentence
                    said = f"Could not refresh: {e}"
                AppHelper.callAfter(self.js, f"toast({said!r})")
                AppHelper.callAfter(self.app.refresh)
            threading.Thread(target=go, daemon=True).start()
        elif act == "box":                               # a text box in this window has / lost the cursor
            self.app.in_box = bool(msg.get("on"))
        elif act == "copy":
            self.app.typer.copy(msg.get("text", ""))
        elif act == "note":                              # star / to-do / title: only these fields may change
            fields = {k: v for k, v in (msg.get("set") or {}).items() if k in ("star", "todo", "title")}
            store.update(str(msg.get("id", "")), **fields)
        elif act == "edit":                              # your own correction of a note's text; one step of undo
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            new = str(msg.get("text", "")).strip()
            if row and new and new != row["text"]:
                self.edit_undo = (row["id"], row["text"])
                store.update(row["id"], text=new, edited=True)
        elif act == "word_times":                        # first Listen on a note: line its words up with the audio
            if msg.get("id") and msg.get("id") not in self.app.ai_busy:
                threading.Thread(target=self.app.line_up, args=(str(msg["id"]),), daemon=True).start()
        elif act == "edit_line":                         # one line of a meeting or file, from the Listen view
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            new = " ".join(str(msg.get("text", "")).split())
            if row and self.app.ai_busy.get(row["id"]) == "finding who spoke":
                self.js("toast(\"Wait until Who spoke has finished. It rewrites the lines.\")")
            elif row and new:
                old = store.edit_line(row, float(msg.get("start", 0)), str(msg.get("speaker", "")), new)
                if old is not None and old != new:
                    self.line_undo = (row["id"], float(msg.get("start", 0)), str(msg.get("speaker", "")), old)
                    self.js("toast('Line saved', () => send({action:'undo_line'}))")
        elif act in ("line_speaker", "merge_line"):      # Listen view: fix one line's speaker, or join it with the next
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            start, who = float(msg.get("start", 0)), str(msg.get("speaker", ""))
            if row and self.app.ai_busy.get(row["id"]) == "finding who spoke":
                self.js("toast(\"Wait until Who spoke has finished. It rewrites the lines.\")")
            elif row:
                keep = {k: row.get(k) for k in ("segments", "text", "wt", "edited")}
                done = store.set_speaker(row, start, who, str(msg.get("to", ""))) if act == "line_speaker" \
                    else store.merge_next(row, start, who)
                if done:
                    self.lines_undo = (row["id"], keep)
                    what = "Speaker changed" if act == "line_speaker" else "Lines joined"
                    self.js(f"toast({what!r}, () => send({{action:'undo_lines'}}))")
                elif act == "merge_line":
                    self.js("toast('Nothing to join: the next line is another speaker, or there is none')")
        elif act == "stop_job":                          # the file job card's Stop: the parts done so far are kept
            self.app.job_stop = True
        elif act == "said":                              # speech test: this note's text is exactly what was said
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            if row:
                store.update(row["id"], said=row["text"] if msg.get("on") else None)   # the stored words, never masked
        elif act == "undo_lines":
            u = getattr(self, "lines_undo", None)
            if u:
                store.update(u[0], **u[1])                       # None values remove what the change added
                self.lines_undo = None
        elif act == "undo_line":
            u = getattr(self, "line_undo", None)
            row = next((r for r in store.history() if u and r["id"] == u[0]), None)
            if row:
                store.edit_line(row, u[1], u[2], u[3])
                self.line_undo = None
        elif act == "undo_edit":
            if getattr(self, "edit_undo", None):
                store.update(self.edit_undo[0], text=self.edit_undo[1], edited=None)
                self.edit_undo = None
        elif act == "delete":                            # what: both (default) | audio | text. Each can be undone.
            nid, what = str(msg.get("id", "")), msg.get("what", "both")
            if what == "audio":
                self.undo = ("audio", nid, store.stash_audio(nid))
            elif what == "text":
                self.undo = ("text", store.delete_text(nid))
            else:
                self.undo = ("both", store.delete(nid), store.stash_audio(nid))
        elif act == "undo":
            u = getattr(self, "undo", None)
            if u:
                if u[0] == "audio":
                    store.unstash_audio(u[1])
                elif u[0] == "text" and u[1]:
                    store.replace(u[1])
                elif u[0] == "both" and u[1]:
                    store.restore(u[1])
                    store.unstash_audio(u[1]["id"])
                self.undo = None
        elif act == "export":
            self.app.export(str(msg.get("id", "")), str(msg.get("fmt", "txt")))
        elif act == "dismiss":
            self.app.file_error = ""
            self.app.ai_error = ""
        elif act == "mic_ask":
            from inditeflow_mac import ask_mic, mic_allowed
            if mic_allowed() is False:                   # refused before: only System Settings can change it
                subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"])
            else:
                ask_mic()
        elif act == "ax_open":
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
        elif act == "flag":                              # a likely mistake: fix it here, always, or it was fine
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            i, how = int(msg.get("i", -1)), msg.get("how")
            flags = list((row or {}).get("flags") or [])
            if row and 0 <= i < len(flags):
                f = flags.pop(i)
                before = store.log_fix(f["heard"], f["want"], how)
                text = row["text"]
                if how in ("fix", "always"):
                    import re as _re
                    text = _re.sub(r"(?<!\w)" + _re.escape(f["heard"]) + r"(?!\w)", lambda _m: f["want"], text, count=1, flags=_re.I)
                if how == "always":
                    why = store.fix_problem(f["heard"], f["want"])
                    if why:
                        self.js(f"toast({why!r})")
                    else:
                        store.add_fix(f["heard"], f["want"])
                decided = (row.get("reviewed") or []) + [{"heard": f["heard"], "want": f["want"], "how": how, "at": __import__("time").time()}]
                store.update(row["id"], text=text, flags=flags or None, reviewed=decided[-50:])    # kept so the list can filter by it
                if how == "fix" and before >= 1:         # the 2nd identical fix: offer to make it permanent
                    self.js(f"toast({'You fixed this before. Always fix ' + f['heard'] + ' → ' + f['want'] + '? Use Always fix next time.'!r})")
            self.push()
        elif act == "listen":                            # load a note's recording into the in-window player
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            files = store.audio_files(row) if row else []
            both = bool(row and row.get("clock") and len(files) == 2)   # recorded on one clock: play together
            track = int(msg["track"]) if msg.get("track") is not None else (2 if both else 0)
            track = 2 if track == 2 and both else min(track, max(0, len(files) - 1))
            if self.app.meeting.running:
                self.js("toast('Playback waits while a meeting is recording - the microphone would hear it')")
            elif row and row.get("live"):
                self.js("toast('This meeting is still recording')")
            elif files:
                try:
                    self.app.player.load(row["id"], files if track == 2 else files[track], track)
                    if msg.get("t"):
                        self.app.player.seek(float(msg["t"]))
                    if msg.get("autoplay", True):
                        self.app.player.play()
                except Exception as e:                   # noqa: BLE001 - a broken file must not take the window down
                    why = "" if "cannot be played" in str(e) else f" ({e})"
                    self.js(f"toast({('This recording cannot be played.' + why)!r})")
        elif act == "pctl":                              # the player's buttons and keys
            pl, cmd = self.app.player, msg.get("cmd")
            if cmd == "play" and not self.app.meeting.running:
                pl.play()
            elif cmd == "pause":
                pl.pause()
            elif cmd == "seek":
                pl.seek(float(msg.get("t", 0)))
            elif cmd == "skip" and pl.p:
                pl.seek(pl.state()["t"] + float(msg.get("d", 0)))
            elif cmd == "rate":
                pl.rate(float(msg.get("r", 1)))
            elif cmd == "volume":                        # 0..1; developer checks run silent
                pl.vol = max(0.0, min(1.0, float(msg.get("v", 1))))
                if pl.p:
                    pl.p.setVolume_(pl.vol)
            elif cmd == "stop":
                pl.stop()
                self.js(f"playerTick({json.dumps(pl.state())})")
        elif act == "reveal":                            # a note's kept recording, shown in Finder
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            files = [str(f) for f in store.audio_files(row)] if row else []
            if files:
                subprocess.run(["open", "-R", files[0]], check=False)
        elif act == "who":
            self.app.who_spoke(str(msg.get("id", "")), int(msg.get("k", 0) or 0))
        elif act == "meeting":
            self.app.toggle_meeting()
        elif act == "rename":                            # a speaker's name in one note: {"Others": "Rohit"}
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            old, new = str(msg.get("who", "")), " ".join(str(msg.get("name", "")).split())
            if len(new) > 40:                            # cut at a word, never mid-word, and say so
                new = new[:41].rsplit(" ", 1)[0] if " " in new[:41] else new[:40]
                self.js(f"toast({('Names are kept to 40 letters: ' + new)!r})")
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
        elif act == "combine":
            # Shelf → one combined note. then="ai" opens the Ask AI drawer right away; then="open" just scrolls to the
            # new row (user asked to save as a note without an AI call). The ids list keeps the shelf's order.
            ids = [str(x) for x in (msg.get("ids") or [])]
            then = str(msg.get("then") or "ai")
            new_id = store.combine(ids)
            if new_id:
                self.push()
                if then == "ai":
                    self.js(f"openDrawer({new_id!r})")
                else:
                    self.js(f"document.querySelector('.row[data-row=\"' + {new_id!r}.replace(/[.]/g, '\\\\.') + '\"]')?.scrollIntoView({{block:'center',behavior:'smooth'}}); toast('Combined note saved.')")
            else:
                self.js("toast('Pick at least 2 dictations with text to combine.')")
        elif act == "tasks":
            self.app.add_tasks(str(msg.get("id", "")), str(msg.get("label", "")))
        elif act == "ai_clear":                           # remove one AI answer, or the improved version
            row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
            if row:
                self.ai_undo = (row["id"], row.get("improved"), row.get("ai"))   # one step back: Undo on the toast
            if row and msg.get("label") == "improved":
                store.update(row["id"], improved=None)
            elif row:
                store.update(row["id"], ai=[a for a in row.get("ai", []) if a["label"] != msg.get("label")] or None)
        elif act == "ai_undo":
            u = getattr(self, "ai_undo", None)
            if u:
                store.update(u[0], improved=u[1], ai=u[2])
                self.ai_undo = None
        elif act == "add_fix":
            heard, want, editing = msg.get("heard", ""), msg.get("want", ""), bool(msg.get("edit"))   # edit: Dictionary page
            why = store.fix_problem(heard, want, editing)  # a refusal has to say why; it used to fail in silence
            if why:
                self.js(f"toast({why!r})")
            else:
                store.add_fix(heard, want, replace=editing)
                row = next((r for r in store.history() if r["id"] == msg.get("id")), None)
                fixed = store.apply_my_fixes(row["text"], [(heard.strip(), want.strip())]) if row else ""
                if row and fixed != row["text"]:             # this note only: past notes are never rewritten in bulk
                    store.update(row["id"], text=fixed)
                self.js(f"toast({('Fixed here and in future dictations: ' if row and fixed != row['text'] else 'Fix added: ') + heard.strip() + ' → ' + want.strip()!r})")
        elif act == "files":
            self.app.open_files(None)
        elif act == "fixes":
            self.app.edit_fixes(None)
        elif act == "clear":
            from AppKit import NSAlert, NSAlertFirstButtonReturn
            n = sum(1 for r in store.history() if not store.keep(r))
            alert = NSAlert.alloc().init()
            alert.setMessageText_(f"Delete {n} dictation{'s' if n != 1 else ''}?")
            alert.setInformativeText_("Starred notes, to-dos, files and meetings are kept. "
                                      "The rest is removed from this Mac and cannot be undone.")
            alert.addButtonWithTitle_("Delete")
            alert.addButtonWithTitle_("Cancel")
            alert.buttons()[0].setHasDestructiveAction_(True)
            if __import__('inditeflow_mac').run_modal(alert) == NSAlertFirstButtonReturn:
                store.clear()
        elif act == "permission":
            from inditeflow_mac import ask_to_listen
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
    is open Inditeflow becomes a normal app with a Dock icon, and goes back to living in the menu bar when it closes.
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
        if store.TEST:
            return
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
        self.win.setTitle_("Inditeflow")
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
        content.addScriptMessageHandler_name_(self.bridge, "inditeflow")
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
            "err: window.__err || '', keys: S.listening, size: [innerWidth, innerHeight], url: location.href.slice(-30)})",
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
        if store.TEST:                                      # the test copy: drawn, never seen, never in front
            self.win.setAlphaValue_(0.0)
            self.win.setIgnoresMouseEvents_(True)
            self.win.orderBack_(None)
            self.win.setFrameOrigin_((-30000.0, -30000.0))   # after ordering: macOS pulls a window on screen as it shows
            self.bridge.push()
            return
        NSApp.setActivationPolicy_(0)                       # a normal app while the window is open (see WindowEvents)
        NSApp.activateIgnoringOtherApps_(True)              # a menu-bar app has to ask for focus
        self.win.makeKeyAndOrderFront_(None)
        self.bridge.push()                                  # fresh history every time it opens
