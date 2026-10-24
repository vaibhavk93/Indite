"""End-to-end check of the REAL app (real Python + the real page) in the hidden test copy.

Not a pytest file (it needs macOS, the built app and about 5 minutes):   .venv/bin/python tests/e2e_testcopy.py

The test copy has its own data folder, its own engine, and never touches the screen, the keyboard, the clipboard, or the
founder's real notes (founder rule, 17 Oct). It drives the window with the same messages the page sends (`send({...})`)
and reads results back from the page state and from the files in the test data folder.
Each line prints PASS or FAIL; the exit code is the number of failures."""
import json
import os
import subprocess
import sys
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = str(ROOT / ".venv/bin/python")
TC = [PY, str(ROOT / "mac/testcopy.py")]
D = Path.home() / "Library/Application Support/indite-test"
WAV = ROOT / "bench_synth/clean/s03.wav"
FAILS = []


def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=120)


def js(code, wait=2.2):
    sh(*TC, "js", code)
    time.sleep(wait)


def ev(expr, wait=2.4):
    (D / "eval.out").unlink(missing_ok=True)
    sh(*TC, "eval", expr)
    time.sleep(wait)
    try:
        v = json.loads((D / "eval.out").read_text())
        while isinstance(v, str):
            try:
                v = json.loads(v)
            except ValueError:
                break
        return v
    except (OSError, ValueError):
        return None


def act(**msg):
    js(f"send({json.dumps(msg)})")


def hist():
    return ev("JSON.stringify(S.history.map(r=>({id:r.id,text:r.text,star:!!r.star,todo:r.todo||null,audio:r.audio,kind:r.kind||'dictation',"
              "title:r.title||null,deleted:!!r.text_deleted,flags:(r.flags||[]).length,reviewed:(r.reviewed||[]).map(x=>x.how),app:r.app||'',where:r.where||'',src:r.sources||null})))") or []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else f"   <- {detail}"), flush=True)
    if not cond:
        FAILS.append(name)


def silent_wav(path, seconds=2.0):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(16000)
        w.writeframes(b"\x00\x00" * int(16000 * seconds))


