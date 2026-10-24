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

    log = (D / "indite.log").read_text()
    check("no Python errors in the log", "Traceback" not in log and "window action failed" not in log, [l for l in log.splitlines() if "Traceback" in l or "failed" in l][:3])
    sh(*TC, "stop")
    print(f"\n{len(FAILS)} failure(s)" if FAILS else "\nAll checks passed")
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(main())
