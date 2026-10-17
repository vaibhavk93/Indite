"""
What indite remembers between launches: the dictations, and the few settings that change how it behaves.

Both live in one folder under Application Support, as plain text a person can read and delete. Nothing goes
anywhere else - the same promise the engine makes.

History is capped, because an unbounded log of everything a user has ever said is a liability, not a feature.
"""

from __future__ import annotations

import json
import os
import functools
import re
import time
from pathlib import Path

# INDITE_DATA points a second copy at another folder - used for the demo video, so a recording never shows a
# person's real notes.
DIR = Path(os.environ["INDITE_DATA"]) if os.environ.get("INDITE_DATA") else Path.home() / "Library/Application Support/indite"
# INDITE_TEST=1: the hidden test copy (mac/testcopy.py, founder rule 17 Oct "never test on my screen"). It has its own
# data folder and engine, and never listens to keys, opens the mic, types, copies, shows a pill / card / menu icon, or
# comes to the front. Refuses to run on the real data folder.
TEST = os.environ.get("INDITE_TEST") == "1"
if TEST and not os.environ.get("INDITE_DATA"):
    raise SystemExit("INDITE_TEST needs its own INDITE_DATA folder")
HISTORY = DIR / "history.jsonl"
PREFS = DIR / "prefs.json"
MY_FIXES = DIR / "my_fixes.txt"
CAP = 500                       # roughly a month of heavy use; older lines are dropped on write

