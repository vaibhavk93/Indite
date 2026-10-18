# indite handoff

**Read this first.** It lets any Claude Code or Codex session (or a different account) continue the work. Keep it current:
update "Where things stand" and add a dated entry to `docs/WORKLOG.md` at the end of every session.

Last updated: 2026-10-10.

---

## 1. What indite is

Offline, private Hinglish speech-to-text. Speak Hindi + English, get Roman-script text ("kal meeting hai").

| Part | Where | State |
|---|---|---|
| **Android app** (main product) | `android/` | build 29 on the founder's OnePlus 12 |
| **Mac app** (hold a key, speak, it types) | `mac/`, built to `dist/indite.app` | working; 0.8 s per sentence with the engine resident |
| Mac CLI + web app | `indite/` (Python, `uv`) | working; local + Sarvam engines |
| Benchmarks | `bench_synth/` (synthetic Hinglish + automated phone test), `indite bench` | working |

Docs that matter, in order:
1. `ROADMAP.md`: **the one roadmap**, split Mac / Android, each done / next / later / parked (17 Oct). Add new items there, nowhere else (built / now / next / later / not doing / founder requests with status). The page
   https://claude.ai/artifact/GuCGtX4TJeASaS2RpGFS4q is published from it. **Update both together.**
2. `PLAN.md`: every decision and test result, with reasons.
3. `docs/AI_MODES.md`: AI features spec (notes, action items, practice, tiers T1–T4).
4. `reports/*.md` (local only, not in git): research reports.
5. `docs/WORKLOG.md`: what each session did.
6. **`docs/FOUNDER_REQUESTS.md`: every founder request with its status. Add new asks and update statuses every session.**

---

## 2. Rules every session must follow

**Founder's working rules** (from the founder's global instructions):
- **Every suggestion passes an independent critic first** (a fresh subagent, not a fork): a feature, design, fix, priority.
  Show the critic's objections and what changed. Evidence over opinion; label unproven things "unproven".
- **Plain, simple language.** Short sentences, explain every term, lead with the answer, tables over paragraphs,
  ASCII trees with boxed options for any branching choice, **⚠ Remember:** flags for critical points.
- Don't drop numbers, caveats or bad news to make text shorter.

**Product rules** (decided, see PLAN.md):
- Audio never leaves the phone. **The public build has no INTERNET permission**: check with `aapt2 dump permissions`.
- Zero per-use cost to the founder. AI only via the user's own AI app, own API key (personal build for now), or the
  founder's own Mac (personal build, removed before launch).
- No in-app Claude/Gemini/ChatGPT login (terms). **Reminders: indite sets its own** (founder decision, 10 Oct, overrides the old "hand off to Calendar / Clock" rule); Calendar and Share are still offered on task rows.
- The `personal` flavour is founder-only: internet, Mac route, OpenRouter key, accessibility auto-paste.

**Design rule (founder, 17 Oct):** indite has its own design language, not the generic AI-tool look. Read
`docs/DESIGN.md` before any UI work and add new patterns to it.

**Testing without disturbing the founder (founder, 17 Oct):** tests of the running app must not take over his screen.
Use the **hidden test copy**: `python mac/testcopy.py start | js | eval | cmd | stop` (own data folder
`~/Library/Application Support/indite-test`, own engine on port 8712 with 2 threads; no keys, mic, typing, clipboard,
pill, card, menu icon, sound or focus; what it would have typed or shown goes to `offstage.jsonl`). Feed speech with
`cmd "dictate:<wav>"` (16 kHz mono, e.g. `bench_synth/clean/s03.wav`).
- **⚠ Stop it when done.** While it runs, opening indite from Spotlight/Finder may reach the hidden copy.
- **⚠ Restart the founder's app with `open -n -g dist/indite.app`** - plain `open` hands over to the test copy if it
  is running (happened 17 Oct: his indite was down ~30 s). Before any restart, check the log: no `pill:` line in the
  last ~2 minutes (the `paint:` lines come every ~10 s).
- Its window does not draw pictures (macOS stops painting off-screen windows): check the page with `eval`; for a
  picture, render `mac/ui/app.html` in headless Chrome with made-up notes.
- Still on the real screen, only with his OK: typing into other apps, the pill, the card's look.
- Never kill engines with `pkill -f "whisper-server...8712"` from a shell command line: the pattern matches the shell.
- **⚠ Never run `dist/indite.app/Contents/Resources/python/bin/python3` directly** (use `.venv/bin/python`). It writes
  `.pyc` files into the app, which breaks its signature: the app then warns "app file has been changed" on the
  founder's screen and Accessibility can stop working (17 Oct). Fix: delete `.pyc` files newer than `Contents/Info.plist`,
  then `codesign --verify --deep --strict dist/indite.app`.

