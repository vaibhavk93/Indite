# indite for Mac

Hold a key, speak, let go. The words are typed where your cursor is, in any app, in about a second.
Everything happens on this Mac: no account, no server, no internet needed.

This file is the one place that says what the Mac app does today. Keep it true: update it in the same commit as
any change to `mac/`. Plans and comparisons live in `docs/MAC_PLAN.md`.

---

## Run it

```sh
./mac/build_app.sh      # builds dist/indite.app (a small launcher that runs mac/indite_mac.py from this folder)
open dist/indite.app    # opens the window; a 🎙 sits in the menu bar
```

Logs: `~/Library/Logs/indite-mac.log` (one line per dictation, with how long it took).

**⚠ The Mac app and the Android app are kept separate.** The Mac never reads `android/`. It has its own model
(`mac/models/`, a hard link to the phone's file, so no extra disk, never in git) and its own `mac/spelling.tsv`.

## The two permissions

| Permission | Why | Where |
|---|---|---|
| **Accessibility** | to notice the hotkey and type into the app you are in | System Settings → Privacy & Security → Accessibility → indite |
| **Microphone** | to hear you | asked the first time you hold the key |

macOS sends no key events to an app without Accessibility, and nothing complains: holding the key just does nothing.
The window shows a banner when the permission is missing.

---

## What it does

| Feature | How |
|---|---|
| **Dictate anywhere** | Hold Right ⌥ (or Left ⌥ / Right ⌘ / Right ⌃), speak, let go |
| **Where the words go** | *Smart*: typed into the text box; copied to the clipboard when there is none. Or always type / always copy |
| **Hands-free** | Tap the key twice (or three times; or pick another key in Settings) and let go; tap once to finish. Red dot in the pill. Stops itself after 15 min |
| **Paste last** | ⌃⌘V types the last dictation again (password guard applies) |
| **Sounds** | Tick on start, pop on stop; Settings → Sounds |
| **Microphone** | Settings → Microphone: Automatic or a named mic; remembered by name, list refreshed on every press |
| **Cancel** | Esc while holding (or while hands-free). Nothing is typed. (Esc also reaches the app underneath; macOS will not let indite block it) |
| **Long dictation** | Holds over 20 s are cut at the quietest moments into pieces; no sound is dropped |
| **Hinglish spelling** | Everyday words written one way (achha, kyunki, maine) from `mac/spelling.tsv` |
| **Word fixes** | Pencil on any history row: "indite wrote / you meant" (shows how many past dictations hold the word). Or Settings → Word fixes → Edit… for the file: `ptm = Paytm`. Whole words, any capitals |
| **Password boxes** | Never typed, copied or saved. The pill says "password box" |
| **Files** | Home → Transcribe a file… (or the menu bar): any audio/video file, transcribed inside the app with the loaded engine; Text and Subtitles (.srt) export |
| **Meetings** | Home → Record a meeting: your mic ("You") + the Mac's sound ("Others", needs Screen & System Audio Recording), text at every pause, saved as it goes, both tracks kept as WAV. REC timer in the pill |
| **Who spoke** | Files: "Who spoke?" (guess, or 2–5). Meetings: Others split into Person 1, 2… after stopping. Click a name to rename. 59/60 turns right on clear voices, 56/60 on similar ones |
| **Notes** | Star (kept forever), ○ To do (its own page, Done ticks), delete with Undo, filters: All / Starred / Files / Meetings |
| **AI on notes** | ✨: improve the wording (original kept), meeting notes, action items (→ To do in one click), summary, lecture notes, brain dump, rewrite in a style, translate, clean up. Your own `claude` login; asks once before text leaves the Mac |
| **Accuracy passes** | Hinglish spelling (now also on words with punctuation), number words → digits next to baje/percent/rupaye, junk from sub-second taps dropped |
| **Backup** | Settings → Backup: all / starred / starred + to-do, with or without audio; restore adds only what is missing |
| **Setup** | First-run screen: Accessibility, microphone, key, try it. Help → Run setup again |
| **Window** | Dictations · Meetings · Files · To do · Dictionary · Settings (General, Look & sounds, Writing, AI, Privacy, Backup, with a finder) · Help. Every note: Copy and a “…” menu (or right-click). Appearance: Light / Dark / Like the Mac |
| **The pill** | Small clear Liquid Glass pill with a two-tone border, above the Dock: voice bars while you hold, a wave of dots and a moving glint while writing, then "✓ typed in", "✓ copied", "nothing heard", "cancelled" or "didn't work". Never takes focus, never blocks a click |
| **Microphone fallback** | If the default mic will not open (a Bluetooth headset that is off), tries the last one that worked, the built-in one, then any other |
| **History** | Home: last 500 dictations by day, search (⌘F), one-click copy. Stats: words, words a minute, average wait |
| **Privacy** | Keep a history on/off; Clear history (asks first). Recordings are deleted as soon as they are transcribed |

## Speed and accuracy, measured (M1, 15 Oct)

| | |
|---|---|
| Time to text, 3–8 s sentence | **0.7–0.9 s** (model kept loaded in `whisper-server` on 127.0.0.1:8711) |
| Words wrong, clean Hinglish sentences | **19%** one by one |
| Long holds, cut into pieces | 62 s → 19.0% wrong in 7.3 s · 93 s → 19.7% in 10.7 s (was 75% and 54% before cutting) |

Two things make the speed, and both are easy to lose: the model stays loaded, and every request sends a window
sized to the audio (without it the engine pads to 30 s and takes 2.2 s).

## Files

| What | Where |
|---|---|
| History | `~/Library/Application Support/indite/history.jsonl` (plain text, capped at 500) |
| Web app log | `~/Library/Logs/indite-web.log` |
| Settings | `~/Library/Application Support/indite/prefs.json` |
| Word fixes | `~/Library/Application Support/indite/my_fixes.txt` |
| Audio (kept dictations, meetings) | `~/Library/Application Support/indite/audio/` |
| Code | `indite_mac.py` (hotkey, mic, engine, typing) · `overlay.py` (pill) · `window.py` + `ui/app.html` (window) · `store.py` (files) |

## Checks

```sh
.venv/bin/python mac/store.py                                   # word fixes
.venv/bin/python tests/test_mac_handsfree.py                    # hold / tap / double-tap / Esc / other key
.venv/bin/python mac/digits.py ; .venv/bin/python mac/ai.py ; .venv/bin/python mac/meeting.py
.venv/bin/python mac/speakers.py                                # who-spoke accuracy on the test dialogue
.venv/bin/python -c "import sys; sys.path.insert(0,'tests'); import test_mac_pieces as t; \
  t.test_long_hold_is_cut_in_the_quiet_and_loses_nothing(); t.test_short_hold_is_untouched()"
```

## Not yet

- Not shareable: `indite.app` runs Python and the model from this folder, so it works only on this Mac.
- The engine takes a few seconds to load at startup; the menu bar shows 🎙… until it is ready.
- Untested on real non-stop speech over 60 s and on a quiet speaker.
- Meeting capture of the call's audio is untested with the Screen Recording permission actually granted.
- Credits: TitaNet-small speaker model © NVIDIA, CC BY 4.0; sherpa-onnx Apache 2.0; whisper.cpp MIT; Hinglish model Apache 2.0.
