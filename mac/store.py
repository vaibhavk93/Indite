"""
What Inditeflow remembers between launches: the dictations, and the few settings that change how it behaves.

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

# INDITEFLOW_DATA points a second copy at another folder - used for the demo video, so a recording never shows a
# person's real notes.
def _data_dir() -> Path:
    """The data folder. The app was called indite until 24 Oct: its folder is moved to the new name once (a rename inside
    one disk, instant), and the old name is left as a link to it, so the old build still works if the rename is undone."""
    if os.environ.get("INDITEFLOW_DATA"):
        return Path(os.environ["INDITEFLOW_DATA"])
    base = Path.home() / "Library/Application Support"
    new, old = base / "inditeflow", base / "indite"
    if not new.exists() and old.is_dir() and not old.is_symlink():
        try:
            old.rename(new)
            old.symlink_to(new)
        except OSError:                          # could not move it: keep working on the old folder, lose nothing
            return old
    return new


DIR = _data_dir()
# INDITEFLOW_TEST=1: the hidden test copy (mac/testcopy.py, founder rule 17 Oct "never test on my screen"). It has its own
# data folder and engine, and never listens to keys, opens the mic, types, copies, shows a pill / card / menu icon, or
# comes to the front. Refuses to run on the real data folder.
TEST = os.environ.get("INDITEFLOW_TEST") == "1"
if TEST and not os.environ.get("INDITEFLOW_DATA"):
    raise SystemExit("INDITEFLOW_TEST needs its own INDITEFLOW_DATA folder")
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
    "claude_model": "",         # the Claude login's model: haiku / sonnet / opus / an id; "" = whatever the account uses
    "ai_effort": "",            # low / medium / high / xhigh / max for the Claude login and Anthropic key; "" = the model's default
    "cost_currency": "USD",     # AI costs are shown in "USD" or "INR"
    "usd_inr": 0,               # rupees per US dollar, typed by you (Inditeflow does not look rates up); 0 = not set
    "views": {},                # per list page: {"home": {"filter": "star", "sort": "old"}, ...}; the search text is never kept
    "history_cap": 500,         # plain dictations to keep: 500 (default), 5000 or 0 = everything. Stars, to-dos, meetings, files: always kept
    "keep_audio": False,        # also keep each dictation's recording (about 0.3 MB for 10 s), for backups
    "backup_scope": "all",      # all · star · keep (starred + to-do)
    "backup_audio": False,      # include recordings and transcribed files in a backup
    "auto_speakers": True,      # find who spoke in every file and meeting, without a click
    "ai_uses": {},              # "action|extra" -> times asked; picks the text card's two AI buttons
    "card_buttons": ["", ""],   # the text card's 2nd and 3rd buttons: "action|extra" you picked, or "" = your most used
    "mask_swears": False,       # common swear words written as b**** (founder asked; off by default)
    "my_swears": [],            # your own extra words to hide the same way
    "ai_secs": [],              # how long the last 30 AI answers took (Ask AI shows the typical wait)
    "ai_review": False,         # Ask AI → "Review with AI" (step 2, being tested: ships to others only at >= 70% right)
    "speech_test": False,       # Dictations: "This is exactly what I said" + a To check filter (mac/speechset.py)
    "ask_calls": True,          # a call app starts using the mic: the card asks "Record this call?" (never records itself)
    "digits": True,             # number words as digits: "chaar baje" -> "4 baje"
    "setup_done": False,
    "asked_screen": False,      # the Screen & System Audio Recording prompt was shown once        # the first-run setup was finished (Help → Run setup again)
    "theme": "light",           # light · dark · system - the window's colours
    "preview": False,           # show what was written in a small card above the pill for a few seconds
    "card_ai": True,            # the text card shows the AI buttons (Ask AI + two more); off = To do only
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
    if key == "history_cap":
        apply_cap()                      # a smaller limit takes effect now, not at the next dictation (24 Oct)
    return p


def keep(row: dict) -> bool:
    """Notes you have marked - a star, a to-do, a transcribed file - are kept until you delete them yourself.
    Only plain dictations are capped and cleared, so "Clear history" can never take a note you meant to keep."""
    return bool(row.get("star") or row.get("todo") or row.get("kind", "dictation") != "dictation")


_cache = {"sig": None, "rows": []}     # the parsed history, reused until the file changes (25,000 notes took 175 ms to parse)


def _sig():
    try:
        st = HISTORY.stat()
        return (str(HISTORY), st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _rows() -> list[dict]:
    """The parsed rows, shared: callers must not change them (use _read() for a list you may edit)."""
    sig = _sig()
    if sig is None or sig != _cache["sig"]:
        out = []
        if HISTORY.exists():
            for line in HISTORY.read_text(encoding="utf-8").splitlines():
                try:
                    row = json.loads(line)
                except Exception:   # noqa: BLE001 - a bad line is skipped, never a crash
                    continue
                row.setdefault("id", repr(row.get("at", 0)))     # rows written before ids existed
                out.append(row)
        _cache["sig"], _cache["rows"] = sig, out
    return _cache["rows"]


def _read() -> list[dict]:
    return [dict(r) for r in _rows()]


def cap() -> int:
    """How many plain dictations to keep (pref "history_cap"); 0 = everything. Starred, to-do, meeting and file notes
    are never counted."""
    c = prefs().get("history_cap", CAP)
    return c if isinstance(c, int) and c >= 0 else CAP


def _write(rows: list[dict]) -> None:
    plain, limit = [r for r in rows if not keep(r)], cap()
    drop = {id(r) for r in plain[:-limit]} if limit and len(plain) > limit else set()     # oldest plain dictations first
    rows = [r for r in rows if id(r) not in drop]
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(HISTORY)                                   # all or nothing: a crash mid-write loses no notes
    _cache["sig"], _cache["rows"] = _sig(), [dict(r) for r in rows]


def apply_cap() -> int:
    """Drops the oldest plain dictations over the keep limit, and their recordings, right now. Returns how many."""
    before = {r["id"] for r in _rows()}
    _write(_read())
    gone = before - {r["id"] for r in _rows()}
    for f in (AUDIO.iterdir() if gone and AUDIO.exists() else []):
        m = _AUDIO_ID.match(f.name)
        if m and m.group(1) in gone:
            f.unlink()
    return len(gone)


def add(text: str, seconds: float, took: float, where: str, app: str, **extra) -> str | None:
    """One dictation, or a note (extra: kind, title, segments, source). Returns its id."""
    if not text or (not prefs()["keep_history"] and extra.get("kind", "dictation") == "dictation"):
        return None
    now = time.time()
    row = {"id": repr(now), "at": now, "text": text, "seconds": round(seconds, 1), "took": round(took, 2),
           "where": where, "app": app, **extra}
    rows, limit = _rows(), cap()
    if limit and sum(1 for r in rows if not keep(r)) >= limit:
        _write(_read() + [row])                            # at the limit: rewrite, dropping the oldest
    else:                                                  # the usual case: one line, not the whole file (465 ms at 25,000 notes)
        DIR.mkdir(parents=True, exist_ok=True)
        lead = ""
        if HISTORY.exists() and HISTORY.stat().st_size:       # a crash can leave the last line without its newline: never glue onto it
            with HISTORY.open("rb") as fb:
                fb.seek(-1, 2)
                lead = "" if fb.read(1) == b"\n" else "\n"
        with HISTORY.open("a", encoding="utf-8") as f:
            f.write(lead + json.dumps(row, ensure_ascii=False) + "\n")
        _cache["sig"] = _sig()
        _cache["rows"].append(dict(row))                   # the cache stays valid: it is the old rows plus this one
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


def combine(ids: list[str]) -> str | None:
    """
    Make one note out of several finished dictations (Android has the same, see Notes.combine). The full text of each
    source is COPIED into the new note under a "— Clip N: title · time —" header, so deleting any source leaves the
    combined note intact. Source ids are stored only for jump-back.

    kind="combined" so (a) the row survives the plain-dictation CAP (`keep()` protects anything non-dictation), and
    (b) the UI can style it slightly differently. Returns the new row's id, or None if nothing valid was passed.
    """
    rows = _read()
    picked = [r for r in rows if r["id"] in ids and r.get("text", "").strip()
              and (r.get("kind", "dictation") in ("dictation", "combined", "file", "meeting"))]
    if len(picked) < 2:
        return None
    picked.sort(key=lambda r: r.get("at", 0))                                 # oldest-first
    labels = []
    chunks = []
    for i, r in enumerate(picked, start=1):
        when = time.strftime("%d %b, %I:%M %p", time.localtime(r.get("at", 0))).lstrip("0")
        title = (r.get("title") or "").strip() or f"Dictation {i}"
        labels.append(f"{title} · {when}")
        chunks.append((r.get("real_text") or r.get("text") or "").strip())
    # No "— Clip N: … —" headers: those made the AI treat each piece as a separate thing to rewrite / summarise.
    # The user picked these BECAUSE they belong together, so the AI should see one piece. Which clips they came from
    # is kept in `sources` + `sourceLabels` for display (e.g. "Combined from 4 clips" on the row).
    text = "\n\n".join(chunks)
    now = time.time()
    day = time.strftime("%d %b", time.localtime(now)).lstrip("0")
    row = {
        "id": repr(now), "at": now, "text": text, "seconds": round(sum(r.get("seconds", 0) for r in picked), 1),
        "took": 0.0, "where": "combined", "app": "",
        "kind": "combined", "title": f"Combined · {len(picked)} clips · {day}",
        "sources": [r["id"] for r in picked], "sourceLabels": labels,
    }
    _write(rows + [row])
    return row["id"]


def history() -> list[dict]:
    """Newest first."""
    return _read()[::-1]


def ai_cost_month() -> tuple[float, int, int]:
    """
    Sum of USD spent on AI this calendar month, count of answers that carried a cost, and count of answers that
    didn't (local Claude CLI, unknown models). The 2nd number plus the 3rd = total AI answers this month.
    """
    now = time.localtime(time.time())
    total, with_cost, without_cost = 0.0, 0, 0
    for r in _read():
        for a in r.get("ai", []) or []:
            at = time.localtime(a.get("at") or r.get("at") or 0)
            if at.tm_year != now.tm_year or at.tm_mon != now.tm_mon:
                continue
            c = a.get("cost_usd")
            if c is not None:
                total += c
                with_cost += 1
            else:
                without_cost += 1
        if r.get("improved_cost") and (r.get("improved_at") or r.get("at")):           # improved is a single answer per note
            at = time.localtime(r.get("improved_at") or r.get("at") or 0)
            if at.tm_year == now.tm_year and at.tm_mon == now.tm_mon:
                c = r["improved_cost"].get("cost_usd")
                if c is not None:
                    total += c
                    with_cost += 1
                else:
                    without_cost += 1
    return round(total, 4), with_cost, without_cost


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


_AUDIO_ID = re.compile(r"^(\d+\.\d+)(?:-you|-others)?\.\w+$")


def audio_counts() -> dict[str, int]:
    """How many recordings each note has in Inditeflow's own audio folder, from ONE directory listing (a stat per note
    would be 25,000 disk checks on every page update after years of use)."""
    out: dict[str, int] = {}
    if AUDIO.exists():
        with os.scandir(AUDIO) as it:
            for e in it:
                m = _AUDIO_ID.match(e.name)
                if m and e.is_file():
                    out[m.group(1)] = out.get(m.group(1), 0) + 1
    return out


def audio_count(row: dict, counts: dict[str, int]) -> int:
    """audio_files(row) without touching the disk for dictations and meetings; a file note points at its source file."""
    if row.get("kind") == "file":
        return len(audio_files(row))
    return counts.get(row["id"], 0)


AUDIO_TRASH = DIR / "audio_trash"        # where "delete the recording" moves it, so Undo can bring it back


def stash_audio(note_id: str) -> int:
    """Moves a note's recordings out of the audio folder (Undo moves them back). Only files inside Inditeflow's own folder:
    a transcribed file's original is the user's own file and is never touched. Returns how many were moved."""
    moved = 0
    for name, n in [(f.name, f) for f in (AUDIO.iterdir() if AUDIO.exists() else [])]:
        m = _AUDIO_ID.match(name)
        if m and m.group(1) == note_id and n.is_file():
            (AUDIO_TRASH / note_id).mkdir(parents=True, exist_ok=True)
            n.replace(AUDIO_TRASH / note_id / name)
            moved += 1
    purge_audio_trash(600.0)
    return moved


def unstash_audio(note_id: str) -> int:
    back = 0
    d = AUDIO_TRASH / note_id
    if d.is_dir():
        AUDIO.mkdir(parents=True, exist_ok=True)
        for f in d.iterdir():
            f.replace(AUDIO / f.name)
            back += 1
        d.rmdir()
    return back


def purge_audio_trash(older_than: float = 600.0) -> int:
    """Really deletes stashed recordings older than this many seconds (all of them at start-up, with 0)."""
    gone = 0
    if AUDIO_TRASH.is_dir():
        for d in AUDIO_TRASH.iterdir():
            if d.is_dir() and time.time() - d.stat().st_mtime >= older_than:
                for f in d.iterdir():
                    f.unlink()
                    gone += 1
                d.rmdir()
    return gone


def delete_text(note_id: str) -> dict | None:
    """Deletes what was said but keeps the note and its recording ("sound only"). Returns the old row for Undo."""
    rows = _read()
    old = next((r for r in rows if r["id"] == note_id), None)
    if not old:
        return None
    new = {k: v for k, v in old.items() if k not in ("segments", "wt", "raw", "flags", "reviewed", "improved", "ai", "said", "names", "speakers")}
    new.update(text="", text_deleted=True)
    _write([new if r["id"] == note_id else r for r in rows])
    return old


def replace(row: dict) -> None:
    """Puts a row back exactly as it was (Undo of delete_text)."""
    _write([row if r["id"] == row["id"] else r for r in _read()])


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


AUDIO_CAP_MB = 500         # how much kept audio to hold before the oldest is let go


def audio_size_mb() -> float:
    """How much disk the kept recordings are using."""
    if not AUDIO.exists():
        return 0.0
    return sum(f.stat().st_size for f in AUDIO.iterdir() if f.is_file()) / 1e6


def trim_audio(cap_mb: float | None = None) -> tuple[int, float]:
    """
    Delete the oldest recordings until the kept audio fits under the cap. Returns (files deleted, MB freed).

    Keeping every recording grows about 31 MB a day and had no limit at all - 202 MB after a week, with nothing to
    stop it (22 Oct). The audio is a convenience: the text of every note is kept whatever happens here, and so is
    the audio of anything starred or on the to-do list, because those were marked as worth keeping.
    """
    cap = (cap_mb if cap_mb is not None else AUDIO_CAP_MB) * 1e6
    if not AUDIO.exists():
        return 0, 0.0
    try:
        protect = {r["id"] for r in _read() if keep(r)}   # starred or on the to-do list: never dropped for space
    except Exception:                                    # noqa: BLE001 - an unreadable history must never cost audio
        return 0, 0.0
    def droppable(f: Path) -> bool:
        note = re.match(r"^(\d+\.\d+)(?:-you|-others)?\.\w+$", f.name)
        return not (note and note.group(1) in protect)

    # The cap counts only what can be dropped. Counting protected audio too meant 891 MB of starred meetings (24 Oct)
    # sat over the 500 MB cap for good, so every new dictation's recording was deleted the moment it was saved.
    files = sorted((f for f in AUDIO.iterdir() if f.is_file() and droppable(f)), key=lambda f: f.stat().st_mtime)
    total = sum(f.stat().st_size for f in files)
    gone = freed = 0
    for f in files:
        if total <= cap:
            break
        size = f.stat().st_size
        f.unlink()
        total -= size
        freed += size
        gone += 1
    return gone, freed / 1e6


def backup(path: Path, scope: str = "all", with_audio: bool = False) -> int:
    import zipfile
    rows = [r for r in _read() if scope == "all" or (scope == "star" and r.get("star"))
            or (scope == "keep" and (r.get("star") or r.get("todo")))]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps({"app": "inditeflow-mac", "format": FORMAT, "made": time.time(),
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
    """Returns how many notes were added or refilled. Refuses a backup from a newer Inditeflow rather than half-reading it.
    A note that is already here is left alone, except when it lost its words or its recording ("Delete → words only /
    recording only" leaves an empty note behind, 24 Oct): those come back from the backup. A plain dictation older than
    the keep limit would be dropped again at once, so it is not counted as restored."""
    import zipfile
    restore_zip.over_limit = 0
    with zipfile.ZipFile(path) as z:
        meta = json.loads(z.read("manifest.json"))
        if meta.get("format", 0) > FORMAT:
            raise ValueError("This backup was made by a newer Inditeflow. Update Inditeflow, then restore it.")
        names = set(z.namelist())
        have = {r["id"]: r for r in _read()}
        new, refill, touched = [], {}, set()
        for line in z.read("notes.jsonl").decode("utf-8").splitlines():
            r = json.loads(line)
            cur = have.get(r["id"])
            if cur is not None and not ((cur.get("text_deleted") or not cur.get("text")) and r.get("text")):
                if _put_audio(z, names, r):                        # words are fine here; only a lost recording comes back
                    touched.add(r["id"])
                continue
            _put_audio(z, names, r)
            if r.get("backup_audio") and r.get("kind") == "file":
                r["source"] = str(AUDIO / f"{r['id']}{Path(r['backup_audio']).suffix}")   # the original may not exist here
            r.pop("backup_audio", None)
            r.pop("backup_tracks", None)
            if cur is None:
                new.append(r)
            else:                                                  # the note kept its place; the words come back
                refill[r["id"]] = {**r, **{k: cur[k] for k in ("star", "todo") if k in cur}}
    if new or refill:
        rows = [refill.get(r["id"], r) for r in _read()] + new
        _write(sorted(rows, key=lambda r: r.get("at", 0)))
        kept = {r["id"] for r in _read()}
        back = set(refill) | {r["id"] for r in new}
        touched |= back & kept
        restore_zip.over_limit = len(back - kept)            # the keep limit took these straight back out
    return len(touched)


def _put_audio(z, names: set, r: dict) -> bool:
    """Writes a backed-up note's recordings that are missing here. True when it wrote at least one."""
    wrote = False
    a = r.get("backup_audio")
    if a and a in names:
        dest = AUDIO / f"{r['id']}{Path(a).suffix}"
        if not dest.exists():
            AUDIO.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(a))
            wrote = True
    for name in r.get("backup_tracks", []):                        # a meeting's you / others tracks
        if name in names and "/" not in name[len("audio/"):] and not (AUDIO / Path(name).name).exists():
            AUDIO.mkdir(parents=True, exist_ok=True)
            (AUDIO / Path(name).name).write_bytes(z.read(name))
            wrote = True
    return wrote


