"""
What indite remembers between launches: the dictations, and the few settings that change how it behaves.

Both live in one folder under Application Support, as plain text a person can read and delete. Nothing goes
anywhere else - the same promise the engine makes.

History is capped, because an unbounded log of everything a user has ever said is a liability, not a feature.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

DIR = Path.home() / "Library/Application Support/indite"
HISTORY = DIR / "history.jsonl"
PREFS = DIR / "prefs.json"
MY_FIXES = DIR / "my_fixes.txt"
CAP = 500                       # roughly a month of heavy use; older lines are dropped on write

# Every one of these does something. Four times in this project a switch was shipped that silently did nothing,
# so the rule here is: a setting exists only if the code reads it.
DEFAULTS = {
    "hotkey": "alt_r",          # alt_r · alt_l · cmd_r · fn - rebound live, no restart
    "output": "smart",          # smart (type when there is a text box, else clipboard) · type · copy
    "spelling": True,           # the shared Hinglish spelling list
    "keep_history": True,       # off means nothing is written, and the list below empties
    "sounds": True,             # a soft tick when listening starts, a pop when it stops
    "mic": "",                  # a microphone's name; "" = automatic (default, then built-in, then any)
}


def prefs() -> dict:
    out = dict(DEFAULTS)
    try:
        out.update(json.loads(PREFS.read_text(encoding="utf-8")))
    except Exception:           # noqa: BLE001 - a missing or half-written file must not stop the app
        pass
    return {k: out.get(k, v) for k, v in DEFAULTS.items()}      # unknown keys from an older build are dropped


def set_pref(key: str, value) -> dict:
    if key not in DEFAULTS:
        return prefs()
    p = prefs()
    p[key] = value
    DIR.mkdir(parents=True, exist_ok=True)
    PREFS.write_text(json.dumps(p, indent=2), encoding="utf-8")
    return p


def add(text: str, seconds: float, took: float, where: str, app: str) -> None:
    if not prefs()["keep_history"] or not text:
        return
    DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"at": time.time(), "text": text, "seconds": round(seconds, 1),
                       "took": round(took, 2), "where": where, "app": app})
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    rows = HISTORY.read_text(encoding="utf-8").splitlines()
    if len(rows) > CAP:
        HISTORY.write_text("\n".join(rows[-CAP:]) + "\n", encoding="utf-8")


def history() -> list[dict]:
    """Newest first, bad lines skipped rather than crashing the window."""
    out = []
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except Exception:   # noqa: BLE001
                continue
    return out[::-1]


def clear() -> None:
    HISTORY.unlink(missing_ok=True)


# ---- your own word fixes ---------------------------------------------------------------------------------------
# One per line, "what it writes = what you want". Read on every dictation, so a saved edit works on the next one.
# "=" and not a tab, because the person editing this is in TextEdit, where a tab and spaces look the same.
FIXES_HEADER = """# indite: your word fixes. One per line:   what indite writes = what you want
# Matches whole words, any capitals. Save the file; the next dictation uses it. Lines starting with # are ignored.
# Examples (delete the # to use one):
# ptm = Paytm
# pay tm = Paytm
# addr1 = 12 MG Road, Bengaluru 560001
"""


def fixes_file() -> Path:
    if not MY_FIXES.exists():
        DIR.mkdir(parents=True, exist_ok=True)
        MY_FIXES.write_text(FIXES_HEADER, encoding="utf-8")
    return MY_FIXES


def parse_fixes(raw: str) -> list[tuple[str, str]]:
    out = []
    for line in raw.splitlines():
        heard, sep, want = line.partition("=")
        heard, want = " ".join(heard.split()), want.strip()
        if sep and heard and want and not heard.startswith("#"):
            out.append((heard, want))
    return sorted(out, key=lambda p: -len(p[0]))     # "pay tm" before "pay", so the longer fix wins


def apply_my_fixes(text: str, pairs: list[tuple[str, str]]) -> str:
    for heard, want in pairs:
        words = r"\s+".join(re.escape(w) for w in heard.split())
        text = re.sub(rf"(?<!\w){words}(?!\w)", lambda _m, w=want: w, text, flags=re.IGNORECASE)
    return text


def add_fix(heard: str, want: str) -> bool:
    """Appends one fix from the window. Refuses anything that would not read back as that same fix."""
    heard, want = " ".join(heard.split()), " ".join(want.split())
    if not heard or not want or "=" in heard or heard.startswith("#") or heard.lower() == want.lower():
        return False
    path = fixes_file()
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw + ("" if raw.endswith("\n") else "\n") + f"{heard} = {want}\n", encoding="utf-8")
    return True


def my_fixes() -> list[tuple[str, str]]:
    try:
        return parse_fixes(MY_FIXES.read_text(encoding="utf-8"))
    except Exception:           # noqa: BLE001 - no file, or half-saved: no fixes, never a failed dictation
        return []


if __name__ == "__main__":     # the one check: uv run python mac/store.py
    pairs = parse_fixes(FIXES_HEADER + "ptm = Paytm\npay tm = Paytm\n  c++  = C++\nbroken line\n= nothing\n")
    assert pairs == [("pay tm", "Paytm"), ("ptm", "Paytm"), ("c++", "C++")], pairs
    assert apply_my_fixes("PTM se pay  tm karo", pairs) == "Paytm se Paytm karo"
    assert apply_my_fixes("aptm wala", pairs) == "aptm wala"          # inside a word: left alone
    assert apply_my_fixes("c++ seekho", pairs) == "C++ seekho"
    assert apply_my_fixes("addr1", [("addr1", r"12 \1 Road")]) == r"12 \1 Road"   # replacement taken literally
    assert parse_fixes("a = b\n" + "pay tm = Paytm\n")[0] == ("pay tm", "Paytm")
    print("ok")