**Repo rules:**
- **⚠ Giving indite to anyone else: send ONLY `dist/portable/indite-mac.zip`, built with `./mac/build_portable.sh`.**
  `dist/indite.app` (mac/build_app.sh) is the founder's own copy: it runs code, libraries and the model from this
  project folder, so on another Mac it "does nothing" (17 Oct, his boss's M2). The portable build carries everything,
  needs macOS 14+ on Apple Silicon, and stops itself if `mac/portable_check.py` finds a home-folder path, a binary for
  a newer macOS or another chip, a missing file, or anything loaded from outside the app. It needs 4 GB free.
- **Never quote speech-set sentences, references or results in docs or commits** (they may hold work names; the repo is public). They live in `~/Library/Application Support/indite/speechset/`.
- **The GitHub repo is PUBLIC** (github.com/vaibhavk93/Indite). Never commit `.env`, `data/`, `clips/`, `phonetest/`,
  `test_recordings/`, APKs, models, or any recording of real people. Never put tokens or keys in docs.
- Commit as `vaibhavk93@users.noreply.github.com` (`git -c user.email=... commit`), never a work email.
- Commit and push only when the founder asks, or as part of a build he asked for.

---

## 3. Build, install, test (Android)

```sh
cd android
export JAVA_HOME="$PWD/../.tools/android/jdk-17.0.20.1+1/Contents/Home"   # the bundled JDK; system has no Java
./gradlew -q assemblePersonalRelease assemblePublicRelease               # ~2-10 min
./gradlew -q :app:testPersonalReleaseUnitTest                            # unit tests (parsers, speaker placement)
A=~/Library/Android/sdk/platform-tools/adb
$A install -r app/build/outputs/apk/personal/release/app-personal-release.apk   # keeps the phone's notes
```

Files that are **not in git** but are needed to build:
| File | Where it goes | How to get it |
|---|---|---|
| Speech model `ggml-apex-q5_k.bin` (574 MB) | `android/app/src/main/assets/models/` | `scripts/setup_local.sh` makes it; copy it in |
| `ggml-silero.bin`, `titanet_small.onnx` | same folder | whisper.cpp VAD model; sherpa-onnx TitaNet-small |
| `sherpa-onnx-1.13.8.aar` | `android/app/libs/` | link in `android/app/build.gradle` |
| Signing key | `~/.indite/indite-testers.keystore` | **irreplaceable**: same key = updates install over the old app |

Model fingerprints (SHA-256), so a rebuild uses exactly the same files:
| File | SHA-256 |
|---|---|
| `ggml-apex-q5_k.bin` | `6f7ab66782c3969cbfc500bc88c43f77be66838937cccb622d184638c62edb9b` |
| `ggml-silero.bin` | `2aa269b785eeb53a82983a20501ddf7c1d9c48e33ab63a41391ac6c9f7fb6987` |
| `titanet_small.onnx` | `ad4a1802485d8b34c722d2a9d04249662f2ece5d28a7a039063ca22f515a789e` |

**Keeping old versions (critic-reviewed 10 Oct):**
- Every build installed on a phone: bump `versionCode`/`versionName` in `android/app/build.gradle`, then
  `git tag build-<versionCode>`. Settings → About shows "build N · git hash" so you can see what's on the phone.
- Keep **one** last-known-good personal APK outside the repo: `~/.indite/apks/` (disk is tight; tags cover older ones).
- **The signing key `~/.indite/indite-testers.keystore` is the one file that can't be replaced.** Founder keeps a copy
  (and its password, `android`) in a password manager or a private, unshared Drive folder. Optional: a copy of the
  574 MB model there too.
- Rollback: Settings → Export all notes → `adb install -r -d <old.apk>` → if notes don't load, uninstall, reinstall,
  re-import the text. Notes have no format version yet, so rollback isn't guaranteed; add a version check when the
  note format changes.

Testing on the phone (USB debugging on, phone untouched while it runs):
```sh
cd bench_synth
QUICK=1 ./phone_test.sh   # ~12 min: live dictation + speaker labels
./phone_test.sh           # ~50 min: also the 15-min file (use when long-file handling changes, and before testers)
```
Personal-build test hooks (adb, see `MainActivity.testHook`): `--es test_import NAME`, `--es test_live NAME`,
`--es test_label NAME --ei k 2`, `--ez test_dump true` (copies the 5 newest recordings' audio out, for mic debugging).

**⚠ Remember:**
- Don't run the phone test while the founder is using the phone: it spoiled a run.
- The Mac is nearly full (about 4 GB free on 10 Oct). Check `df -h ~` before big builds or downloads.
- Mac timings are unreliable (memory pressure). Use the phone for speed numbers.

---

## 4. Code map (Android, `android/app/src/main/java/com/whispercppdemo/`)

| File | What |
|---|---|
| `notes/Notes.kt` | notes on disk (one folder per note: audio.pcm, cuts.json, transcript.jsonl, meta.json, speakers.json, ai.json) |
| `notes/NoteService.kt` | foreground service, transcription queue, `transcribePiece` (dropped-text re-run for live only), Recording |
| `notes/LiveRecorder.kt` | mic → audio.pcm, Silero speech detection, cuts at pauses; last piece saved in `finally` |
| `notes/Speakers.kt` | who spoke: Silero → 1.5 s windows → TitaNet → k-means; sentences placed over speech; guess the count |
| `notes/Settings.kt`, `notes/Guards.kt`, `notes/Pauses.kt` | spelling + word fixes; likely-wrong flags; pause cutting |
| `ui/NotesApp.kt` | home, recording, note screen, AI requests (`AskPrompts`, `ask`, `send`), cards, language picker |
| `ui/SettingsScreen.kt` | Settings in 6 groups |
| `keyboard/VoiceKeyboard.kt` | voice keyboard (listening → writing → typed in) |
| `overlay/BubbleService.kt` | floating mic (+ `StartMicActivity`) |
| `src/personal/…` | `ai/MacCompanion.kt`, `ai/OpenRouter.kt`, `overlay/AutoPaste.kt` (accessibility); `src/public/…` = stubs |

---

## 5. Where things stand (update every session)

**18 Oct 01:45 — Mac: portable app, bug sweep, UI review and critic-passed changes done; roadmap page republished.**
- Give indite to others ONLY as `dist/portable/indite-mac.zip` (`./mac/build_portable.sh`; see Repo rules).
- Meetings: the call's sound reconnects if its capture dies (16 Oct it died after 7 s on headphones); the mic in use
  is shown and logged. Listen: engine "nan" answers retried, else word times estimated from the sound.
- End-to-end bugs fixed (window actions can no longer crash the app; masked text never saved over real words;
  meeting tracks in backups; orphan recordings removed at start). UI review items done; critic dropped 2.
- New: own menu-bar mark (`menubar_icon()`), Ask AI typical wait (`ai_secs`), pill/card on the pointer's screen,
  Stop for files, search on Meetings/Files, ⌘Z after delete, Settings ⌘, / Transcribe ⌘O.
- Open: one Who spoke error in the test copy ("GetElementType is not implemented"), not reproduced; a lock was added.
- Waiting on the founder: D21 (boss's macOS), D20 (headphone call), D14/D15 (speech test), D19 (on-screen look).

**17 Oct 23:05 — Mac roadmap: everything buildable without the founder is built; copy reviewed.**
- New: Listen view in indite's look; card buttons picked in Settings (`card_buttons`); meeting tracks on one clock
  (`Track.catch_up`, arrival-stamped system audio) + "Both" playback (`clock` on the note); word times rebuilt when
  words change (`store.wt_fits`) or the engine heard nothing; lines remember their track (`k`, `store.track_of`);
  per-line speaker fix + join (Listen → click the name); "Record this call?" (`mac/calls.py`, CoreAudio process
  list, `ask_calls`); own hidden words (`my_swears`); setup step 5 (card); speech test (`speech_test`, ⋯ → "This is
  exactly what I said", To check filter, `python mac/speechset.py score` on a private 8712 engine).
- Hidden test copy: `mac/testcopy.py` (see "Testing without disturbing the founder"). Stop it after use.
- Copy: independent review (63 rows) applied; naming rules in DESIGN.md §5. Left: menu-bar emoji icon, an AI
  wait-time hint (needs real timings).
- Waiting on the founder: DECISIONS D14-D19 (Dictionary names, 35 checked dictations, AI order test, live clean-up,
  ₹/lakh, on-screen checks). Not pushed yet.

**17 Oct 17:15 — Mac: text card AI buttons + To do, clipboard rules, Mark likely mistakes, Insights grouped.**
- Every dictation is typed AND copied (`also_copy`); every AI answer is copied when it lands; the card shows it.
- Mark likely mistakes (`mac/review.py`, setting `review`, on for the founder): after typing, a second listen with
  per-word confidence; a saved word is "unsure" unless heard the same way with p ≥ 0.9; Dictionary targets ≥ 6
  letters; Hinglish sound-key; joins with Hindi particles skipped. Synthetic bench 0.19 false/100 words. Note keeps
  `raw` (engine text) and `flags`; decisions go to `fixlog.jsonl`. The real speech set is the gate.
- Swear masking is FIXED (real word stored). The stuck-mic restart has fired 3 times for real and worked.
- ⚠ Two sessions work in this folder and both number FOUNDER_REQUESTS rows: check the last number before adding.

**16 Oct 10:20 — ROADMAP.md is now two roadmaps (Mac, Android) + a limits/parity table + personalisation.**
Recordings can be played from a note's menu. ⚠ Another session works in this folder too: check `git status` before
committing and commit only your own files.

**16 Oct 09:50 — roadmap re-prioritised (ROADMAP.md "Now" + "Parked").** Order: demo (freeze Mac code until
recorded) → real speech set → founder checks → verbose_json → Dictionary cap → AI review step 1. Swear masking now
keeps the real word stored. The published roadmap page is still the 10 Oct version.

**Mac, 16 Oct 03:10 — back-to-back meetings built (founder request 251).** Each recording is its own `Meeting`;
Stop hands it to a background finisher and the next can start at once (it waits only for `released`, ~2 s max).
A stopped meeting never reads the shared mic queue again. `system_audio._output_class()` defines the ScreenCaptureKit
receiver once: before this, **every second meeting in a session failed to start**. Tab dots (`navDots` in
`ui/app.html`) and a "finishing" entry in `ai_busy`. Tested live with `demo_feed.wav` (no real mic); not on a real
call. Four test meetings (16 Oct 03:02-03:06) are in the founder's Meetings list. Assistant idea: request 252.

**Mac, 16 Oct 02:40 — the stuck-mic bug came back; the old fix could not work.** After a meeting, CoreAudio
deadlocked closing the mic and held the device lock for the life of the process, so every later press queued forever
(pill shown, nothing recorded). Now `Mic.start` gives up after 8 s, a stuck close or open raises `MicStuck`, and the
next press restarts indite itself (at most once per 10 min, else "restart the Mac"). **The self-restart is untested
on a real lock-up**: if the log shows "restarting indite to get the microphone back", check it came back.
Founder's assistant idea answered: use Claude/Gemini for actions (ROADMAP "Not doing").

**Mac, 16 Oct ~02:00 — full end-to-end test: 21 of 21 pass.** App, engine, signature, both permissions, 3 live
recordings through the real microphone, typing 389 characters into TextEdit exactly in 0.32 s, a 230 s two-speaker
file transcribed and both voices found (58 labelled parts), and all 8 window pages drawing. Four real bugs were
found and fixed getting there: the CoreAudio deadlock, PortAudio left shut down by a wedged rescan, the consent
dialog pasted into `who_spoke()` (every file reported "file failed"), and the app breaking its own signature.
The 3:20 demo cut is built (`python mac/demo.py --short`) to the beat sheet in `docs/DEMO_PLAN.md` §8.

**Before recording:** close anything private (the screen is recorded whole), Do Not Disturb on, and decide the two
open questions — whether the founder records the narration, and whether a real transcription error is shown on
camera. The signing certificate is deliberately left until after the demo.


**Mac, 16 Oct — ready for the leadership demo.** Fixed since the last entry: long dictation no longer crawls into
text fields (~40x fewer key events, measured in TextEdit and a Chrome textarea, character-exact at 1,576 chars);
word fixes no longer break contractions ("don't" stayed "Dawn't" with the fix `don = Dawn`); the demo script now
covers the gold AI edge, "Make it a prompt" and AI usage in Insights, and pre-answers the meeting→AI warning so the
modal cannot stop a take; "Make it a prompt" rebuilt to Anthropic's published guidance. Research landed in
`docs/WISPR_DEEPDIVE.md`.

**⚠ Open, and it breaks a product rule:** swear masking runs inside `tidy()`, so with the switch on the real word
is never stored — the stars are what gets saved. R5 says nothing is deleted silently. Masking should be a view
(mask when shown or typed, keep the raw text). Off by default, so nothing is lost yet.


**Mac, 15 Oct 23:30 — Ask AI rebuilt three times on founder feedback (latest: answers as documents, options on a
sunken surface, one-click Rewrite/Translate, "Make it a prompt", gold AI chip, AI in Insights). Pill-after-hide bug
fixed. Next: founder looks, restarts the Mac, demo video. Plans: `docs/ROADMAP_DETAIL.md` (AI review first).**

**Mac, 15 Oct 21:55 — key access and Screen Recording both work now.** Hotkey dictation tested by the founder.
The blocker was a silent crash, not the permission (see "The Mac app now" below). Item 1 in the list below is
resolved. Next: restart the Mac (a frozen indite copy holds Dock clicks), then record the demo video.

**Mac, 15 Oct evening — the Wispr Flow gap review changed the plan.** 5 of the 14 "missing" features were already
built (snippets = word fixes, the Dictionary page, and every Insights stat including the streak). What is actually
next is 3 small Dictionary items (~2 h), two gated experiments, and 11 dropped features — `docs/MAC_PLAN.md` §6.

**⚠ Three things beat every feature on that list, and two are shipped features that do not work:**
1. ~~**Screen & System Audio Recording is still not granted**~~ (granted 15 Oct night) → meeting recording (R14) and the demo video (R41) are dead.
2. **The 53 real dictations have never been scored.** Every accuracy number comes from 360 synthetic clips;
   `mac/digits.py:5` admits the digits pass changed 0 of those 53. Scoring them is ~2 h and would re-rank the plan.
3. **Nothing is signed or notarised** (P7, R20), every rebuild resets permissions, and 10 items are still 🧪.

Also cheap and open: the public repo has **no LICENSE file**; the Android keystore still has **one copy**.


**Build 29 (0.29) is on the founder's phone and passes every gate.** Measured 14 Oct, phone cool (33.5 → 36.9 °C):

| Measure | Build 29 | Best before |
|---|---|---|
| Live dictation: wait after a pause | **9.6 s** (worst 16.7 s) | 9.1 s (build 7) |
| Live dictation: words wrong | **17.1%** | 16.9% |
| 15-min import: words wrong | **25.0%** | 25.0% |
| Speaker labels, clear voices | **96.7%** | 96.7% |
| Speaker labels, similar voices | 93.3% | 93.3% |
| Live engine throughput | **1.16x real time** | below 1.0x all day = the cause of 90 s waits |

### The engine fix (13–14 Oct), and two wrong turns on the way

`Pauses.audioCtx` now **sizes the window to the piece**: `min(1280, max(512, ceil((sec+2)*50/256)*256))`.
A flat window was wrong in both directions, and both were measured on the phone:

| Attempt | What broke | Cost |
|---|---|---|
| Flat 768 (old default) | a 5 s sentence paid for 15 s of encoder, so the engine fell behind and the wait compounded | 65.5 s median wait, 0.73x real time |
| Flat 512 (build 27) | shorter than an 11 s piece, so the end of every piece was cut off | live WER 18.3% → 32.8% |
| Flat 512 left on by mistake (build 28) | the test override `shortCtx` shipped as 512 and applied to **every** piece | 15-min import 25.0% → **75.7%** |
| **Window follows the piece (build 29)** | — | all gates pass |

`AudioCtxTest` now fails if the window is ever shorter than the audio, if a short piece pays for a long window, or
if `shortCtx` ships as anything but 0.

### Found the hard way: `adb install` is 60x slower than push + install

| Method | 681 MB APK |
|---|---|
| `adb install -r app.apk` | **34 minutes**, and it failed twice mid-transfer |
| `adb push … /data/local/tmp/x.apk` then `adb shell pm install -r /data/local/tmp/x.apk` | **30 seconds** (17 s push at 38.7 MB/s + 12 s install) |

Use push + install always. Three failed installs and ~90 minutes were lost before this was spotted.

### Done since build 15

- **Backup that can be restored** (`notes/Backup.kt`): a zip with text, times, speaker labels, edits and AI answers;
  audio optional; restore skips notes already present; `fmt` version in every note and a refusal to open a newer one.
- **One door for AI**: the three duplicate buttons and the ten-label menu are gone; one sheet, grouped by intent,
  every action says what it gives back, suggestions ordered by what indite knows about the note.
- **R06** per-paragraph speaker correction with "Not sure", rename-to-merge. **R03** retry one failed part.
  **N01** briefs link each task back to its paragraph. **N02** task states (done / not mine). **N03** rewrite chips
  in the keyboard. "Say this calmly" style with an insults-removed carve-out.
- Reminders ring on the alarm stream, played by indite itself (this ROM stores a USAGE_ALARM channel as
  USAGE_NOTIFICATION), and stop on Stop, Done, Snooze, swipe-away or opening the app.
- Delete asks what to delete: audio, text, or the whole note.
- 22 unit tests (was 14), `docs/PRD.md`, and the audit register (37 findings).

### The Mac app now (15 Oct, 19:00) — read this before the older Mac notes below

**Start here: `docs/MAC_PLAN.md` §0** (done / pending / future), **`mac/README.md`** (what it does, how to run it),
and **`docs/MAC_TEST_PLAN.md`** (what was tested automatically, and 32 tests B1–B32 the founder runs by hand).

| | |
|---|---|
| Run (your Mac) | `./mac/build_app.sh && open dist/indite.app` (a launcher for this folder) |
| Share | `./mac/build_share.sh` → `dist-share/indite-mac.zip`, 624 MB, Apple Silicon, unsigned (right-click → Open once). Own Python, libraries, models; no personal data, no logins |
| Window | Dictations · Meetings · Files · To do · Dictionary · Settings (General, Look & sounds, Writing, AI, Privacy, Backup) · Help |
| Code | `indite_mac.py` (keys, mic, engine, files, AI calls, who-spoke), `meeting.py`, `system_audio.py`, `speakers.py`, `ai.py`, `digits.py`, `store.py`, `window.py`, `overlay.py`, `ui/app.html` |
| Checks | `tests/test_mac_handsfree.py`, `tests/test_mac_pieces.py`, and `python mac/<store,ai,digits,meeting,speakers>.py` |
| See the real window | write a tab (`settings:ai`, `home`…) into `~/Library/Application Support/indite/snapshot.request`; a PNG appears beside it (needs Screen Recording) |

**⚠ Lessons from today, each cost time:**
- **A normal (Dock) app's panels cannot appear over another app's full screen.** indite is a normal app only while its window is in front, else menu-bar only.
- **The first engine start on a new Mac takes ~63 s** (GPU code compiled once), 3 s after. The app waits 2 min and says so.
- **The engine had a library path from this Mac baked in** (with a space in it). `build_share.sh` strips it and refuses to finish if one remains.
- **`sherpa-onnx` needs `sherpa-onnx-core`** or its runtime library is missing.
- **Python's stdlib has a `numbers` module**: the digits pass is `mac/digits.py`, never `numbers.py`.
- **WKWebView ignores `confirm()` and `prompt()`**: use native dialogs or inline forms.
- **A Finder-launched app has a bare PATH**: `ai.py` adds `~/.local/bin` so `claude` is found.
- **AI uses the founder's personal Claude account**, signed in on this Mac. Settings → AI shows which account is
  signed in, so it is never a surprise; AI is off by default for new users.
- **A class defined in `indite_mac.py` is defined twice** (it runs as the program and `window.py` imports it again):
  Objective-C refuses the second copy. NSObject subclasses go in `window.py` / `overlay.py`.
- **Opening a running indite did nothing visible**, so it looked dead: the window now shows whenever the app is
  activated (Finder, Spotlight, Dock).
- **indite had no app menus**: full screen's top bar was empty and ⌘C/⌘V did nothing in the window. `window.main_menu`
  adds indite / Edit / Window; Quit goes through `quit_all` so the engine stops too.
- **Menu-bar-only mode on "window lost focus" stranded the window when leaving full screen** (grey buttons). It now
  follows the app losing focus (`Activation.resigned_`).
- **Fading the pill's glass froze its view of the background.** The glass stays at full strength; transparency is a
  tint drawn under the text (`pill_clear`, 0–100 % in 10 % steps). Check with `pill:<0-100>` in `snapshot.request`.
- Who spoke now runs by itself after files (≥20 s) and meetings; Settings → Writing → Find who spoke.
- **⚠ Screen & System Audio Recording is NOT granted to indite** (log line "screen & system audio recording
  allowed: False", 15 Oct 20:55). Meetings therefore hear only the mic, and the demo video cannot record. A window
  snapshot of the desktop looked fine only because wallpaper and own windows need no permission. The founder may
  have enabled it for `dist-share/indite.app` (a different signature) instead.
- **⚠ macOS switches off a slow key listener and pynput never turns it back on** — the founder's shortcuts died
  after a settings change. Key handlers only change state; mic work runs on `self.ops` (one worker, in order);
  `listen()` restarts the listener on a "tap disabled" event. Keep anything slow out of `on_press`/`on_release`.
- **⚠ SOLVED 16 Oct - the app was breaking its own signature every single run.** Python writes `.pyc` files
  beside the modules it imports, and the interpreter lives inside the bundle, so each run wrote bytecode into
  `Contents/Resources/python` (249 files found) and broke the seal. macOS judges Accessibility on that signature, so
  it switched itself off mid-session: the log shows `allowed: True` ... `key listener was switched off by macOS` ...
  `not trusted` ... `allowed: False`. A reboot only looked like the cause - that is when macOS re-checks.
  **Fixes:** `PYTHONDONTWRITEBYTECODE=1` in `run.sh` and `build_app.sh`; `build_app.sh` clears stray `.pyc` before
  signing and refuses to call a build good if the seal does not verify; `signature_broken()` checks at start-up and
  says so loudly instead of letting the keyboard die quietly. Verified: the signature now survives a full run.
  **The one trigger left is rebuilding**, because ad-hoc signing derives identity from content. Either rebuild only
  when the bundle itself must change (code lives outside it, so code changes need only a restart), or create a local
  signing certificate for a stable identity - the founder's call, it adds a certificate to the keychain.
- **Ad-hoc signing + rebuilds can drop a privacy permission**: after `build_app.sh`, check the log line
  "screen & system audio recording allowed". If False: remove indite from that list (−), add `dist/indite.app` (+).
- **Your app now carries its own Python** (`build_app.sh` copies the interpreter into the bundle). Reason: macOS
  checked Screen & System Audio Recording against the interpreter *outside* the app, so the switch for indite
  never applied. After this one change Accessibility and Screen Recording must be granted again, once.
- **⚠ The app's executable must stay alive as Python's parent** (`mac/launcher.c`, compiled by both build scripts).
  With a shell script that exec'd Python, Screen Recording was credited to indite but Accessibility was judged
  against Python itself, so key access stayed False with indite switched on. Every rebuild re-signs ad hoc and
  resets both permissions: rebuild only when the bundle itself must change (code changes need only a restart).
  A local signing certificate would stop the resets; it needs the founder's OK (it adds a trusted certificate).
- **⚠ Key access finally works (15 Oct, 21:50); the real blocker was a crash, not the permission.** Once keys reached
  indite, pynput read the keyboard layout from its listener thread; macOS 26 demands the main thread and killed the
  app silently (SIGTRAP, `dispatch_assert_queue`). Fix: `_layout_on_main_thread()` in `indite_mac.py` reads it once at
  start-up and hands pynput that copy, so **pynput is pinned to 1.8.2** (the patch reaches into its internals).
- **⚠ Media keys crashed indite (18 Oct):** pynput turns volume/brightness/play keys into an NSEvent on its own thread
  (`keyboard/_darwin.py:303`), which macOS 26 aborts. `_skip_media_keys()` drops those events first; keep it with the pin.
  The log's old "Accessibility" line was checking **Input Monitoring** (`CGPreflightListenEventAccess`), so it read
  False even with Accessibility on. `can_listen()` (log, menu ⚠, window banner, prompt) now checks Accessibility, plus `faulthandler` writes a Python stack into the log on
  any crash. Rules: after a crash, read `~/Library/Logs/DiagnosticReports/python3.12-*.ips` before blaming a
  permission; Accessibility True + Input Monitoring False is the working state.
- **A frozen indite copy (pid 99097, status `T`) can't be killed, even outside the sandbox.** Likely the company's
  security agent (unproven: its logs need admin). It makes a normal `open` fail (-1712) and Dock clicks go to it, so
  the window "doesn't show". Until the Mac restarts: start with `open -n dist/indite.app`, show the window with
  `echo open: > ~/Library/Application\ Support/indite/demo.cmd`. `launcher.c` now stops waiting on any error but
  an interruption (source only; takes effect at the next rebuild, which resets permissions).
- **Ask AI is a side panel** (`openDrawer` in `ui/app.html`): answers first, then actions; new "Ask anything" action
  (`custom` in `ai.py`). The note list shows only "AI · n answers".
- Logo: `mac/brand/logo.svg` (five voice bars, the middle one is the letter i) → `indite.icns` in both builds.
- **Demo video** (`mac/demo.py`, `mac/recorder.py`, `mac/demo_make.py`): runs against a demo profile
  (`open --env INDITE_DATA=<folder> dist/indite.app`), started by writing `run:<out_dir>` into that folder's
  `demo.cmd`. Synthetic key presses from the runner work (it inherits Accessibility); screen recording must happen
  inside indite (`rec:` command) because a child process is refused. `say` can freeze: clips are made first, with
  timeouts. Hidden apps are restored in `finally` (needs a run-loop spin to take effect).
- **Insights** page (sidebar): words, this week vs last, speed, time saved vs typing at 40 wpm, 12-week activity,
  14 days, by app, by hour, meetings/files/wait.
- **The text card was one line + "…"**: it now wraps, grows to ~14 lines and stays 4–15 s by length. Check it with
  `preview:<text>` in `snapshot.request` (writes `snapshot-preview.png`).

### The Mac app (15 Oct)

`mac/indite_mac.py` plus `overlay.py`, `window.py`, `store.py`. Hold a key anywhere, speak, let go, and the text is
typed into whatever app has focus. Same window rule as the phone.

**⚠ The Mac and Android apps are kept separate (founder, 15 Oct).** Neither reads the other's folder. The Mac has its
own model (`mac/models/`, a hard link to the phone's file, so no extra disk; git-ignored) and its own `mac/spelling.tsv`
(started as a copy of the phone's). A change to one app's model or spelling cannot change the other. Only the
whisper.cpp tools in `.tools/` are shared, and Android builds its own copy from source.

| | |
|---|---|
| **Speed** | **0.75–0.89 s** per 3–8 s sentence, measured 15 Oct. Was 1.2–1.5 s when every sentence reloaded the model |
| How | `whisper-server` on 127.0.0.1:8711 keeps the 574 MB model in memory; the per-sentence binary is the fallback |
| Typing | synthetic key events carrying up to 20 characters each, so **nothing touches the clipboard** (the phone's bubble has to, and that is its one real privacy cost). One-per-character typing made long dictations crawl into Chromium apps; see `docs/research/mac_typing_speed_2026-10-16.txt` |
| Feedback | a floating pill: voice bars while held, "writing…", a tick when it lands |
| Window | history grouped by day, searchable, one-click copy, words/minute and a day streak; settings for the hotkey, typed-or-copied, Hinglish spelling, and whether history is kept at all |
| History | capped at 500 lines in Application Support — an unbounded log of everything said is a liability, not a feature |
| Build | `./mac/build_app.sh` → `dist/indite.app`, ad-hoc signed so the Accessibility tick survives a rebuild |

**⚠ The permission lesson, three times over.** macOS gives no key events to an untrusted process and pynput fails
silently, so the first build looked healthy and did nothing. The permission attaches to **the app that launched the
script** — Terminal, or Claude, or iTerm — which is why granting it to a python binary never stuck, and why the
bundle exists. The app now checks at startup and names what to add.

**⚠ The project moved on 14 Oct** from `~/Desktop/Personal/Cowork/Voice to Text` to `~/Projects/indite`, because a
new app cannot read `~/Desktop` (macOS protects it) and the bundle could not reach its own Python. A symlink keeps
the old Desktop path working. All paths in the repo were relative, so nothing else changed.

### Mac fixes (15 Oct, afternoon)

- **A mic that will not open no longer kills the hotkey.** The default input was a Bluetooth headset that was off
  (PortAudio -9986); the error killed the key listener. Now it tries the last mic that worked, the default, the
  built-in, then any input; if none opens, the pill and a popup say why. **Founder tested with the headset off: works.**
- **Leftover engines.** A killed or crashed app left `whisper-server` running (three found, 574 MB each). The app now
  clears any old engine on port 8711 at startup. Checked with `kill -9`, then relaunch: one engine.
- `build_app.sh` uses the real folder (`pwd -P`); run from the Desktop symlink, it baked in a path macOS blocks.
- **Built (untested by the founder):** your own word fixes — menu → "Edit my word fixes…" opens
  `~/Library/Application Support/indite/my_fixes.txt` (`heard = wanted`, whole words, multi-word OK, read on every
  dictation; check: `.venv/bin/python mac/store.py`). **Esc while holding cancels** (pill: "cancelled"); Esc also
  reaches the app underneath, pynput cannot block it.
- **Long holds were broken, now fixed (measured 15 Oct, clean synthetic clips, local server):**

  | Hold | Before: one request | Full window only | **After: cut at quiet points (≤20 s pieces)** |
  |---|---|---|---|
  | 33 s | 31.2% wrong, 10.4 s | 18.2%, 5.5 s | **16.9%, 3.6 s** |
  | 62 s | **75.4%**, 21.5 s | 18.3%, 8.5 s | **19.0%, 7.3 s** |
  | 93 s | 53.5%, 28.9 s | 46.0%, 14.7 s | **19.7%, 10.7 s** |

  Same sentences sent one at a time: 19.0%. With no gaps between sentences: 19.5% (60 s), 22.8% (90 s).
  `pieces()` keeps every sample and cuts in the quietest 0.3 s between 15 and 20 s; no voice detector (torch took
  19 s to import). Test: `tests/test_mac_pieces.py`. **Untested:** real non-stop speech and a quiet speaker.
- **New window design (15 Oct), design-critic reviewed:** white page, glass sidebar, three stat tiles (words,
  speed, wait; the streak was removed, as ROADMAP rules out streaks), history with an always-visible copy icon,
  Settings in Dictation / Writing / Privacy cards with a Word fixes row, Help as three steps plus fixes. Every grey
  passes WCAG AA on white. "Clear history" used `confirm()`, which a WKWebView ignores, so it never deleted
  anything; it is now a native NSAlert. The window opens on launch.
- **Pill:** 116 x 30 and on macOS 26 real Liquid Glass (`NSGlassEffectView`), falling back to the blur before 26.
- **"nan" was typed into apps:** the model writes "nan" for silence; a piece that says only that is now silence.
- **Android + Wispr comparison and plan: `docs/MAC_PLAN.md`** (critic-reviewed). Built from it: password-box guard
  (subrole `AXSecureTextField`, every mode), fix a word from a history row, "Transcribe a file…" opening the web app,
  a Help line for Login Items. Waiting on the founder: hands-free, AI actions (see the PATH catch in the plan).
- **15 Oct evening: phases 1–5 built** (MAC_PLAN §3 R1–R32): notes with stars, To do page, files transcribed in
  the app, AI on notes via own `claude` (PATH fixed for Finder launches), improve-with-original, meeting recording
  (mic + ScreenCaptureKit system audio, `mac/meeting.py`), who spoke (`mac/speakers.py`, sherpa-onnx + TitaNet; needs
  the `sherpa-onnx-core` package or onnxruntime is missing), backup/restore, first-run setup, accuracy passes
  (`mac/digits.py`; spelling punctuation bug). **Not yet checked in real use:** meeting audio with the permission
  granted, full screen, drag strip, hands-free key/taps. **Next:** a shareable signed build (R20).
- **Founder's requirement list R1–R24 is in `docs/MAC_PLAN.md` §3 and now drives the Mac app** (he overruled the
  earlier drops). Done: clear glass pill with border and writing animation, drag strip, hands-free, ⌃⌘V paste last,
  sounds, mic picker. Next phase: notes with stars, to-do mark and page, files transcribed inside the app. **Built vs planned is
  tabled in MAC_PLAN §3 — keep it honest; the founder asked whether things were built or only shown.**
- The app log was empty because Python buffered its prints; the launcher now runs `python -u`.
- **Next Mac features (critic-reviewed, all unproven):** later snippets and hands-free (long holds now work); drop undo-by-backspace, voice "press enter",
  command mode (no AI route). Waiting on the founder to say what they actually miss from Wispr.

### Waiting on the founder

1. **Back up `~/.indite/indite-testers.keystore`** — still one copy. Everything else here is reproducible; this is not.
2. **A new OpenRouter key** (the old one was disabled). No AI feature has ever answered on the phone.
3. **The ₹15k phone** — accuracy and speed on cheap hardware, never measured. Still the biggest unknown.
4. **The 681 MB install** — 34 minutes over a cable is a long download on mobile data. Gate for a smaller model is
   set: "if quality doesn't decrease" (15-min ≈ 25%, clean ≈ 13%).
5. Hand check of everything built since build 15; the model licence question is **closed**: Apache 2.0, commercial
   use allowed (verified on the model card and Oriserve's announcement).

### Known environment problems

- **USB drops constantly** (7 times on 14 Oct). Push + install makes this survivable; long live tests still need luck.
- **Mac disk**: 2.4 GB of old speed-test APKs deleted from `phonetest/` and `APK/` on 14 Oct (the 28 MB of test audio
  and 44 other files were kept). 4.3 GB free afterwards. Gradle's daemon died twice when it was under 2 GB.

---

### Next build scope

**Remaining features, split (critic-reviewed 10 Oct):**
- **A · next build (~16–20 h), only after build 10 passes the hand check:** Show only [name]; recovery banner; space
  left while recording; speed line; find & replace in a note; search jumps to the paragraph; WhatsApp date titles; one
  permissions checklist. If time: "Your data" screen, merge speakers.
- **B · after a gate:** try-it onboarding, model download on first open, targetSdk raise, Play internal testing (gate:
  ₹15k phone passes; each gets its own phone test) · battery check (measure on build 11) · voice "Me" (tester asks +
  consent text) · overlap marking (3 real recordings lose > ~3% words) · speaker listen-check (founder first) ·
  deletion time, other Indian languages (tester sign-up answers) · per-phone benchmark (≥1.5x gain) · web speakers,
  Windows (phone stable, Windows PC) · remove personal-only features (Play launch).
- **C · not building:** ChatGPT login in-app (not allowed), Google login (needs hosting), own translation/speak aloud
  (too slow, no asks), dictation ≤3 s / own models (no offline path), "more use cases" (research), licence & logo
  (founder decisions).
- Rule: one batch per build; quick test after every build, phone < ~36 °C, untouched.

---

## 5b. Where the code and builds live (repo status)

| Place | What's there | State (15 Oct, night) |
|---|---|---|
| **GitHub** `github.com/vaibhavk93/Indite` (PUBLIC, branch `main`) | Source, docs | **Pushed 15 Oct night** (`aad93dc` and this doc fix), incl. tags `build-7`…`build-10`. Push again when the founder says so |
| **Local repo** (this Mac) | Everything, plus git-ignored files: models in `android/app/src/main/assets/models/`, `android/app/libs/sherpa-onnx-1.13.8.aar`, `.tools/` (JDK, whisper.cpp), test audio, old APKs in `phonetest/` and `APK/` (~2.4 GB, OK to delete pending) | HEAD = latest commit; tags `build-7`…`build-10` mark builds installed on the phone |
| **Mac app builds** | `dist/indite.app` (yours: launcher + its own Python, code runs from this folder) and `dist-share/indite.app` + `indite-mac.zip` (shareable, self-contained). Both git-ignored | Rebuilding resets Accessibility and Screen Recording (ad-hoc signing) |
| **Founder's phone** (OnePlus CPH2573, USB) | Personal build 0.10 (build 10) + the rounding A/B hook | Notes live only on the phone (no backup). Export via Settings → Storage |
| **Signing key** `~/.indite/indite-testers.keystore` | Same key for every build (updates install over the old app) | **Only copy is on this Mac: founder to back it up** |

---

## 6. How to hand off (end of every session)

1. Update section 5 above.
2. Add an entry to `docs/WORKLOG.md`: date, who (Claude Code / Codex, which account), what changed (commits), what's
   untested, what's next.
3. Update `ROADMAP.md` **and** the roadmap page if anything was built, decided or dropped; update `docs/FOUNDER_REQUESTS.md`.
4. Commit (founder's no-reply email). Tag any build that got installed on the phone: `git tag build-YYYYMMDD-N`.
5. Leave a one-line "next step" at the top of the WORKLOG entry.