# ---- your own word fixes ---------------------------------------------------------------------------------------
# One per line, "what it writes = what you want". Read on every dictation, so a saved edit works on the next one.
# "=" and not a tab, because the person editing this is in TextEdit, where a tab and spaces look the same.
FIXES_HEADER = """# Inditeflow: your word fixes. One per line:   what Inditeflow writes = what you want
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
    if heard == want:                                    # a fix that only changes capitals (jira → Jira) is allowed: it is how names are kept
        return "Those are exactly the same."
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
    assert AUDIO_CAP_MB > 0 and audio_size_mb() >= 0
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
    u = add("fresh dictation", 1, 1, "done", ""); (AUDIO / f"{u}.wav").write_bytes(b"abcd")
    assert trim_audio(cap_mb=0.00001) == (0, 0.0) and (AUDIO / f"{u}.wav").exists()   # starred audio (13 B) over the 10 B cap must not eat a new clip
    assert trim_audio(cap_mb=0.000001)[0] >= 1 and not (AUDIO / f"{u}.wav").exists()  # but a real overflow of droppable audio still trims
    assert (AUDIO / f"{c}.wav").exists()                                              # starred audio is never dropped
    assert fix_problem("jira", "Jira") == "" and fix_problem("jira", "jira") != ""                       # capitals-only fixes are fine
    assert apply_my_fixes("we use jira, JIRA and Jira", [("jira", "Jira")]) == "we use Jira, Jira and Jira"
    HISTORY = Path(tempfile.mkdtemp()) / "torn.jsonl"; DIR = HISTORY.parent                           # a torn last line costs only itself
    HISTORY.write_text('{"id": "1.5", "at": 1.5, "text": "kept"}\n{"id": "2.5", "at": 2.5, "tex')
    _cache["sig"] = None
    assert [r["text"] for r in history()] == ["kept"]
    add("after the crash", 1, 1, "done", "x")
    assert [r["text"] for r in history()][0] == "after the crash"
    _cache["sig"] = None
    assert [r["text"] for r in history()] == ["after the crash", "kept"]                              # re-read from disk: nothing lost
    # delete choices: recording only (Undo brings it back), text only (the note stays as sound), both
    HISTORY = Path(tempfile.mkdtemp()) / "del.jsonl"; DIR = HISTORY.parent; AUDIO = DIR / "audio"; AUDIO_TRASH = DIR / "audio_trash"; AUDIO.mkdir()
    d1 = add("hello there", 2, 1, "done", "x"); (AUDIO / f"{d1}.wav").write_bytes(b"RIFF1234")
    assert audio_counts() == {d1: 1} and audio_count(history()[0], audio_counts()) == 1
    assert stash_audio(d1) == 1 and audio_counts() == {} and history()[0]["text"] == "hello there"      # recording gone, note kept
    assert unstash_audio(d1) == 1 and audio_counts() == {d1: 1}                                          # Undo
    old = delete_text(d1); assert old["text"] == "hello there" and history()[0]["text"] == "" and history()[0]["text_deleted"]
    assert audio_counts() == {d1: 1}                                                                    # the recording stays
    replace(old); assert history()[0]["text"] == "hello there" and "text_deleted" not in history()[0]   # Undo
    stash_audio(d1); assert purge_audio_trash(0) == 1 and not (AUDIO_TRASH / d1).exists()               # really gone
    # how many plain dictations to keep: the oldest go first, a star is never counted, 0 keeps everything, and the
    # parsed-rows cache always agrees with the file (add() appends one line instead of rewriting it)
    HISTORY = Path(tempfile.mkdtemp()) / "cap.jsonl"; DIR = HISTORY.parent
    cap = lambda: 3                                                      # noqa: E731 - the check's own limit
    for i in range(5):
        add(f"n{i}", 1, 1, "done", "x")
    assert [r["text"] for r in history()] == ["n4", "n3", "n2"]
    keepme = add("starred", 1, 1, "done", "x"); update(keepme, star=True)
    for i in range(5, 8):
        add(f"n{i}", 1, 1, "done", "x")
    assert [r["text"] for r in history()] == ["n7", "n6", "n5", "starred"]   # 3 plain dictations + the star
    cap = lambda: 0                                                      # noqa: E731 - everything
    for i in range(8, 40):
        add(f"n{i}", 1, 1, "done", "x")
    cached = [r["text"] for r in history()]
    _cache["sig"] = None                                                 # force a fresh parse of the file
    assert len(cached) == 36 and [r["text"] for r in history()] == cached
    # multi-select: two dictations in → one combined note out, with headers and sources preserved.
    HISTORY.write_text("")
    d1 = add("the meeting with Priya went well", 1, 1, "done", "")
    d2 = add("she wants pricing by Friday", 1, 1, "done", "")
    nid = combine([d1, d2])
    assert nid is not None
    r = next(x for x in history() if x["id"] == nid)
    assert r["kind"] == "combined" and r["sources"] == [d1, d2] and len(r["sourceLabels"]) == 2
    # The text the AI sees must NOT carry "Clip N:" headers (that was making it rewrite each clip separately,
    # founder, 23 Oct). It's just the concatenated transcripts with blank-line breaks.
    assert "Clip 1" not in r["text"] and "Priya" in r["text"] and "Friday" in r["text"]
    assert combine([d1]) is None                                   # needs 2+
    assert combine([d1, "no-such-id"]) is None                     # only one valid id → still refuses
    # a combined row is NOT a plain dictation, so clear() must not touch it
    assert clear() == 2                                            # d1, d2 go; the combined one stays
    assert any(x["id"] == nid for x in history())
    # restore after Delete → words only / recording only: the empty note is refilled (24 Oct: it said "already here")
    HISTORY = Path(tempfile.mkdtemp()) / "rest.jsonl"; DIR = HISTORY.parent; AUDIO = DIR / "audio"; AUDIO_TRASH = DIR / "audio_trash"; AUDIO.mkdir()
    cap = lambda: 0                                                      # noqa: E731
    r1 = add("old words", 2, 1, "done", "x"); (AUDIO / f"{r1}.wav").write_bytes(b"SND1")
    r2 = add("other words", 2, 1, "done", "x"); (AUDIO / f"{r2}.wav").write_bytes(b"SND2")
    z = DIR / "r.zip"; assert backup(z, "all", with_audio=True) == 2
    assert restore_zip(z) == 0                                           # nothing lost: nothing changed
    delete_text(r1)
    assert restore_zip(z) == 1 and next(x for x in history() if x["id"] == r1)["text"] == "old words" \
        and "text_deleted" not in next(x for x in history() if x["id"] == r1)
    stash_audio(r2); purge_audio_trash(0)
    assert restore_zip(z) == 1 and (AUDIO / f"{r2}.wav").read_bytes() == b"SND2"      # the recording alone comes back
    delete(r1); stash_audio(r1); purge_audio_trash(0)
    assert restore_zip(z) == 1 and (AUDIO / f"{r1}.wav").read_bytes() == b"SND1"      # whole note + recording
    assert restore_zip(z) == 0
    # a plain dictation older than the keep limit is not "restored": it would be dropped at once
    cap = lambda: 1                                                      # noqa: E731
    delete(r1)
    assert restore_zip(z) == 0 and {x["id"] for x in history()} == {r2}  # r1 is older than the 1 kept: honest "0"
    assert restore_zip.over_limit == 1
    # a smaller keep limit is applied at once and takes the dropped notes' recordings with it
    cap = lambda: 0                                                      # noqa: E731
    HISTORY = Path(tempfile.mkdtemp()) / "now.jsonl"; DIR = HISTORY.parent; AUDIO = DIR / "audio"; AUDIO.mkdir()
    ids = [add(f"m{i}", 1, 1, "done", "x") for i in range(6)]
    for i in ids:
        (AUDIO / f"{i}.wav").write_bytes(b"x")
    cap = lambda: 4                                                      # noqa: E731
    assert apply_cap() == 2 and [r["text"] for r in history()] == ["m5", "m4", "m3", "m2"]
    assert not (AUDIO / f"{ids[0]}.wav").exists() and (AUDIO / f"{ids[5]}.wav").exists()
    assert apply_cap() == 0
    print("ok")
