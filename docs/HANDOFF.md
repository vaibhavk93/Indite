# indite handoff

**Read this first.** It lets any Claude Code or Codex session (or a different account) continue the work. Keep it current:
update "Where things stand" and add a dated entry to `docs/WORKLOG.md` at the end of every session.

Last updated: 2026-10-10.

---

## 1. What indite is

Offline, private Hinglish speech-to-text. Speak Hindi + English, get Roman-script text ("kal meeting hai").

| Part | Where | State |
|---|---|---|
| **Android app** (main product) | `android/` | v0.6+, on the founder's OnePlus 12 |
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
- No in-app Claude/Gemini/ChatGPT login (terms). No own reminders/to-do app (hand off to Calendar / Clock).
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

- **Fixed in code 10 Oct, NOT built and NOT heard yet** (no Android SDK, no model assets and no signing key in the
  cloud container, so nothing here was compiled). The founder reported: "alarm is not giving me sound", "the
  translations are not working", and "making formal statement out of the context I have shared" does not work.

  **Why the reminder was silent — ranked, with what is actually proven** (critic-reviewed; the first theory was wrong,
  see below):
  | Rank | Cause | Proven? | What changed |
  |---|---|---|---|
  | 1 | **"Ring like an alarm" defaulted to OFF.** So every reminder was a 2.6 s chime on the *notification* stream, which silent/vibrate mode, Do Not Disturb and a low notification volume all mute. Founder request #84 was "alarm-like sound"; it shipped as an opt-in switch, off, inside Settings | Code-proven (`Reminders.ringLikeAlarm` default was `false`). That it is what *he* hit is the best guess, not proven | **Default ON.** The alarm path is now the channel's own sound with `USAGE_ALARM` + `FLAG_INSISTENT`: alarm stream, alarm volume, repeated by the phone until the notification is seen, through silent mode and through DND wherever DND allows alarms |
  | 2 | **POST_NOTIFICATIONS may be denied.** indite asked for it only when recording or importing, never when a reminder was set. Denied = nothing appears and nothing sounds | Code-proven (`MainActivity.askNotificationsOnce` is called from `record()` and `import()` only) | `RemindDialog` asks when it opens; `Reminders.show()` returns false when notifications are off, and `fire()` then does **not** mark the reminder `fired`, so it is not thrown away |
  | 3 | **OxygenOS force-stopped indite**, which deletes its alarms. Nothing in the app can stop this | Plausible, untested | Settings → Reminders now says so and opens the phone's battery setting (that button previously existed only under the floating-mic section) |
  | — | ~~The channel's sound URI used the numeric `R.raw.reminder` id, which AAPT2 moves between builds~~ | **Checked and false.** `reminder.wav`, the channel ids and `setSound` all arrived in one commit (`3d42717`) and `res/raw` is unchanged since, so the stored number still resolved | The URI is named anyway (`.../raw/<entry name>`, via `getResourceEntryName`, which also keeps a code reference so resource shrinking can't strip the WAV). Channel ids went to `_v2` because a channel's sound is frozen at creation — needed for the `USAGE_ALARM` change regardless. **Next change needs `_v3`:** deleting a channel does not reset it, recreating the same id restores the old settings |
  | — | A missed reminder re-announced itself on every app open | Code-proven (`rescheduleAll` notified every past reminder, with nothing marking it done) | `fired` flag in `reminders.json`; shown once, quietly |
  | — | No way to test the sound without waiting for 5 pm | — | Settings → Reminders: **Test the reminder sound** + Stop; `soundProblem()` names the blocking phone setting (notifications off, channel blocked or muted, silent/vibrate, notification volume 0, DND, alarm volume 0); "Last reminder: …" records what happened the last time one fired |

  **A foreground service that played the alarm itself was written and then deleted.** The critic was right that it was
  over-engineering: it could lose a reminder (it marked `fired` before the notification was confirmed) and opening
  indite removed its own ongoing notification. The channel route does the same job with the system playing the sound.
  Add a player back **only** if a device test shows the phone cutting the channel sound short.

  **Why Translate did nothing useful:**
  | Cause | What changed |
  |---|---|
  | *Ask my AI → Translate* called `ask("Translate")` with no language, so `{lang}` became **English** — and the Hinglish reply rule was already skipped, so a Hinglish note came back looking almost unchanged | Translate in that list now opens the language picker |
  | The one route that needs no key and no internet (the Google Translate app) was the last line of a scrolling dialog | It is the first button when the app is installed (`<queries>` for that one package so `installed()` can ask) |
  | **The real block: no AI route exists on this phone.** `MacCompanion` needs a Tailscale URL + token, `OpenRouter` needs an `sk-` key + a model; both are still waiting on the founder. So every AI request can only hand the text to another app and wait for a paste | Settings → AI prints one line (`aiRouteNow()`) saying exactly what will happen. ⚠ **An OpenRouter key is the single highest-value thing the founder can do**: it makes Translate, Formal version and every other request answer inside indite today |
  | ~~Android 11+ package visibility made `startActivity(setPackage(…))` throw~~ | **False.** Google's docs: `startActivity()` does not require package visibility, for implicit or explicit intents. Filtering hits *queries* and starting another app's *service* |

  **"Formal statement" did not exist.** Added as **Formal version** in `AskPrompts`: formal English, every fact / name /
  number / date kept, nothing invented, "(unclear)" where it can't tell. It and Translate are in `OwnLanguage`, so the
  "reply in Hinglish" rule is not applied to them (that rule would have wrecked a formal English statement).

  **Open question only the founder can answer:** when the reminder was due, did it appear on screen with no sound, or
  did nothing appear at all? Silent-but-visible points at cause 1; nothing at all points at 2 or 3.

  **To verify (on the Mac):** build 11 → Settings → Reminders → Test the reminder sound with the switch ON, then OFF →
  one real 2-minute reminder with the phone locked → one Translate → one Formal version. `adb shell dumpsys alarm | grep
  indite` and `adb shell dumpsys notification --noredact` after a test answer most of the rest.