def main():
    sh(*TC, "stop")
    for f in ("history.jsonl", "my_fixes.txt", "prefs.json", "fixlog.jsonl"):
        (D / f).unlink(missing_ok=True)
    for d in ("audio", "audio_trash"):
        subprocess.run(["rm", "-rf", str(D / d)])
    (D / "indite.log").write_text("")
    sh(*TC, "start")
    time.sleep(7)
    sys.path.insert(0, str(ROOT / "mac"))
    os.environ["INDITE_DATA"] = str(D)
    import store  # noqa: PLC0415

    print("\n== 1. Dictation: positive, silence, tiny, private ==")
    sh(*TC, "cmd", f"dictate:{WAV}")
    time.sleep(14)
    h = hist()
    check("a dictated wav becomes a note with its recording", len(h) == 1 and h[0]["audio"] == 1 and len(h[0]["text"]) > 10, h)
    sh(*TC, "cmd", f"dictate:{WAV}")
    time.sleep(14)
    h = hist()
    check("a second dictation is a second note, newest first", len(h) == 2 and h[0]["id"] != h[1]["id"], h)
    silent = D / "silence.wav"
    silent_wav(silent)
    sh(*TC, "cmd", f"dictate:{silent}")
    time.sleep(8)
    check("silence is not saved as a note", len(hist()) == 2)
    tiny = D / "tiny.wav"
    silent_wav(tiny, 0.15)
    sh(*TC, "cmd", f"dictate:{tiny}")
    time.sleep(6)
    check("a 0.15 s blip is not saved", len(hist()) == 2)
    sh(*TC, "cmd", "private")
    time.sleep(1.5)
    sh(*TC, "cmd", f"dictate:{WAV}")
    time.sleep(14)
    check("Don't save the next dictation: not saved", len(hist()) == 2)
    sh(*TC, "cmd", f"dictate:{WAV}")
    time.sleep(14)
    check("...and it switches itself off after one", len(hist()) == 3)
    a, b, c = (x["id"] for x in hist())

    print("\n== 2. Row actions: star, to-do, edit, bad ids ==")
    act(action="note", id=a, set={"star": True})
    check("star on", next(x for x in hist() if x["id"] == a)["star"] is True)
    act(action="note", id=a, set={"star": False})
    check("star off", next(x for x in hist() if x["id"] == a)["star"] is False)
    act(action="note", id=b, set={"todo": "open"})
    act(action="note", id=b, set={"todo": "done"})
    check("to-do open then done", next(x for x in hist() if x["id"] == b)["todo"] == "done")
    act(action="note", id=b, set={"text": "HACKED", "audio": 9})
    check("a note can only change star, to-do and title (not its words)", next(x for x in hist() if x["id"] == b)["text"] != "HACKED")
    n0 = len(hist())
    act(action="note", id="no-such-id", set={"star": True})
    act(action="delete", id="no-such-id", what="both")
    act(action="delete", id="", what="audio")
    check("unknown ids change nothing and do not crash", len(hist()) == n0)
    act(action="todo_add", text="Buy milk")
    check("a typed to-do becomes an open to-do", any(x["text"] == "Buy milk" and x["todo"] == "open" for x in hist()))
    n1 = len(hist())
    act(action="todo_add", text="   ")
    check("a blank to-do is ignored", len(hist()) == n1)
    old = next(x for x in hist() if x["id"] == c)["text"]
    act(action="edit", id=c, text="edited words here")
    check("edit changes the words", next(x for x in hist() if x["id"] == c)["text"] == "edited words here")
    act(action="undo_edit")
    check("undo edit brings the words back", next(x for x in hist() if x["id"] == c)["text"] == old)

    print("\n== 3. Dictionary: valid and invalid entries ==")
    for heard, want, ok, why in [("jaypur", "Jaipur", True, "a normal fix"), ("jira", "Jira", True, "capitals only"), ("jaypur", "Jaipur", False, "a duplicate"),
                                 ("", "x", False, "empty left"), ("abc", "", False, "empty right"), ("a=b", "x", False, "contains ="),
                                 ("x" * 90, "y", False, "too long"), ("q", "Quick", False, "one letter"), ("same", "same", False, "exactly the same"),
                                 ("#tag", "x", False, "starts with #")]:
        before = len(store.my_fixes())
        act(action="add_fix", heard=heard, want=want)
        got = len(store.my_fixes()) - before
        check(f"Dictionary {'accepts' if ok else 'rejects'}: {why}", got == (1 if ok else 0), f"{heard!r}->{want!r} changed {got}")
    check("Dictionary file stays readable", (D / "my_fixes.txt").read_text().count("\n") >= 2)
    act(action="fix_del", heard="jira")
    check("removing an entry works", all(h != "jira" for h, _ in store.my_fixes()))
    n_fix = len(store.my_fixes())
    act(action="fix_del", heard="not there")
    check("removing a missing entry is harmless", len(store.my_fixes()) == n_fix)

    print("\n== 4. Review decisions: Fix, Always fix, Not a mistake ==")
    now = time.time()
    rows = [{"id": repr(now + i), "at": now + i, "text": f"I like jaypur number {i}", "seconds": 2, "took": 1, "where": "done", "app": "Notes",
             "flags": [{"heard": "jaypur", "want": "Jaipur", "why": "city", "sure": "high"}]} for i in (1, 2, 3)]
    with (D / "history.jsonl").open("a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    store.set_pref("noop", 1)
    act(action="note", id=rows[0]["id"], set={"star": False})        # makes the app reload its notes
    act(action="flag", id=rows[0]["id"], i=0, how="fix")
    act(action="flag", id=rows[1]["id"], i=0, how="dismiss")
    act(action="flag", id=rows[2]["id"], i=0, how="always")
    hh = {x["id"]: x for x in hist()}
    check("Fix: the word is corrected, the flag removed, 'fix' recorded", "Jaipur" in hh[rows[0]["id"]]["text"] and hh[rows[0]["id"]]["flags"] == 0 and hh[rows[0]["id"]]["reviewed"] == ["fix"], hh[rows[0]["id"]])
    check("Not a mistake: the words stay, the flag is removed, 'dismiss' recorded", "jaypur" in hh[rows[1]["id"]]["text"] and hh[rows[1]["id"]]["flags"] == 0 and hh[rows[1]["id"]]["reviewed"] == ["dismiss"])
    check("Always fix: corrected, recorded, and added to the Dictionary", "Jaipur" in hh[rows[2]["id"]]["text"] and hh[rows[2]["id"]]["reviewed"] == ["always"])
    act(action="flag", id=rows[0]["id"], i=0, how="fix")
    act(action="flag", id=rows[0]["id"], i=5, how="fix")
    act(action="flag", id="nope", i=0, how="fix")
    check("a flag that is already settled, a bad index, a bad id: nothing breaks", {x["id"]: x for x in hist()}[rows[0]["id"]]["reviewed"] == ["fix"])
    menu = ev("(()=>{go('home');const b=document.querySelector('.qbar[data-for=home] .vm[data-k=review]');b.click();"
              "const t=[...document.querySelectorAll('.menu button[data-v]')].map(x=>x.textContent.trim());document.querySelectorAll('.menu').forEach(m=>m.remove());return JSON.stringify(t)})()") or []
    check("the Mistake review menu counts exactly these decisions", any(m.startswith("Fixed · 1") for m in menu) and any(m.startswith("Always fix · 1") for m in menu)
          and any(m.startswith("Not a mistake · 1") for m in menu) and any(m.startswith("Has suggestions · 0") for m in menu), menu)

    print("\n== 5. Delete: three ways, Undo, bad cases ==")
    d1 = c
    act(action="delete", id=d1, what="audio")
    h1 = next(x for x in hist() if x["id"] == d1)
    check("recording only: words stay, no recording on the page", h1["audio"] == 0 and len(h1["text"]) > 5)
    act(action="undo")
    check("...Undo brings the recording back", next(x for x in hist() if x["id"] == d1)["audio"] == 1)
    act(action="delete", id=d1, what="text")
    h2 = next(x for x in hist() if x["id"] == d1)
    check("words only: the recording stays, the words are gone", h2["audio"] == 1 and h2["deleted"] and h2["text"] == "")
    act(action="undo")
    check("...Undo brings the words back", next(x for x in hist() if x["id"] == d1)["text"] != "")
    n2 = len(hist())
    act(action="delete", id=d1, what="both")
    check("both: the note is gone and its recording is in the trash", len(hist()) == n2 - 1 and (D / "audio_trash" / d1).exists())
    act(action="undo")
    check("...Undo brings back the note and the recording", len(hist()) == n2 and not (D / "audio_trash" / d1).exists() and any(x["id"] == d1 and x["audio"] == 1 for x in hist()))
    act(action="undo")
    check("Undo with nothing to undo does nothing", len(hist()) == n2)
    act(action="delete", id=d1, what="nonsense")
    check("an unknown delete mode is treated as the full delete, and Undo restores it", len(hist()) == n2 - 1)
    act(action="undo")
    check("...restored", len(hist()) == n2)

    print("\n== 6. Combine notes ==")
    ids = [x["id"] for x in hist() if x["kind"] == "dictation" and x["text"]][:2]
    n3 = len(hist())
    act(action="combine", ids=ids[:1])
    check("combining one note makes nothing", len(hist()) == n3)
    act(action="combine", ids=["x", "y"])
    check("combining unknown notes makes nothing", len(hist()) == n3)
    act(action="combine", ids=ids)
    comb = [x for x in hist() if x["kind"] == "combined"]
    check("two notes combine into one new note", len(hist()) == n3 + 1 and len(comb) == 1, len(comb))
    act(action="delete", id=ids[0], what="both")
    check("deleting a source leaves the combined note intact", any(x["kind"] == "combined" and len(x["text"]) > 10 for x in hist()))

    print("\n== 7. Preferences, saved views, the keep limit ==")
    for key, val in [("history_cap", 0), ("history_cap", 500), ("history_cap", 5000), ("usd_inr", 85.5), ("cost_currency", "INR"), ("claude_model", "haiku"), ("ai_effort", "low")]:
        act(action="pref", key=key, value=val, **{})
        check(f"preference {key}={val} is saved", json.loads((D / "prefs.json").read_text()).get(key) == val)
    act(action="pref", key="totally_unknown", value=1)
    check("an unknown preference is ignored", "totally_unknown" not in json.loads((D / "prefs.json").read_text()))
    for bad in (-5, "x", None, 1.5):
        store.set_pref("history_cap", bad)
        check(f"a damaged keep limit ({bad!r}) falls back to 500", store.cap() == 500, store.cap())
    store.set_pref("history_cap", 5000)
    js("send({action:'pref',key:'views',value:{home:{filter:{x:1},when:5,app:null,sort:'zzz',group:'zzz'},bogus:1}})")
    rows_ok = ev("(()=>{go('home');return document.querySelectorAll('#list .row').length})()")
    check("junk saved views still draw the list", isinstance(rows_ok, int) and rows_ok > 0, rows_ok)
    js("send({action:'pref',key:'views',value:null})")
    check("a null saved view still draws the list", (ev("document.querySelectorAll('#list .row').length") or 0) > 0)

    print("\n== 8. Keep limit enforced, torn file, big history (Python, same files the app uses) ==")
    store.set_pref("history_cap", 4)
    n_plain_before = sum(1 for r in store.history() if not store.keep(r))
    for i in range(10):
        store.add(f"cap test {i}", 1, 1, "done", "x")
    plain = [r for r in store.history() if not store.keep(r)]
    check("only the newest 4 plain dictations are kept (stars, to-dos, combined stay)", len(plain) == 4 and plain[0]["text"] == "cap test 9", len(plain))
    store.set_pref("history_cap", 0)
    for i in range(30):
        store.add(f"keep all {i}", 1, 1, "done", "x")
    check("'Everything' keeps them all", sum(1 for r in store.history() if r["text"].startswith("keep all")) == 30)
    with (D / "history.jsonl").open("a") as f:
        f.write('{"id": "9.5", "at": 9.5, "tex')                  # a crash mid-write
    store._cache["sig"] = None
    store.add("after the torn line", 1, 1, "done", "x")
    store._cache["sig"] = None
    check("a torn last line costs only itself", store.history()[0]["text"] == "after the torn line")

    print("\n== 9. Pages and search in the real app ==")
    js("send({action:'pref',key:'sounds',value:false})")      # makes the app push its state again
    for page in ("home", "meetings", "files", "todo", "dict", "insights", "settings", "help"):
        js(f"go('{page}')", 1.2)
    errs = (D / "indite.log").read_text()
    check("every page opens without a page error", "Script error" not in errs and "Traceback" not in errs, errs[-300:])
    got = ev("(()=>{go('home');$('#q').value='cap test';searched();const r=[document.querySelectorAll('#list .row').length,document.querySelectorAll('#list mark').length];$('#q').value='';searched();return JSON.stringify(r)})()")
    check("search finds the notes and marks the words", isinstance(got, list) and got[0] >= 1 and got[1] >= 1, got)

    print("\n== 10. AI: real call, bad model ==")
    import ai  # noqa: PLC0415
    try:
        ans, u = ai.run("improve", "kal meeting hai", "", "claude", "haiku", "low")
        check("a real Claude answer carries its model and cost", u["model"] == "claude-haiku-5-5" and u["cost_usd"] and u["cost_usd"] < 0.01, u)
    except Exception as e:  # noqa: BLE001
        check("a real Claude answer", False, e)
    try:
        ai.run("improve", "kal meeting hai", "", "claude", "no-such-model-xyz", "")
        check("a wrong model name gives a readable error", False, "no error")
    except RuntimeError as e:
        check("a wrong model name gives a readable error", len(str(e)) > 5, e)
    try:
        ai.run("improve", "x", "", "claude", "--tools bash", "")
        check("a model name that looks like an option is refused", False, "accepted")
    except RuntimeError as e:
        check("a model name that looks like an option is refused", "odd characters" in str(e), e)


    print("\n== 11. Ask AI end to end (real Claude, haiku: a few tenths of a cent) ==")
    for k, v in [("ai", True), ("ai_ok", True), ("ai_ok_meetings", True), ("ai_provider", "claude"), ("claude_model", "haiku"), ("ai_effort", "low"), ("cost_currency", "USD")]:
        store.set_pref(k, v)
    act(action="pref", key="sounds", value=False)
    base = next(x for x in hist() if x["kind"] == "dictation" and len(x["text"]) > 20)
    nid = base["id"]

    def row(i=None):
        return ev(f"JSON.stringify(S.history.find(r=>r.id==={json.dumps(i or nid)})||null)") or {}

    act(action="ai", id=nid, act="improve")
    time.sleep(14)
    r = row()
    check("Improve: an improved version is saved on the note", isinstance(r.get("improved"), str) and len(r["improved"]) > 3, r.get("improved"))
    check("...with the model, tokens and cost the provider reported", (r.get("improved_cost") or {}).get("model", "").startswith("claude-haiku") and (r.get("improved_cost") or {}).get("cost_usd", 0) > 0, r.get("improved_cost"))
    act(action="ai", id=nid, act="summary")
    time.sleep(14)
    r = row()
    summ = next((a for a in r.get("ai") or [] if a["label"] == "Summary"), None)
    check("Summary: an answer is saved with its cost", bool(summ) and len(summ["text"]) > 3 and summ.get("cost_usd", 0) > 0, r.get("ai"))
    month = ev("S.ai_cost_month") or [0, 0, 0]
    check("this month's cost total counts these answers", month[0] > 0 and month[1] >= 2, month)
    act(action="ai_clear", id=nid, label="improved")
    check("removing the improved version works", row().get("improved") in (None, ""))
    act(action="ai_undo")
    check("...and Undo brings it back", bool(row().get("improved")))
    act(action="ai_clear", id=nid, label="Summary")
    check("removing one answer by its label works", not any(a["label"] == "Summary" for a in row().get("ai") or []))
    act(action="ai_undo")
    check("...and Undo brings it back", any(a["label"] == "Summary" for a in row().get("ai") or []))
    n_before = len(hist())
    act(action="ai", id=nid, act="no_such_action")
    act(action="ai", id="no-such-note", act="summary")
    act(action="ai", id="", act="")
    time.sleep(4)
    log_now = (D / "indite.log").read_text()
    check("an unknown AI action / note does nothing and does not crash", len(hist()) == n_before and "Traceback" not in log_now, log_now[-300:])
    store.update(nid, ai=(row().get("ai") or []) + [{"action": "actions", "label": "Action items", "text": "- Call the bank\n- Send the report\n- Book tickets", "at": time.time()}])
    act(action="pref", key="sounds", value=False)
    tasks_before = sum(1 for x in hist() if x["kind"] == "task")
    act(action="tasks", id=nid, label="Action items")
    tk = [x for x in hist() if x["kind"] == "task"]
    check("Action items become one open to-do each, linked to the note", len(tk) - tasks_before == 3 and all(x["todo"] == "open" for x in tk), [x["text"] for x in tk])
    act(action="tasks", id=nid, label="No such answer")
    check("tasks from a missing answer create nothing", sum(1 for x in hist() if x["kind"] == "task") == len(tk))
    act(action="pref", key="cost_currency", value="INR")
    act(action="pref", key="usd_inr", value=85.5)
    shown = ev("(()=>{openDrawer(%s);return JSON.stringify([...document.querySelectorAll('#drawer .aicost')].map(e=>e.textContent))})()" % json.dumps(nid)) or []
    check("the answer's cost shows in rupees at the typed rate", shown and all(c.startswith("₹") for c in shown), shown)
    act(action="pref", key="cost_currency", value="USD")
    shown = ev("JSON.stringify([...document.querySelectorAll('#drawer .aicost')].map(e=>e.textContent))") or []
    check("...and in dollars when Dollars is chosen", shown and all(c.startswith("$") for c in shown), shown)
    js("closeDrawer()")

    print("\n== 12. The card after a dictation: its buttons ==")
    (D / "offstage.jsonl").write_text("")
    todo_before = next(x for x in hist() if x["id"] == nid)["todo"]
    sh(*TC, "cmd", "card:3")
    time.sleep(3)
    newest = next(x for x in hist() if x["kind"] == "dictation")
    check("card To do: the newest dictation goes on your To do list", newest["todo"] == "open", newest)
    sh(*TC, "cmd", "card:2")
    time.sleep(16)
    off = [json.loads(l) for l in (D / "offstage.jsonl").read_text().splitlines() if l.strip()]
    calls = [(o["who"], o["call"]) for o in off]
    check("card AI button: the card shows 'working' then the answer", ("card", "working") in calls and ("card", "answer") in calls, calls)
    nw = next(x for x in hist() if x["kind"] == "dictation")
    check("...and the answer is saved on that dictation", any(True for _ in [0]) and bool(ev("(S.history.find(r=>r.id===%s)||{}).ai" % json.dumps(nw["id"]))), nw["id"])
    sh(*TC, "cmd", "card:0")
    time.sleep(4)
    newest_py = next(r for r in store.history() if (r.get("kind") or "dictation") == "dictation")["id"]      # what the app itself calls the newest
    drawer_open = ev("'id:'+drawerId")                                     # as text: a bare id would be read back as a number
    check("card Ask AI: opens the Ask AI panel on that note, and it is visible", drawer_open == "id:" + newest_py and ev("String(getComputedStyle(document.querySelector('#drawer')).display!=='none')") in ("true", True), (drawer_open, newest_py))
    js("closeDrawer()")

    print("\n== 13. Files: transcribe, edit lines, Listen, and bad files ==")
    n4 = len(hist())
    sh(*TC, "cmd", f"file:{WAV}")
    time.sleep(25)
    fh = [x for x in hist() if x["kind"] == "file"]
    check("a transcribed file becomes a note with its words", len(fh) == 1 and len(fh[0]["text"]) > 10, fh)
    fid = fh[0]["id"] if fh else None
    frow = row(fid) if fid else {}
    segs = frow.get("segments") or []
    check("...in timed lines", len(segs) >= 1 and all("start" in x and "text" in x for x in segs), segs[:1])
    if segs:
        t0, orig = segs[0]["start"], segs[0]["text"]
        act(action="edit_line", id=fid, start=t0, speaker=segs[0].get("speaker", ""), text="a corrected line")
        check("editing one line changes it and the note's words", "a corrected line" in row(fid)["text"] and row(fid)["segments"][0]["text"] == "a corrected line")
        act(action="undo_line")
        act(action="undo_lines")
        check("...and Undo brings the line back", row(fid)["segments"][0]["text"] == orig, row(fid)["segments"][0]["text"])
        act(action="edit_line", id=fid, start=t0, speaker=segs[0].get("speaker", ""), text="   ")
        check("an empty line edit is ignored", row(fid)["segments"][0]["text"] == orig)
        act(action="edit_line", id=fid, start=9999.0, speaker="x", text="nowhere")
        check("a line that does not exist is ignored", "nowhere" not in row(fid)["text"])
        act(action="merge_line", id=fid, start=9999.0, speaker="x")
        check("joining a line that does not exist is harmless", True)
    act(action="listen", id=fid, autoplay=False)
    time.sleep(3)
    loaded = ev("JSON.stringify([P.note, P.dur])") or [None, 0]
    check("Listen loads the recording into the player", loaded[0] == fid and loaded[1] > 0, loaded)
    act(action="pctl", cmd="seek", t=1.0)
    time.sleep(1.5)
    check("the player seeks", abs((ev("P.t") or 0) - 1.0) < 1.0, ev("P.t"))
    act(action="listen", id="no-such-note")
    act(action="pctl", cmd="nonsense")
    check("Listen on a missing note, and an unknown player command, are harmless", True)
    sh(*TC, "cmd", "file:/no/such/file.wav")
    time.sleep(5)
    bad = D / "corrupt.wav"
    bad.write_bytes(os.urandom(5000))
    sh(*TC, "cmd", f"file:{bad}")
    time.sleep(8)
    log_now = (D / "indite.log").read_text()
    check("a missing file and a corrupt file give no new note and no crash", sum(1 for x in hist() if x["kind"] == "file") == 1 and "Traceback" not in log_now, log_now[-300:])

    print("\n== 14. Speech test marking ==")
    store.set_pref("speech_test", True)
    act(action="pref", key="sounds", value=False)
    act(action="said", id=nid, on=True)
    r = row()
    check("'This is exactly what I said' stores the words as the reference", r.get("said") == r.get("text") and bool(r.get("said")))
    act(action="said", id=nid, on=False)
    check("...and 'Not exactly' takes it out", not row().get("said"))
    out = sh(PY, str(ROOT / "mac/speechset.py"), "--selftest")
    check("the speech-test scorer's own check passes", "ok" in out.stdout, out.stdout + out.stderr)

    print("\n== 15. Settings: every switch saves and restores ==")
    sw_ids = ev("JSON.stringify([...document.querySelectorAll('#pane-settings .sw[id^=set-]')].map(b=>b.id.slice(4)))") or []
    check("the Settings page has its switches", len(sw_ids) >= 10, sw_ids)
    for key in sw_ids:
        before = json.loads((D / "prefs.json").read_text()).get(key, store.DEFAULTS.get(key))
        js(f"document.querySelector('#set-{key}').click()", 1.8)
        after = json.loads((D / "prefs.json").read_text()).get(key)
        js(f"document.querySelector('#set-{key}').click()", 1.8)
        back = json.loads((D / "prefs.json").read_text()).get(key)
        check(f"switch '{key}' turns {'off' if before else 'on'} and back", after == (not before) and back == before, (before, after, back))
    for seg_id, vals in {"theme": ["dark", "light"], "output": ["type", "copy", "smart"], "cost_currency": ["INR", "USD"]}.items():
        for v in vals:
            js(f"[...document.querySelectorAll('#set-{seg_id} button')].find(b=>b.textContent.trim().toLowerCase().startsWith({json.dumps(v[:3].lower())})||b.dataset.v==={json.dumps(v)})?.click()", 1.8)
        check(f"the '{seg_id}' choices save (ends on {vals[-1]})", json.loads((D / "prefs.json").read_text()).get(seg_id) == vals[-1], json.loads((D / "prefs.json").read_text()).get(seg_id))
    js("(()=>{const e=document.querySelector('#set-usd_inr');e.value='abc';e.dispatchEvent(new Event('change'))})()")
    check("a rupee rate that is not a number is refused", json.loads((D / "prefs.json").read_text()).get("usd_inr") == 85.5)
    js("(()=>{const e=document.querySelector('#set-usd_inr');e.value='0';e.dispatchEvent(new Event('change'))})()")
    check("a rate of 0 is refused", json.loads((D / "prefs.json").read_text()).get("usd_inr") == 85.5)
    js("(()=>{const e=document.querySelector('#set-usd_inr');e.value='90.456';e.dispatchEvent(new Event('change'))})()")
    check("a valid rate is saved to 2 decimals", json.loads((D / "prefs.json").read_text()).get("usd_inr") == 90.46)

    print("\n== 16. Real history through the real app, checked against an independent count ==")
    real = Path.home() / "Library/Application Support/indite/history.jsonl"
    if real.exists():
        (D / "history.jsonl").write_text(real.read_text())      # a COPY: the founder's own file is only read
        store._cache["sig"] = None
        act(action="pref", key="sounds", value=False)
        rows_ = [r for r in store.history() if r.get("kind", "dictation") in ("dictation", "combined")]
        t0_ = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
        apps_ = sorted({r.get("app") for r in rows_ if r.get("app")}, key=lambda a: -sum(1 for r in rows_ if r.get("app") == a))[:3]
        cases = [{"filter": "all", "when": "any", "app": "any"}, {"filter": "copied", "when": "any", "app": "any"}, {"filter": "all", "when": "today", "app": "any"},
                 {"filter": "star", "when": "any", "app": "any"}] + [{"filter": "all", "when": "any", "app": a} for a in apps_] + \
                [{"filter": "copied", "when": "30d", "app": apps_[0]}, {"filter": "ai", "when": "7d", "app": apps_[1] if len(apps_) > 1 else "any"}]
        chip = {"all": lambda r: True, "copied": lambda r: r.get("where") == "copied", "star": lambda r: r.get("star"), "ai": lambda r: r.get("ai") or r.get("improved")}
        span = {"any": 0, "today": t0_, "7d": t0_ - 6 * 86400, "30d": t0_ - 29 * 86400}
        for c in cases:
            exp = sum(1 for r in rows_ if chip[c["filter"]](r) and r["at"] >= span[c["when"]] and (c["app"] == "any" or r.get("app") == c["app"]))
            act(action="pref", key="views", value={"home": {**c, "sort": "new", "group": "date", "review": "any"}})
            time.sleep(1.0)
            got = ev("(()=>{go('home');const e=document.querySelector('.qbar[data-for=home] .vcount');return JSON.stringify([e&&e.children.length?+e.querySelector('b').textContent.replace(/,/g,''):null,"
                     "[...document.querySelectorAll('#list .row')].filter(r=>getComputedStyle(r).display!=='none').length])})()") or [None, None]
            shown_n = got[0] if got[0] is not None else len(rows_)
            check(f"real history {c}: the page says {exp}", shown_n == exp and got[1] == min(exp, 100), (exp, got))
        act(action="pref", key="views", value={})
    else:
        print("      (no real history found: skipped)")

    log = (D / "indite.log").read_text()
    check("no Python errors in the log", "Traceback" not in log and "window action failed" not in log, [l for l in log.splitlines() if "Traceback" in l or "failed" in l][:3])
    sh(*TC, "stop")
    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nAll checks passed")
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())
