"""
What indite remembers between launches: the dictations, and the few settings that change how it behaves.

Both live in one folder under Application Support, as plain text a person can read and delete. Nothing goes
anywhere else - the same promise the engine makes.

History is capped, because an unbounded log of everything a user has ever said is a liability, not a feature.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

DIR = Path.home() / "Library/Application Support/indite"
HISTORY = DIR / "history.jsonl"
PREFS = DIR / "prefs.json"
CAP = 500                       # roughly a month of heavy use; older lines are dropped on write

# Every one of these does something. Four times in this project a switch was shipped that silently did nothing,
# so the rule here is: a setting exists only if the code reads it.
DEFAULTS = {
    "hotkey": "alt_r",          # alt_r · alt_l · cmd_r · fn - rebound live, no restart
    "output": "smart",          # smart (type when there is a text box, else clipboard) · type · copy
    "spelling": True,           # the shared Hinglish spelling list
    "keep_history": True,       # off means nothing is written, and the list below empties
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
