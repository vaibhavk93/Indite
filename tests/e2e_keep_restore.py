"""Real-app check of the two 24 Oct founder reports, in the hidden test copy (needs macOS; ~1 minute):
   .venv/bin/python tests/e2e_keep_restore.py
1. "How many to keep": choosing Newest 500 with 519 plain dictations, then Delete them, must leave 500 at once
   (it used to wait for the next dictation, so nothing changed on screen).
2. Restore after Delete → words only / whole note: the note comes back (it used to say "already here")."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import e2e_testcopy as t  # noqa: E402  (its helpers: sh, ev, act, check)

D = t.D


def main():
    t.sh(*t.TC, "stop")
    for f in ("history.jsonl", "prefs.json"):
        (D / f).unlink(missing_ok=True)
    subprocess.run(["rm", "-rf", str(D / "audio"), str(D / "audio_trash")])
    sys.path.insert(0, str(ROOT / "mac"))
    os.environ["INDITE_DATA"] = str(D)
    import store  # noqa: PLC0415
    store.set_pref("history_cap", 0)
    (D / "audio").mkdir()
    ids = [store.add(f"dictation number {i}", 1, 1, "done", "x") for i in range(519)]
    for i in ids[:5] + ids[-3:]:
        (D / "audio" / f"{i}.wav").write_bytes(b"RIFF")
    zipf = D / "before.zip"
    t.check("519 notes seeded", len(store.history()) == 519, len(store.history()))
    store.backup(zipf, "all", with_audio=True)
    t.sh(*t.TC, "start")
    time.sleep(7)

    print("\n== keep limit through the real page ==")
    t.js("go('settings'); sgo('privacy')")
    t.ev("(()=>{document.querySelectorAll('#set-history_cap button')[0].click();return 1})()")
    warn = t.ev("document.querySelector('#cap-warn-slot').innerText") or ""
    t.check("choosing Newest 500 asks first and names 19 notes", "19" in warn and "Delete them" in warn, warn)
    t.check("nothing is deleted before the answer", len(store.history()) == 519)
    t.ev("(()=>{document.querySelector('#cap-yes').click();return 1})()", wait=3)
    store._cache["sig"] = None
    t.check("Delete them deletes now: 500 left on disk", len(store.history()) == 500, len(store.history()))
    shown = t.ev("S.history.filter(r=>!(r.star||r.todo||(r.kind||'dictation')!=='dictation')).length")
    t.check("and the page shows 500", shown == 500, shown)
    t.ev("(()=>{document.querySelectorAll('#set-history_cap button')[2].click();return 1})()")      # Everything
    t.ev("(()=>{document.querySelectorAll('#set-history_cap button')[0].click();return 1})()")      # back to 500
    shown = t.ev("S.history.filter(r=>!(r.star||r.todo||(r.kind||'dictation')!=='dictation')).length")
    t.check("Everything and back: still 500, no question", shown == 500 and not (t.ev("document.querySelector('#cap-warn-slot').innerText") or ""), shown)
    gone = [i for i in ids[:19]]
    t.check("the recordings of the 19 deleted notes are gone too", not any((D / "audio" / f"{i}.wav").exists() for i in gone))
    t.check("the recordings of kept notes stay", (D / "audio" / f"{ids[-1]}.wav").exists())

    print("\n== restore ==")
    n = store.restore_zip(zipf)
    t.check("restoring while the limit is 500 says so honestly: 0 restored, 19 over the limit", n == 0 and store.restore_zip.over_limit == 19, (n, store.restore_zip.over_limit))
    t.act(action="pref", key="history_cap", value=0)
    n = store.restore_zip(zipf)
    store._cache["sig"] = None
    t.check("with Everything on, the 19 older notes come back", n == 19 and len(store.history()) == 519, (n, len(store.history())))
    t.check("and their recordings", (D / "audio" / f"{ids[0]}.wav").exists())
    target = ids[100]
    t.act(action="delete", id=target, what="text")
    store._cache["sig"] = None
    t.check("Delete → words only leaves an empty note", next(r for r in store.history() if r["id"] == target)["text"] == "")
    n = store.restore_zip(zipf)
    store._cache["sig"] = None
    row = next(r for r in store.history() if r["id"] == target)
    t.check("Restore refills the words (it used to say 'already here')", n == 1 and row["text"] == "dictation number 100" and not row.get("text_deleted"), (n, row))
    t.act(action="delete", id=target, what="both")
    store._cache["sig"] = None
    t.check("Delete → both removes the note", not any(r["id"] == target for r in store.history()))
    n = store.restore_zip(zipf)
    store._cache["sig"] = None
    t.check("Restore brings the whole note back", n == 1 and any(r["id"] == target for r in store.history()), n)
    t.check("a second restore changes nothing", store.restore_zip(zipf) == 0)
    t.sh(*t.TC, "stop")
    print("\nfailures:", len(t.FAILS), t.FAILS)
    sys.exit(len(t.FAILS))


if __name__ == "__main__":
    main()
