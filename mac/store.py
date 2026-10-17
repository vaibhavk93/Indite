"""
What indite remembers between launches: the dictations, and the few settings that change how it behaves.

Both live in one folder under Application Support, as plain text a person can read and delete. Nothing goes
anywhere else - the same promise the engine makes.

History is capped, because an unbounded log of everything a user has ever said is a liability, not a feature.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

# INDITE_DATA points a second copy at another folder - used for the demo video, so a recording never shows a
# person's real notes.
DIR = Path(os.environ["INDITE_DATA"]) if os.environ.get("INDITE_DATA") else Path.home() / "Library/Application Support/indite"
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
    "hf_key": "",               # hands-free key; "" = the same key you hold to talk
    "hf_taps": 2,               # taps of that key that lock hands-free: 2 or 3
    "pill_clear": 60,           # pill transparency in %, steps of 10: 100 = clear glass only, 0 = a solid tint
    "ai": False,                # AI on notes; off until the person turns it on and picks where answers come from (answers come from your own Claude login)
    "ai_ok": False,
    "ai_ok_meetings": False,    # "Don't ask again" on the meeting/file → AI warning
    "ai_provider": "claude",    # claude · anthropic · openai · openrouter (keys live in the Keychain, not here)
    "ai_model": "",             # "" = the provider's default             # you said yes to text leaving the Mac for AI answers (asked once)
    "keep_audio": False,        # also keep each dictation's recording (about 0.3 MB for 10 s), for backups
    "backup_scope": "all",      # all · star · keep (starred + to-do)
    "backup_audio": False,      # include recordings and transcribed files in a backup
    "auto_speakers": True,      # find who spoke in every file and meeting, without a click
    "mask_swears": False,       # common swear words written as b**** (founder asked; off by default)
    "digits": True,             # number words as digits: "chaar baje" -> "4 baje"
    "setup_done": False,
    "asked_screen": False,      # the Screen & System Audio Recording prompt was shown once        # the first-run setup was finished (Help → Run setup again)
    "theme": "light",           # light · dark · system - the window's colours
    "preview": False,           # show what was written in a small card above the pill for a few seconds
}


def prefs() -> dict:
    out = dict(DEFAULTS)
    try:
        saved = json.loads(PREFS.read_text(encoding="utf-8"))
        if "pill_glass" in saved and "pill_clear" not in saved:       # the old 0-1 "glass" setting, as % clear
            saved["pill_clear"] = int(round((1 - float(saved["pill_glass"])) * 10) * 10)
        out.update(saved)
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


def keep(row: dict) -> bool:
    """Notes you have marked - a star, a to-do, a transcribed file - are kept until you delete them yourself.
    Only plain dictations are capped and cleared, so "Clear history" can never take a note you meant to keep."""
    return bool(row.get("star") or row.get("todo") or row.get("kind", "dictation") != "dictation")


def _read() -> list[dict]:
    out = []
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except Exception:   # noqa: BLE001 - a bad line is skipped, never a crash
                continue
            row.setdefault("id", repr(row.get("at", 0)))     # rows written before ids existed
            out.append(row)
    return out


def _write(rows: list[dict]) -> None:
    plain = [r for r in rows if not keep(r)]
    drop = {id(r) for r in plain[:-CAP]} if len(plain) > CAP else set()     # oldest plain dictations first
    rows = [r for r in rows if id(r) not in drop]
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(HISTORY)                                   # all or nothing: a crash mid-write loses no notes


def add(text: str, seconds: float, took: float, where: str, app: str, **extra) -> str | None:
    """One dictation, or a note (extra: kind, title, segments, source). Returns its id."""
    if not text or (not prefs()["keep_history"] and extra.get("kind", "dictation") == "dictation"):
        return None
    now = time.time()
    row = {"id": repr(now), "at": now, "text": text, "seconds": round(seconds, 1), "took": round(took, 2),
           "where": where, "app": app, **extra}
    _write(_read() + [row])
    return row["id"]


def update(note_id: str, **fields) -> None:
    """Star, to-do, title, improved text... only the fields given change. None removes a field."""
    rows = _read()
    for r in rows:
        if r["id"] == note_id:
            for k, v in fields.items():
                if v is None:
                    r.pop(k, None)
                else:
                    r[k] = v
    _write(rows)


def delete(note_id: str) -> dict | None:
    rows = _read()
    gone = next((r for r in rows if r["id"] == note_id), None)
    _write([r for r in rows if r["id"] != note_id])
    return gone


def restore(row: dict) -> None:
    """Undo a delete: the note goes back exactly as it was, in time order."""
    _write(sorted(_read() + [row], key=lambda r: r.get("at", 0)))


def history() -> list[dict]:
    """Newest first."""
    return _read()[::-1]


def clear() -> int:
    """Deletes plain dictations; starred, to-do and file notes stay. Returns how many were deleted."""
    rows = _read()
    kept = [r for r in rows if keep(r)]
    _write(kept)
    return len(rows) - len(kept)


# ---- backup and restore ----------------------------------------------------------------------------------------
# One zip: notes.jsonl, manifest.json (format version, when, what was chosen), audio/ when asked for. Restore adds
# notes that are not already here and never overwrites one that is, so restoring twice changes nothing.
AUDIO = DIR / "audio"
FORMAT = 1
SCOPES = {"all": "every note", "star": "starred notes", "keep": "starred notes and to-dos"}


def audio_of(row: dict) -> Path | None:
    """The sound behind a note: a kept dictation recording, or the file a note was transcribed from."""
    own = AUDIO / f"{row['id']}.wav"
    if own.exists():
        return own
    src = Path(row.get("source", "")) if row.get("kind") == "file" else None
    return src if src and src.is_file() else None


def audio_files(row: dict) -> list[Path]:
    """Every recording kept for a note: a meeting has two tracks (you, others), anything else at most one."""
    if row.get("kind") == "meeting":
        return [p for p in (AUDIO / f"{row['id']}-you.wav", AUDIO / f"{row['id']}-others.wav") if p.exists()]
    own = audio_of(row)
    return [own] if own else []


def backup(path: Path, scope: str = "all", with_audio: bool = False) -> int:
    import zipfile
    rows = [r for r in _read() if scope == "all" or (scope == "star" and r.get("star"))
            or (scope == "keep" and (r.get("star") or r.get("todo")))]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps({"app": "indite-mac", "format": FORMAT, "made": time.time(),
                                                "scope": scope, "audio": with_audio, "notes": len(rows)}))
        out = []
        for r in rows:
            r = dict(r)
            a = audio_of(r) if with_audio else None
            if a:
                r["backup_audio"] = f"audio/{r['id']}{a.suffix}"
                z.write(a, r["backup_audio"])
            out.append(r)
        z.writestr("notes.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    return len(rows)


def restore_zip(path: Path) -> int:
    """Returns how many notes were added. Refuses a backup from a newer indite rather than half-reading it."""
    import zipfile
    with zipfile.ZipFile(path) as z:
        meta = json.loads(z.read("manifest.json"))
        if meta.get("format", 0) > FORMAT:
            raise ValueError("This backup was made by a newer indite. Update indite, then restore it.")
        have = {r["id"] for r in _read()}
        new = []
        for line in z.read("notes.jsonl").decode("utf-8").splitlines():
            r = json.loads(line)
            if r["id"] in have:
                continue
            if r.get("backup_audio") and r["backup_audio"] in z.namelist():
                AUDIO.mkdir(parents=True, exist_ok=True)
                dest = AUDIO / f"{r['id']}{Path(r['backup_audio']).suffix}"
                dest.write_bytes(z.read(r["backup_audio"]))
                if r.get("kind") == "file":
                    r["source"] = str(dest)          # the original file may not exist on this Mac
            r.pop("backup_audio", None)
            new.append(r)
    if new:
        _write(sorted(_read() + new, key=lambda r: r.get("at", 0)))
    return len(new)


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
        # An apostrophe does not end a word: with the fix "don = Dawn", "don't go" became "Dawn't go" (15 Oct).
        # So a match must not sit either side of one - "don't", "it's", "y'all" are left alone. The cost: a
        # possessive is left alone too ("ptm's app" stays). Deliberate - a missed fix reads fine, "Dawn't" does not.
        text = re.sub(rf"(?<!\w)(?<!['’]){words}(?!\w)(?!['’]\w)",
                      lambda _m, w=want: w, text, flags=re.IGNORECASE)
    return text


MAX_FIX_WORDS = 6          # a whole sentence is not a word fix; it would match almost nothing and cost every pass
MAX_FIX_CHARS = 80
MAX_FIXES = 500            # the list is applied to every dictation: past this it is a speed problem, not a feature


def fix_problem(heard: str, want: str) -> str:
    """
    Why this fix cannot be added, in a sentence a person can act on - or "" if it is fine.

    The list runs over every dictation, every file and every meeting, so a bad entry is not a bad row in a table: it
    is a wrong word in everything typed from now on. Checked here, in one place, because the window, the note row and
    anything that later adds fixes by itself must all obey the same rules (roadmap Mac 6).
    """
    heard, want = " ".join(heard.split()), " ".join(want.split())
    if not heard or not want:
        return "Both boxes need something in them."
    if "=" in heard or heard.startswith("#"):
        return "A fix cannot contain = or start with #, because that is how the list is written down."
    if heard.lower() == want.lower():
        return "Those are the same word."
    if len(heard) > MAX_FIX_CHARS or len(want) > MAX_FIX_CHARS:
        return f"Keep each side under {MAX_FIX_CHARS} characters - this is for words, not sentences."
    if len(heard.split()) > MAX_FIX_WORDS:
        return f"That is {len(heard.split())} words. A fix matches up to {MAX_FIX_WORDS}."
    if len(heard) < 2:
        return "One letter would match far too much."
    pairs = my_fixes()
    for h, w in pairs:
        if h.lower() == heard.lower():
            return f"Already there: {h} → {w}. Remove it first if you want to change it."
    if len(pairs) >= MAX_FIXES:
        return f"The list is full ({MAX_FIXES}). Remove something you no longer need."
    return ""


def add_fix(heard: str, want: str) -> bool:
    """Appends one fix from the window. Refuses anything fix_problem objects to."""
    heard, want = " ".join(heard.split()), " ".join(want.split())
    if fix_problem(heard, want):
        return False
    path = fixes_file()
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw + ("" if raw.endswith("\n") else "\n") + f"{heard} = {want}\n", encoding="utf-8")
    return True


def remove_fix(heard: str) -> None:
    """Drops every line that fixes this word; comments and other fixes stay exactly as they were."""
    path = fixes_file()
    keep = [l for l in path.read_text(encoding="utf-8").splitlines()
            if not (l.partition("=")[1] and " ".join(l.partition("=")[0].split()).lower() == heard.lower())]
    path.write_text("\n".join(keep) + "\n", encoding="utf-8")


def my_fixes() -> list[tuple[str, str]]:
    try:
        return parse_fixes(MY_FIXES.read_text(encoding="utf-8"))
    except Exception:           # noqa: BLE001 - no file, or half-saved: no fixes, never a failed dictation
        return []


# Clear-cut swear words only, in their common Roman spellings. Words with an everyday meaning ("saala" =
# brother-in-law, "kamina", "hell") are left out on purpose: masking them would damage normal sentences.
# ponytail: a fixed list misses new spellings; let people add their own if they ask.
SWEARS = ("fuck fucking fucked fucker motherfucker shit bullshit bitch bastard asshole dick cunt "
          "chutiya chutiye chutiyapa chut bhenchod behenchod bhenchodd benchod bc madarchod maderchod mc "
          "bhosdike bhosdi bhosadike gandu gaandu lauda lavda lund randi harami haramkhor bhadwa").split()
_SWEAR_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, SWEARS), key=len, reverse=True)) + r")\b", re.I)


def mask_swears(text: str) -> str:
    """"chutiya" -> "c******": the first letter stays, so the sentence still reads."""
    return _SWEAR_RE.sub(lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1), text)


def masked(row: dict) -> dict:
    """
    A copy of a note for showing, with swears masked. The note on disk keeps the real words (R5: nothing is deleted
    silently) - masking is only ever applied where text is shown, typed, copied or exported.
    """
    r = dict(row)
    for k in ("text", "improved"):
        if r.get(k):
            r[k] = mask_swears(r[k])
    if r.get("segments"):
        r["segments"] = [{**s, "text": mask_swears(s.get("text", ""))} for s in r["segments"]]
    if r.get("ai"):
        r["ai"] = [{**a, "text": mask_swears(a.get("text", ""))} if isinstance(a, dict) else a for a in r["ai"]]
    return r


if __name__ == "__main__":     # the one check: uv run python mac/store.py
    assert fix_problem("", "Paytm")
    assert fix_problem("ptm", "ptm")                                  # same word
    assert fix_problem("a", "Paytm")                                  # one letter matches everything
    assert fix_problem("one two three four five six seven", "x")      # too many words
    assert fix_problem("x" * 90, "y")                                 # too long
    assert not fix_problem("pay tm", "Paytm")                         # a normal two-word fix is fine
    assert mask_swears("Yeh BC kya hai, chutiya mat bana") == "Yeh B* kya hai, c****** mat bana"
    assert mask_swears("saala hell dickens bcc") == "saala hell dickens bcc"          # everyday words untouched
    note = {"text": "chutiya", "segments": [{"speaker": "You", "text": "bc yaar"}], "ai": [{"text": "shit"}]}
    shown = masked(note)
    assert (shown["text"], shown["segments"][0]["text"], shown["ai"][0]["text"]) == ("c******", "b* yaar", "s***")
    assert note["text"] == "chutiya" and note["segments"][0]["text"] == "bc yaar"    # the stored note is untouched
    pairs = parse_fixes(FIXES_HEADER + "ptm = Paytm\npay tm = Paytm\n  c++  = C++\nbroken line\n= nothing\n")
    assert pairs == [("pay tm", "Paytm"), ("ptm", "Paytm"), ("c++", "C++")], pairs
    assert apply_my_fixes("PTM se pay  tm karo", pairs) == "Paytm se Paytm karo"
    assert apply_my_fixes("don't go", [("don", "Dawn")]) == "don't go"      # an apostrophe does not end a word
    assert apply_my_fixes("don ko bulao", [("don", "Dawn")]) == "Dawn ko bulao"
    assert apply_my_fixes("aptm wala", pairs) == "aptm wala"          # inside a word: left alone
    assert apply_my_fixes("c++ seekho", pairs) == "C++ seekho"
    assert apply_my_fixes("addr1", [("addr1", r"12 \1 Road")]) == r"12 \1 Road"   # replacement taken literally
    assert parse_fixes("a = b\n" + "pay tm = Paytm\n")[0] == ("pay tm", "Paytm")
    import tempfile
    HISTORY = Path(tempfile.mkdtemp()) / "h.jsonl"         # the notes rules, on a scratch file
    DIR = HISTORY.parent
    a = add("one", 1, 1, "done", "")
    b = add("two", 1, 1, "done", "", kind="file", title="call.m4a")
    update(a, star=True)
    assert [r["text"] for r in history()] == ["two", "one"] and history()[1]["star"]
    gone = delete(a); assert len(history()) == 1; restore(gone); assert len(history()) == 2
    update(a, star=None); assert clear() == 1 and [r["text"] for r in history()] == ["two"]   # file note kept
    c = add("three", 1, 1, "done", ""); update(c, star=True)
    AUDIO = DIR / "audio"; AUDIO.mkdir(); (AUDIO / f"{c}.wav").write_bytes(b"RIFF")
    z = DIR / "b.zip"
    assert backup(z, "star", with_audio=True) == 1
    assert restore_zip(z) == 0                                # already here: nothing added, nothing changed
    delete(c); (AUDIO / f"{c}.wav").unlink()
    assert restore_zip(z) == 1 and (AUDIO / f"{c}.wav").read_bytes() == b"RIFF" and history()[0]["star"]
    print("ok")