# Every one of these does something. Four times in this project a switch was shipped that silently did nothing,
# so the rule here is: a setting exists only if the code reads it.
DEFAULTS = {
    "hotkey": "alt_r",          # alt_r · alt_l · cmd_r · fn - rebound live, no restart
    "output": "smart",          # smart (type when there is a text box, else clipboard) · type · copy
    "review": False,            # mark likely mistakes after a dictation (being tested: on for the founder, off for others)
    "also_copy": True,          # typed words ALSO go on the clipboard, and so does every AI answer (founder, 17 Oct)
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
    "ai_uses": {},              # "action|extra" -> times asked; picks the text card's two AI buttons
    "card_buttons": ["", ""],   # the text card's 2nd and 3rd buttons: "action|extra" you picked, or "" = your most used
    "mask_swears": False,       # common swear words written as b**** (founder asked; off by default)
    "my_swears": [],            # your own extra words to hide the same way
    "ai_secs": [],              # how long the last 30 AI answers took (Ask AI shows the typical wait)
    "speech_test": False,       # Dictations: "This is exactly what I said" + a To check filter (mac/speechset.py)
    "ask_calls": True,          # a call app starts using the mic: the card asks "Record this call?" (never records itself)
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
            if ("text" in fields or "segments" in fields) and "wt" not in fields and r.get("wt") and not wt_fits(r):
                r.pop("wt")                  # a fix or edit changed the words: the Listen view lines them up again
    _write(rows)


def track_of(seg: dict, meet: bool = True) -> int:
    """Which of a meeting's audio files a line was heard on: 0 = you, 1 = the others. Lines saved before 17 Oct
    have no "k" and are placed by speaker; a line whose speaker you changed keeps its own track."""
    return int(seg["k"]) if "k" in seg else int(meet and seg.get("speaker") != "You")


def set_speaker(row: dict, start: float, speaker: str, new: str) -> bool:
    """One line gets another speaker ("Rohit" -> "You"); it keeps its track and word times."""
    segs = [dict(s) for s in row.get("segments") or []]
    meet = row.get("kind") == "meeting"
    for s in segs:
        if abs(float(s.get("start", 0)) - float(start)) < 0.01 and (s.get("speaker") or "") == (speaker or ""):
            s["k"], s["speaker"] = track_of(s, meet), new
            update(row["id"], segments=segs, text=text_of(segs), edited=True)
            return True
    return False


def merge_next(row: dict, start: float, speaker: str) -> bool:
    """Joins a line with the next line of the same speaker on the same track (Who spoke cut one turn in two)."""
    segs = [dict(s) for s in row.get("segments") or []]
    meet = row.get("kind") == "meeting"
    i = next((i for i, s in enumerate(segs) if abs(float(s.get("start", 0)) - float(start)) < 0.01
              and (s.get("speaker") or "") == (speaker or "")), None)
    if i is None:
        return False
    a = segs[i]
    j = next((j for j in range(i + 1, len(segs)) if track_of(segs[j], meet) == track_of(a, meet)), None)
    if j is None or (segs[j].get("speaker") or "") != (speaker or ""):
        return False
    b = segs.pop(j)
    a.update(text=f"{a['text']} {b['text']}", end=b.get("end", a.get("end")), k=track_of(a, meet))
    wt = [dict(w) for w in row.get("wt") or []]
    wa = next((w for w in wt if abs(w["s"] - float(a["start"])) < 0.01 and w["k"] == a["k"]), None)
    wb = next((w for w in wt if abs(w["s"] - float(b["start"])) < 0.01 and w["k"] == a["k"]), None)
    if wa and wb:                                        # the joined line keeps both lines' word times
        wa["t"] = wa["t"] + wb["t"]
        wt.remove(wb)
    update(row["id"], segments=segs, text=text_of(segs), edited=True, **({"wt": wt} if wa and wb else {}))
    return True


def wt_fits(row: dict) -> bool:
    """Each line's word times ("wt") still have one time per shown word (the Listen view needs exactly that)."""
    segs, meet = row.get("segments") or [], row.get("kind") == "meeting"
    for w in row.get("wt") or []:
        if segs:
            line = next((x for x in segs if abs(float(x.get("start", 0)) - w["s"]) < 0.01
                         and (not meet or track_of(x, meet) == w["k"])), None)
            if not line:
                return False
            text = line["text"]
        else:
            text = row.get("text", "")
        if len(text.split()) != len(w["t"]) or (len(w["t"]) > 2 and len(set(w["t"])) == 1):
            return False             # wrong count, or every word at one time: the engine heard nothing that time
    return True


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


FIXLOG = DIR / "fixlog.jsonl"    # every Fix / Always fix / Not a mistake on a flagged word: the proof the review helps


def log_fix(heard: str, want: str, how: str) -> int:
    """Notes one decision on a flag; returns how many times this same fix has been made before (for "Always fix?")."""
    seen = 0
    if FIXLOG.exists():
        for line in FIXLOG.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            seen += e["heard"].lower() == heard.lower() and e["want"] == want and e["how"] != "dismiss"
    with FIXLOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": time.time(), "heard": heard, "want": want, "how": how}, ensure_ascii=False) + "\n")
    return seen


def fix_counts() -> dict:
    """How the flagged words were decided: the proof AI review helps (roadmap Mac next #4)."""
    out = {"fix": 0, "always": 0, "dismiss": 0}
    if FIXLOG.exists():
        for line in FIXLOG.read_text(encoding="utf-8").splitlines():
            how = json.loads(line).get("how")
            if how in out:
                out[how] += 1
    return out


def text_of(segments: list[dict]) -> str:
    """A note's text from its timed lines, the way meetings and files write it: "Speaker: words" per line, else paragraphs."""
    if any(s.get("speaker") for s in segments):
        return "\n".join(f"{s.get('speaker', '')}: {s['text']}" for s in segments)
    return "\n\n".join(s["text"] for s in segments)


def edit_line(row: dict, start: float, speaker: str, text: str) -> str | None:
    """
    Changes one timed line and the note's text with it; returns the old words for Undo, or None if no line matched.
    The line is found by its start time and speaker, never by position: Who spoke rebuilds the list.
    """
    segs = [dict(s) for s in row.get("segments") or []]
    for s in segs:
        if abs(float(s.get("start", 0)) - float(start)) < 0.01 and (s.get("speaker") or "") == (speaker or ""):
            old, s["text"] = s["text"], text
            wt = [dict(w) for w in row.get("wt") or []]
            for w in wt:                                  # keep the word times: re-match just this line's words
                if abs(w["s"] - float(start)) < 0.01 and w["k"] == track_of(s, row.get("kind") == "meeting") \
                        and len(w["t"]) == len(old.split()):     # this line's own track, not a line at the same moment
                    import wordtimes
                    w["t"] = wordtimes.align([text.split()], list(zip(old.split(), w["t"], w["t"])), [w["s"]])[0]
            update(row["id"], segments=segs, text=text_of(segs), edited=True, **({"wt": wt} if wt else {}))
            return old
    return None


def named_segments(row: dict) -> list[dict]:
    """A meeting's lines with the speakers' names as renamed by the user ("Person 1" -> "Rohit")."""
    names = row.get("names") or {}
    return [{**s, "speaker": names.get(s.get("speaker"), s.get("speaker"))} for s in row.get("segments") or []]


def named_text(row: dict) -> str:
    """What the note shows: for a meeting, its lines with the renamed speakers - copied and exported the same way."""
    segs = named_segments(row)
    return "\n".join(f"{s['speaker']}: {s['text']}" for s in segs) if segs else row.get("text", "")


def audio_files(row: dict) -> list[Path]:
    """Every recording kept for a note: a meeting has two tracks (you, others), anything else at most one."""
    if row.get("kind") == "meeting":
        return [p for p in (AUDIO / f"{row['id']}-you.wav", AUDIO / f"{row['id']}-others.wav") if p.exists()]
    own = audio_of(row)
    return [own] if own else []


def drop_orphan_audio(older_than: float = 3600.0) -> int:
    """
    Recordings of notes that are gone (deleted, cleared, or past the 500 kept) are removed - at start-up, so Undo
    still had them (17 Oct: nothing ever removed them, so meetings kept other people's voices after Delete).
    Never runs on an empty or unreadable history, and leaves anything touched in the last hour.
    """
    try:
        ids = {r["id"] for r in _read()}
    except Exception:                                    # noqa: BLE001 - an unreadable history must never cost audio
        return 0
    if not ids or not AUDIO.exists():
        return 0
    gone = 0
    for f in AUDIO.iterdir():
        note = re.match(r"^(\d+\.\d+)(?:-you|-others)?\.\w+$", f.name)
        if note and note.group(1) not in ids and time.time() - f.stat().st_mtime > older_than:
            f.unlink()
            gone += 1
    return gone


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
            if with_audio and r.get("kind") == "meeting":   # both tracks (17 Oct: meetings had none in backups)
                r["backup_tracks"] = [f"audio/{f.name}" for f in audio_files(r)]
                for f in audio_files(r):
                    z.write(f, f"audio/{f.name}")
            a = audio_of(r) if with_audio and r.get("kind") != "meeting" else None
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
            for name in r.pop("backup_tracks", []):            # a meeting's you / others tracks
                if name in z.namelist() and "/" not in name[len("audio/"):]:
                    AUDIO.mkdir(parents=True, exist_ok=True)
                    (AUDIO / Path(name).name).write_bytes(z.read(name))
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


def fix_problem(heard: str, want: str, editing: bool = False) -> str:
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
        return f"Keep each side under {MAX_FIX_CHARS} characters. This is for words, not sentences."
    if len(heard.split()) > MAX_FIX_WORDS:
        return f"That is {len(heard.split())} words. A fix matches up to {MAX_FIX_WORDS}."
    if len(heard) < 2:
        return "One letter would match far too much."
    pairs = my_fixes()
    for h, w in pairs:
        if h.lower() == heard.lower() and not editing:   # automatic paths never overwrite a word you set
            return f"Already there: {h} → {w}. Remove it first if you want to change it."
    if len(pairs) >= MAX_FIXES:
        return f"The list is full ({MAX_FIXES}). Remove something you no longer need."
    return ""


def add_fix(heard: str, want: str, replace: bool = False) -> bool:
    """Appends one fix from the window. Refuses anything fix_problem objects to. replace: the Dictionary page's Add,
    where the same word again is an edit (one line per word)."""
    heard, want = " ".join(heard.split()), " ".join(want.split())
    if fix_problem(heard, want, editing=replace):
        return False
    if replace:
        remove_fix(heard)
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
# A fixed list misses new spellings: people add their own in Settings ("my_swears").
SWEARS = ("fuck fucking fucked fucker motherfucker shit bullshit bitch bastard asshole dick cunt "
          "chutiya chutiye chutiyapa chut bhenchod behenchod bhenchodd benchod bc madarchod maderchod mc "
          "bhosdike bhosdi bhosadike gandu gaandu lauda lavda lund randi harami haramkhor bhadwa").split()
@functools.lru_cache(maxsize=4)
def _swear_re(mine: tuple = ()) -> re.Pattern:
    words = {w.strip().lower() for w in SWEARS + list(mine) if w.strip()}
    return re.compile(r"\b(" + "|".join(sorted(map(re.escape, words), key=len, reverse=True)) + r")\b", re.I)


def mask_swears(text: str, mine=()) -> str:
    """"chutiya" -> "c******": the first letter stays, so the sentence still reads. mine: your own extra words."""
    return _swear_re(tuple(mine or ())).sub(lambda m: m.group(0)[0] + "*" * (len(m.group(0)) - 1), text)


def masked(row: dict, mine=()) -> dict:
    """
    A copy of a note for showing, with swears masked. The note on disk keeps the real words (R5: nothing is deleted
    silently) - masking is only ever applied where text is shown, typed, copied or exported.
    """
    r = dict(row, real_text=row.get("text", ""))      # edit boxes get the real words: saving stars over them lost them
    for k in ("text", "improved"):
        if r.get(k):
            r[k] = mask_swears(r[k], mine)
    if r.get("segments"):
        r["segments"] = [{**s, "text": mask_swears(s.get("text", ""), mine), "real": s.get("text", "")} for s in r["segments"]]
    if r.get("ai"):
        r["ai"] = [{**a, "text": mask_swears(a.get("text", ""), mine)} if isinstance(a, dict) else a for a in r["ai"]]
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
    assert mask_swears("Kya bakwaas hai, BC", ["bakwaas", " "]) == "Kya b****** hai, B*"   # your own words too
    assert mask_swears("bakwaas") == "bakwaas"                                          # only when you added it
    assert text_of([{"speaker": "You", "text": "a"}, {"speaker": "Others", "text": "b"}]) == "You: a\nOthers: b"
    assert text_of([{"text": "a"}, {"text": "b"}]) == "a\n\nb"
    import tempfile
    HISTORY = Path(tempfile.mkdtemp()) / "h.jsonl"
    HISTORY.write_text(json.dumps({"id": "f1", "text": "kal aana", "segments": [{"start": 2.0, "end": 4.0, "text": "kal aana"}],
                                   "wt": [{"s": 2.0, "k": 0, "t": [2.1, 2.6]}]}) + "\n")
    assert edit_line(history()[0], 2.0, "", "kal zaroor aana") == "kal aana"
    r = history()[0]
    assert r["text"] == "kal zaroor aana" and len(r["wt"][0]["t"]) == 3                 # word times kept for the new words
    update(r["id"], star=True)
    assert history()[0].get("wt")                                                       # a star leaves the times alone
    update(r["id"], segments=[{**r["segments"][0], "text": "kal Crocin le aana"}])
    assert "wt" not in history()[0]                                                     # a fix changed the words: redone
    assert not wt_fits({"text": "a b c", "wt": [{"s": 0, "k": 0, "t": [0.0, 0.0, 0.0]}]})       # nothing matched
    assert wt_fits({"text": "a b c", "wt": [{"s": 0, "k": 0, "t": [0.0, 0.4, 0.9]}]})
    HISTORY.write_text(json.dumps({"id": "m", "at": 2, "kind": "meeting", "text": "", "segments": [
        {"start": 0.0, "end": 2.0, "speaker": "Person 1", "text": "haan deck"},
        {"start": 1.0, "end": 3.0, "speaker": "You", "text": "theek"},
        {"start": 2.0, "end": 4.0, "speaker": "Person 1", "text": "bhej dena"}],
        "wt": [{"s": 0.0, "k": 1, "t": [0.1, 0.6]}, {"s": 2.0, "k": 1, "t": [2.1, 2.5]}]}) + "\n")
    assert merge_next(history()[0], 0.0, "Person 1")             # "You" sits between, on the other track: still joins
    m = history()[0]
    assert [x["text"] for x in m["segments"]] == ["haan deck bhej dena", "theek"] and m["segments"][0]["end"] == 4.0
    assert m["wt"] == [{"s": 0.0, "k": 1, "t": [0.1, 0.6, 2.1, 2.5]}] and wt_fits(m)
    assert not merge_next(m, 1.0, "You")                          # nothing after it on its track
    assert set_speaker(m, 0.0, "Person 1", "You")
    m = history()[0]
    assert m["segments"][0]["speaker"] == "You" and track_of(m["segments"][0]) == 1   # still plays from the others
    assert m["text"].startswith("You: haan deck") and wt_fits(m)
    meet = {"text": "Person 1: haan", "names": {"Person 1": "Rohit"},
            "segments": [{"speaker": "Person 1", "text": "haan"}, {"speaker": "You", "text": "theek hai"}]}
    assert named_text(meet) == "Rohit: haan\nYou: theek hai" and named_text({"text": "plain"}) == "plain"
    note = {"text": "chutiya", "segments": [{"speaker": "You", "text": "bc yaar"}], "ai": [{"text": "shit"}]}
    shown = masked(note)
    assert (shown["text"], shown["segments"][0]["text"], shown["ai"][0]["text"]) == ("c******", "b* yaar", "s***")
    assert note["text"] == "chutiya" and note["segments"][0]["text"] == "bc yaar"    # the stored note is untouched
    assert shown["real_text"] == "chutiya" and shown["segments"][0]["real"] == "bc yaar"   # what an edit box starts from
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
    mt = add("call", 1, 1, "done", "", kind="meeting"); update(mt, star=True)
    for t in ("you", "others"):
        (AUDIO / f"{mt}-{t}.wav").write_bytes(t.encode())
    assert backup(z, "star", with_audio=True) == 2
    delete(mt)
    for t in ("you", "others"):
        (AUDIO / f"{mt}-{t}.wav").unlink()
    assert restore_zip(z) == 1 and (AUDIO / f"{mt}-others.wav").read_bytes() == b"others"   # both tracks come back
    (AUDIO / "1700000000.5-you.wav").write_bytes(b"x"); (AUDIO / "notes.txt").write_bytes(b"x")
    assert drop_orphan_audio(older_than=0) == 1                      # a deleted note's track goes; nothing else
    assert (AUDIO / f"{mt}-you.wav").exists() and (AUDIO / "notes.txt").exists()
    print("ok")
