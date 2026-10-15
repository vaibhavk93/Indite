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
1. `ROADMAP.md`: **the one roadmap** (built / now / next / later / not doing / founder requests with status). The page
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

**Repo rules:**
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
| Typing | character by character, so **nothing touches the clipboard** (the phone's bubble has to, and that is its one real privacy cost) |
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

| Place | What's there | State (10 Oct, evening) |
|---|---|---|
| **GitHub** `github.com/vaibhavk93/Indite` (PUBLIC, branch `main`) | Source, docs | **Pushed** (10 Oct evening), incl. tags `build-7`…`build-10`. Push again when the founder says "push" |
| **Local repo** (this Mac) | Everything, plus git-ignored files: models in `android/app/src/main/assets/models/`, `android/app/libs/sherpa-onnx-1.13.8.aar`, `.tools/` (JDK, whisper.cpp), test audio, old APKs in `phonetest/` and `APK/` (~2.4 GB, OK to delete pending) | HEAD = latest commit; tags `build-7`…`build-10` mark builds installed on the phone |
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
