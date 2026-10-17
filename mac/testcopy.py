"""
The hidden test copy of indite (founder rule, 17 Oct: "never test on my screen while I work").

    python mac/testcopy.py start           # own data folder + own engine (port 8712); nothing on screen
    python mac/testcopy.py js "go('meetings')"
    python mac/testcopy.py eval "S.history.length"
    python mac/testcopy.py cmd "dictate:/path/to/clip.wav"     # any demo.cmd verb (see InditeApp.demo_cmd)
    python mac/testcopy.py shot home        # a picture of its window -> <data>/snapshot-home.png
    python mac/testcopy.py stop

What it never does (store.TEST): listen to keys, open the mic, type, copy, show a pill / card / menu icon, come to the
front, play sound, or restart itself. What the card or the typer would have done goes to <data>/offstage.jsonl.
Typing into other apps and the pill itself still need the real screen, with the founder's OK.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path.home() / "Library/Application Support/indite-test"
APP = ROOT / "dist/indite.app"
PREFS = {"setup_done": True, "sounds": False, "asked_screen": True, "preview": True, "ai": False, "keep_audio": True}


def pid() -> str:
    out = subprocess.run(["ps", "-Eaxo", "pid=,command="], capture_output=True, text=True).stdout   # -E: environment
    return next((l.split()[0] for l in out.splitlines() if "indite_mac.py" in l and "INDITE_TEST=1" in l), "")


def cmd(line: str) -> None:
    (DATA / "demo.cmd").write_text(line + "\n")


def evaluate(expr: str, wait: float = 10.0) -> str:
    out = DATA / "eval.out"
    out.unlink(missing_ok=True)
    cmd("eval:" + expr)
    end = time.time() + wait
    while time.time() < end:
        if out.exists() and out.stat().st_size:
            raw = out.read_text()
            try:
                got = json.loads(raw)                    # the window sends JSON.stringify(value), as a JSON string
                return json.loads(got) if isinstance(got, str) else got
            except json.JSONDecodeError:
                return {"error": raw.strip()[:500]}       # the expression threw: say what the page said
        time.sleep(0.2)
    raise SystemExit("no answer from the test copy (is it running? python mac/testcopy.py start)")


def start() -> None:
    if pid():
        print("already running, pid", pid())
        return
    DATA.mkdir(parents=True, exist_ok=True)
    prefs = DATA / "prefs.json"
    p = json.loads(prefs.read_text()) if prefs.exists() else {}
    prefs.write_text(json.dumps({**p, **PREFS}, indent=2))
    log = DATA / "indite.log"
    seen = log.stat().st_size if log.exists() else 0
    subprocess.run(["open", "-n", "-g", "--env", "INDITE_TEST=1", "--env", f"INDITE_DATA={DATA}", str(APP)], check=True)
    end = time.time() + 120
    while time.time() < end:                     # the engine takes ~10 s; a first start up to a minute
        if log.exists() and "resident engine:" in log.read_text(errors="replace")[seen:]:
            break
        time.sleep(0.5)
    print("test copy:", "ready" if pid() else "did not start - see", log, "pid", pid())


def stop() -> None:
    if not pid():
        print("not running")
        return
    cmd("quit")
    for _ in range(20):
        if not pid():
            print("stopped")
            return
        time.sleep(0.5)
    subprocess.run(["kill", pid()], check=False)
    print("stopped (killed)")


if __name__ == "__main__":
    verb, arg = (sys.argv[1:] + ["", ""])[:2]
    if verb == "start":
        start()
    elif verb == "stop":
        stop()
    elif verb == "js":
        cmd("js:" + arg)
    elif verb == "eval":
        if "\n" in arg:
            raise SystemExit("eval takes one line (demo.cmd reads one instruction per line)")
        print(json.dumps(evaluate(arg), indent=1)[:4000])
    elif verb == "cmd":
        cmd(arg)
    elif verb == "shot":
        (DATA / "snapshot.request").write_text(arg or "home")
        print("picture ->", DATA / f"snapshot-{arg or 'home'}.png")
    else:
        print(__doc__)
