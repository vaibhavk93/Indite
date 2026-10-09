# indite

Hinglish-first speech-to-text. Output is Roman script ("kal meeting hai").

## Setup

```sh
export UV_SYSTEM_CERTS=1          # needed on networks that inspect HTTPS
uv sync                           # app + Sarvam engine
sh scripts/setup_local.sh         # free local engine: builds whisper.cpp, shrinks the Hinglish model to ~550 MB (~10 min, once)
sh scripts/setup_local.sh --best  # optional: also the slower, loop-free "best quality" model (~1 GB)
cp .env.example .env              # then paste your Sarvam key into .env
```

## Use

```sh
uv run indite transcribe meeting.m4a                                 # free, on this Mac (~0.8 GB RAM)
uv run indite transcribe meeting.m4a --engine local-best             # free, slower, fewest loops (~2 GB RAM)
uv run --env-file .env indite transcribe meeting.m4a --engine sarvam # paid, ~₹30/audio hour
uv run --env-file .env indite bench clips/                           # score both engines
```

Output styles (`--style`):

| Style | For | File |
|---|---|---|
| `timestamped` (default) | interviews, calls | `meeting.timestamped.txt` |
| `paragraphs` | lectures, notes | `meeting.paragraphs.txt` |
| `srt` / `vtt` | subtitles (max 2 lines × 42 chars) | `meeting.srt` / `meeting.vtt` |

Every run also saves `meeting.indite.json`. To change style without transcribing (or paying) again:

```sh
uv run indite transcribe meeting.indite.json --style srt
```

Parts the engine may have invented (text over silence, looping phrases, "thanks for watching") are marked `[check: ...]` in the timestamped style. Nothing is deleted.

## Web app

```sh
uv run --env-file .env indite serve       # then open http://127.0.0.1:8000
```

Upload → transcribe in the background → edit (click a time to hear it) → export SRT/VTT/TXT,
or "Copy for Claude / ChatGPT" for notes. Runs on this Mac only. Files live in `data/` and are deleted after 3 years.
Edited lines keep the engine's original text, so we can later measure how much people had to fix.

Checks: `uv run python tests/test_web.py`

## Notes with your own Claude or ChatGPT (experimental)

```sh
uv run indite notes meeting.indite.json               # uses your installed, logged-in `claude`
uv run indite notes meeting.indite.json --via codex   # uses your installed, logged-in `codex` (untested)
```

Writes `meeting.notes.md`: summary, decisions, action items, open questions. Runs your own `claude -p` or
`codex exec` on this Mac with every tool switched off. indite never reads your login. This counts against your
plan's usage limits. Vendor rules changed often in 2026, so this may stop working.

## Test clips for `bench`

```
clips/
  creators/   c1.m4a  c1.txt
  interviews/ i1.m4a  i1.txt
  calls/      s1.m4a  s1.txt
  students/   l1.m4a  l1.txt
```

Each `.txt` is what was actually said, typed in Roman script, using one spelling style. The folder name becomes the group in the results. Engine outputs are cached in `clips/.results/`, so re-running never pays twice.

Self-check: `uv run python tests/test_core.py`