- **Speaker labels now run by themselves (10 Oct, code only, not built):** the founder asked why diarization was not
  automatic. Answer: **nothing ever decided it had to be manual.** It was built as an on-demand action (`ui/NotesApp.kt`
  card "Was this a conversation? Find who spoke.") and request #60 removed the *count* question but left the tap. There
  was no technical blocker: PLAN.md line 230 records **15.9 s on the phone for a 15-minute file** (~1 s per minute of
  audio), against minutes for transcription.
  | Change | Where |
  |---|---|
  | `NoteService` labels every note it just finished, once the queue has nothing left to transcribe (so a live dictation is never delayed), inside the foreground service (so Android does not kill it half-done), after `waitUntilSafe()` (heat/battery), and bails out if a recording starts | `notes/NoteService.kt`: `finish()` → `toLabel`, `wantsLabels()`, `labelFinished()` |
  | Gate: over 60 s, 2+ paragraphs, no speakers file yet, **not a `test` note** (so `phone_test.sh`'s `--ei k 2` scoring stays clean). Only notes *this run* finished — never a sweep of the whole back catalogue | `wantsLabels()` |
  | `Speakers.labelAuto()` + `Speakers.status` (a `MutableStateFlow`, because `Speakers.running` is not observable, so the note screen could not show a run it did not start) | `notes/Speakers.kt` |
  | **One voice = no labels at all**, however the run started. An explicit "1" used to write "Speaker 1" on every paragraph; now `heardOne()` saves `skipped=true, k=1, guessed=<indite decided>` and the note screen shows a one-line "indite heard one voice. Two people spoke?" only when indite decided it | `Speakers.label()`, `heardOne()`, `NotesApp.kt` |
  | The existing "indite heard N people. Is that right?" card is the founder's "ask and update later" — unchanged | `NotesApp.kt` |
  ⚠ **The count guess is unmeasured on real audio.** PLAN.md line 230 says "auto count fragile on real audio", and
  `phone_test.sh` only ever scores a *given* count (`--ei k 2`). The 96.7% / 93.3% figures are given-count numbers, not
  guess numbers. Before testers: score the guess on the 3 real recordings (ROADMAP "Now" 3), and measure the battery
  and heat cost of auto-labelling a 15-minute import. If either is bad, add a switch (the hook is one `if`).
  No setting was added on purpose: the cost is small and nothing waits on it.
- **Installed on the founder's phone:** build 10 (0.10, tag `build-10`), personal flavour.
- **Pushed to GitHub:** everything up to the evening of 10 Oct (and build tags).
- **Engine consistency (fixed 10 Oct, needs phone confirmation):** same audio gave different text because flash attention
  read audio-cache rows left over from the previous piece. Fix: `Pauses.audioCtx` always a multiple of 256, max 1280
  (`Pauses.FULL`); never pass 0. Mac: 15-min file 10/39 → 39/39 parts repeatable, 27.6% → 24.7%. Turning flash attention
  off also fixed it but cost ~6 s per live sentence (build 8 test: 9.1 → 14.8 s), so it stays on.
- **Last phone tests:** build 7 full: speakers 96.7% / 91.7%, live 9.1 s median, 16.5% WER, 15-min 28.7%.
  Build 8 quick: speakers 98.3% / 93.3%, live 14.8 s (flash off; reverted).
- **Next:** `QUICK=1 ./bench_synth/phone_test.sh` on build 10 (gate: live median ≈ 9 s), then the full run (gate: 15-min ≈ 25%).
- **Built in builds 9–10, waiting for the founder's hand check:** indite's own reminders (exact alarms, chime + nudges,
  optional ring-like-alarm, Settings → Reminders); one-switch floating mic (✕ drop zone, quick settings tile, magnetic ✕,
  spring snap, remembered position; personal: accessibility shortcut toggles it); cards with border + copy button +
  long-press menu with icons + sticky day headers; swipe hint animation (Settings → Look & feel → Tutorial); keyboard
  redesign (orb, halo, level bars, springy keys); password/PIN guard (shared `notes/Secret.kt`); delete paragraph + Undo/Redo;
  Settings in 7 groups (incl. Reminders); italic subtitle (real Figtree italic).
- **Accepted, not built:** "Show only [name]" filter; voice "Me" (behind consent + privacy text); value-adds top 8
  (recovery banner, speed line, "Your data" screen, space while recording, merge speakers, find & replace, WhatsApp date
  titles, search → paragraph).
- **Deferred with a plan:** overlapping speech (record 3 real conversations first); other Indian languages in Roman script
  (ask script on tester sign-up first); OpenRouter (no key yet); iPhone (5+ tester asks).
- **Build 10 quick test (16:30):** live wait **17.3 s median** (build 7: 9.1 s) though engine time per part is only +6%
  (8.7 → 9.2 s) and threads are 6 as before; live speed 1.03x vs 1.20x. Speakers 96.7% / 93.3%. Cause not known yet:
  re-running the quick test to check run-to-run noise; if still slow, A/B against build 7.
- **Build 10 quick test, run 2:** live wait 12.0 s (run 1: 17.3 s) on the same build; phone 39.8-40.2 °C vs 35.8 °C for
  build 7; live WER 20.2% (run 1: 16.9%). Live numbers swing a lot run to run (cut timing + heat).
- **A/B result (10 Oct, 4 live rounds, phone 35-37 °C): keep rounding 256.** 256: wait 9.1 s / 14.1 s, engine 8.7 / 9.0 s
  per part, 21 parts, WER 20.4% both runs (repeatable). 64 (old): wait 78.8 s / 87.3 s, engine 14.3 / 15.2 s, only 11
  parts (engine fell behind, recorder switched to long pieces), WER 17.9% both runs. Likely cause (unproven): leaked
  rows garble pieces, the live dropped-text re-run then runs 2-3x. Heat matters: +0.9 °C ≈ +5 s wait.
  Next accuracy item: live WER (cut points), not rounding.
- **(done) A/B speed test of the audio-window rounding** (the only live-path engine change between build 7 and 10).
  Hidden personal-build hook `--ei test_round 64|256` (`Pauses.round`, in memory only). Script:
  `cd bench_synth; ROUND=256 LIVE_ONLY=1 ./phone_test.sh` then `ROUND=64 ...`, alternating, 2 rounds each, phone below
  ~36 °C at the start, untouched. Decide: if 256 is clearly slower live, use 256 only for imports (consistency) and 64
  for live; otherwise keep 256 everywhere.
- **Added after build 10 (committed, not installed):** Mac route can answer with ChatGPT via the founder's own Codex CLI
  (`via` in `/api/ask`; Settings → AI → Your Mac); Settings → Your stats dashboard (on-phone counts only).
- **ChatGPT login inside the app:** not allowed yet (OpenAI's "Sign in with ChatGPT" = application-only preview, no mobile;
  reusing Codex's login would impersonate OpenAI's client). Founder to apply to the programme.
- **Founder's checklist of every request:** `docs/FOUNDER_REQUESTS.md` (175 items).
- **Waiting on the founder** (highest value first): **an OpenRouter key** — a 2-minute signup that makes Translate,
  Formal version and every other AI request answer inside indite, instead of handing the text to another app; then the
  answer to the reminder question above; hand check of builds 9–11; phone free for the quick test; Tailscale (the Mac
  route, harder than the key); back up the signing key; OK to delete ~2.4 GB of old APKs; ₹15k phone; "push".

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
