# Work log

Newest first. One entry per session: date, who, what changed, what's untested, next step. See `docs/HANDOFF.md`.

---

## 2026-10-17 (22:35-23:05) · Claude Code (Opus 5.5) · Rest of the Mac roadmap, copy review

- Built and tested (unit tests, self-checks, headless Chrome renders, the new hidden test copy): card buttons in
  Settings; meeting clock + Both tracks; word-time healing; paused dictations keep the lit word; test copy;
  Record this call?; own hidden words; setup step 5; line speaker fix + join with Undo; speech-test tools.
- Bugs found and fixed: card-button reload code had landed inside start-up (would not apply until restart);
  word times saved as all-zero when the engine was busy; word times kept after a fix changed the word count;
  a test leaked a fake thread maker into later tests; "Nothing to join" wording.
- Mistakes of mine, fixed: a plain `open` reached the test copy (founder's indite down ~30 s; now `open -n -g`);
  running the bundled Python wrote .pyc files into the app and broke its signature (warning shown once; removed,
  signature valid, app restarted). Both are in HANDOFF.
- Copy: independent agent reviewed every UI string; 12 must-fixes and most should/nice items applied. 17 tests pass.
- Answered: Wispr cleanup levels without AI (None yes, filler words yes, grammar/clarity/polish need a model).

## 2026-10-17 (22:30) · Claude Code (Opus 5.5) · Listen view restyled to indite's own look (#283)

- Listen panel now matches the note list: gutter, `.who` speaker colours, 14 px text, hairline rows, icon actions on
  hover, a grey player strip with SVG play/pause and a thin orange-fill slider. Playing line = `--well` (no orange box
  or bar); spoken word = `--accent-soft`. Hint text was centred by a CSS clash: fixed. New pattern in `docs/DESIGN.md`.
- Off-screen check: headless Chrome render of `app.html` with made-up notes (light + dark, dictation + meeting), no
  page errors. Live page reloaded in the background via `js:location.reload()` (no restart, no focus).
- Test fix: `test_mac_handsfree.py` replaced `threading.Thread` for the whole run, so 2 later tests failed when the
  files ran together. Now restored after each test. 13 pass (`uv run --with pytest pytest tests/test_mac_*.py`).

## 2026-10-17 (15:00-17:15) · Claude Code (Opus 5.5) · Card, clipboard, Insights, Mark likely mistakes, one roadmap

**Next step:** Mac next #4 (fixes count), #5 (engine-hint test), #7 (edit + undo); founder's 30-min checks (Mac next #2).

- Card: Ask AI + the two most-used AI actions + To do; copy icon tried and removed at the founder's call; answers wrap.
- Clipboard: typed words also copied; every AI answer copied (tested end to end in TextEdit: dictation, card
  Rewrite · Formal, Ask AI Summary).
- Insights: a rebuild was rolled back on founder feedback; the original page grouped into 4 sections + 4 KPIs.
- Copy: one icon on notes and answers; meeting copy/export use renamed speakers (bug).
- Mark likely mistakes built and tested end to end ("crasin" → Fix → "Crocin"). Found on the way: confidence comes
  in word pieces (merged now), and the second listen can differ from the typed text (flags now come from the text).
- ROADMAP.md rewritten as one file (Mac / Android, done / next / later / parked); 10 Oct sections archived; an audit
  of all requests, commits and chat logs added 11 missing items and 8 founder decisions.

---

## 2026-10-17 (14:40) · Claude Code (Opus 5.5) · Text card AI buttons; crash fix; context-safe fixes planned

**Next step:** founder dictates, hovers the card, clicks Make it a prompt - confirms the click-through works.

- Crash fixed: `window.py` add_fix refusal called `self.bridge.js` inside Bridge (from `3c9ba16`); now `self.js`.
- Text card (`overlay.Preview`): 3 buttons, clicks only while hovered (`_track`), `working()` / `answer()` states;
  `App.card_action`; `_ai` sends the answer back to the card and the clipboard. Snapshot: `preview:+text`.
- `tests/test_mac_handsfree.py` was failing since `9b0c4a8` (no `preview` on the fake app); fixed.
- Critic on the founder's "same word, different context" worry -> ROADMAP Mac #7 and Android #4.

---

## 2026-10-16 (10:20) · Claude Code (Opus 5.5) · Two roadmaps, personalisation plan, recordings reachable

**Next step:** founder: demo decisions (length) and the real speech set; Android item 1 (key or Tailscale).

- Recordings: saved but unreachable. Added Play / Show in Finder to the note menu (`store.audio_files`, window
  actions `play`/`reveal`). Crashed the app once on the way (a local `import subprocess` later in the same handler
  shadowed the module import); fixed, pyflakes clean, Show in Finder tested.
- ROADMAP.md forward sections rewritten as two roadmaps + limits table + personalisation (critic-reviewed).
- Another session (founder's other account) commits in the same folder (81f8487, narrate.py only). Commit this work
  soon so it is not swept into someone else's commit.

---

## 2026-10-16 (09:50) · Claude Code (Opus 5.5) · Swear masking fixed; roadmap re-prioritised

**Next step:** founder confirms the demo decisions and length; the real speech set starts (ROADMAP Now 1-2).

- Swear masking: removed from `tidy()` (the saved text); `App.out()` masks typed/copied/previewed/exported text;
  `store.masked()` masks the window's copy of notes. Check added to `mac/store.py`. App restarted, no rebuild.
- Wispr comparison found in MAC_PLAN §6, ROADMAP_DETAIL, WISPR_DEEPDIVE; ~10 decided items were missing from
  ROADMAP.md. "Now" rewritten (9 items) after a critic: demo first with a code freeze; real speech set gates step 1
  too (~1 day, not 2 h); verbose_json and the Dictionary cap before step 1; C2 + W2 merged into step 1; W1/W3 after
  the demo. New "Parked" table (₹15k phone, Mac certificate, build 29 check, Android key backup + release key).
- Stale fixed: header date, Wispr row, "shading unsure words", language order; requests #236, #238, #240, #244.

---

## 2026-10-16 (03:10) · Claude Code (Opus 5.5) · Mac: back-to-back meetings + working dots built

**Next step:** founder tries two real calls back to back; check both notes and the "Others" track.

- Each meeting is its own object; Stop finishes in the background; Start waits only for the old one to let go of the mic.
- Found while testing live: every 2nd meeting in a session failed ("Out is overriding existing Objective-C class") -
  `SystemAudio.start` defined its class each time. Fixed (defined once). A failed start now closes the mic.
- `mic_trouble` now logs the reason (it only showed a pop-up, which hid the cause during this test).
- UI: dot on Meetings / Files / Dictations tabs (red = recording, grey = working; still under reduced motion);
  "Finishing the last words…" on the row.
- Tests: `tests/test_mac_meetings.py` (B keeps its first 2 s, A keeps all of its own); 11 Mac tests pass. Live test
  with sample audio: two meetings 14 s apart, each with only its own text. Snapshot checked.
- Four test meeting notes left in the founder's list (03:02-03:06).

---

## 2026-10-16 (03:00) · Claude Code (Opus 5.5) · Mac: back-to-back meetings planned; assistant idea tested on paper

**Next step:** founder's go-ahead on the meetings plan (founder request 251) and on the 7-day assistant test (252).

- Bug fixed: `Meeting.start` never cleared `segments`, so a 2nd meeting in one app session saved the 1st's lines too. Saved meetings unaffected (each was in a different session).
- Two races found, unfixed: after Stop, Start is allowed at once; the old `stop()` then calls `app.mic.stop()` (kills the new mic) and `pump(force=True)` (reads the new meeting's audio from the shared mic queue).
- Research: Granola admits back-to-back calls can merge; macOS 14+ lists which app holds the mic (poll; listeners reportedly don't fire). Anthropic forbids routing users' Claude plans through third-party apps (API keys only). WhatsApp bans automating personal accounts.
- Founder usage: 127 of 167 notes were typed into Terminal or the Claude app; Ask AI used 14 times.

---

## 2026-10-16 (02:30) · Claude Code (Opus 5.5) · Mac: stuck mic, for real this time; assistant question answered

**Next step:** watch the log for "restarting indite to get the microphone back" to confirm the self-restart works on a real lock-up.

- Pill showed, nothing recorded, right after a meeting. A live stack sample showed a deadlock between PortAudio's stop
  and CoreAudio's audio thread, and the next open waiting on the same device lock forever. The 16 Oct "abandon the
  stream" fix cannot recover this: only a new process can. Force-restarted the app.
- Fix (critic: adopt with changes): `MicStuck`; `Mic.start` waits at most 8 s; a stuck close or open marks the mic
  stuck; the next press restarts indite (detached `open -n`, then `os._exit`, since `sys.exit` would hang in
  sounddevice's exit hook), at most once per 10 min (`restart_allowed`), else an alert. Test added; 10 Mac tests pass.
- Untested: the restart on a real lock-up. Unproven: that meetings are the trigger (1 of 2 lock-ups followed plain
  dictation). Worth checking: whether a newer PortAudio (bundled one is V19.7.0-devel) fixes the cause.
- Founder asked: build a personal assistant (Slack/Gmail/Drive) into indite, or use Claude? Critic-reviewed answer:
  use Claude/Gemini; nothing new now. Added to ROADMAP "Not doing". WhatsApp pre-fill is the one gap, if testers ask.
- uv.lock synced to the pynput==1.8.2 pin already in pyproject.

---

## 2026-10-15 (late night) · Claude Code (Opus 5.5) · Mac: key access fixed; it was a crash

**Next step:** restart the Mac (clears the frozen copy), then the demo video. B22 (real meeting) still open.

- Founder removed and re-added indite in Accessibility; it now reads True. Three dictations typed fine.
- Root cause of "permission doesn't work": pynput crashed indite the moment keys arrived (keyboard-layout call off the
  main thread, macOS 26). Fixed by reading the layout once on the main thread; pynput pinned to 1.8.2.
- The log's Accessibility line was really checking Input Monitoring; now both are logged. Crashes now leave a Python
  stack in the log (faulthandler).
- A frozen indite copy can't be killed (probably the company security agent); window opened via `demo.cmd` meanwhile.
- launcher.c: no endless wait loop on errors (applies at the next rebuild).
- Ask AI panel (critic-reviewed): no redraw unless something changed (scroll, cursor, choices kept); answers
  formatted (headings, bold, bullets; action-item tables stay as pipes); long answers folded with Show more; Ask box
  pinned at the bottom; errors shown in the panel and cleared on the next ask; dictation into indite's own window is
  no longer saved as a note (process check, not app name). Settings → AI lists what AI unlocks vs what is offline.
- Round 2 (critic-reviewed): Ask AI beside the list when wide, highlighted note, no dim layer, 32 px close, three
  plain sections, own Rewrite/Translate menus, growing Ask box, full question kept as the title. Caught and fixed my own
  bug (empty list: the list read a variable before it existed). Full self-test passed (see MAC_TEST_PLAN Part A).
- Heard twice: "indite" transcribed as "in diet" / "In night" - a word-fix candidate.
- Round 3 (founder: "maybe worse"): Ask AI rebuilt after a critic (answers as documents, options on a sunken surface,
  one-click Rewrite/Translate chips, loading + ready/failed message, calm styling app-wide). Summary scales with the
  note; API limits raised (300 s, 4000 tokens; long meetings untested).
- Roadmap research (web + MAC_PLAN §6) critic-reviewed -> `docs/ROADMAP_DETAIL.md`; ROADMAP "Now" 6-7 updated.
- Round 4: pill-after-hide bug fixed (tested with indite hidden); Ask AI closes on page switch; AI usage in Insights +
  "With AI" filter; gold AI chip; "Make it a prompt"; meeting/file → AI warning; optional swear masking (critic-reviewed).

## 2026-10-15 (night) · Claude Code (Opus 5.5) · Mac: UX restructure, AI providers, shareable build

**Next step:** founder sends `dist-share/indite-mac.zip` to his boss; says what still feels bad in Settings; tries a
real call with the meeting recorder. Me: the dropped-sentence-end test (running), then P6 (local clean-up test).

- UX review → one job per page, Settings in six sections with a finder, "…" menu per note, Light/Dark/Like the Mac.
- AI: off for new users; Claude login (account shown, Sign in opens Claude's login) or API key in the Keychain.
- Pill over full-screen Terminal fixed (Dock-app panels cannot enter another app's full screen).
- Blank window found via a real-window snapshot; page watcher reloads it. Slider ran backwards; full-screen width capped.
- `mac/build_share.sh`: self-contained 624 MB zip; engine library path from this Mac removed; first start 63 s → app waits.
- Roadmap with done / pending / future: `docs/MAC_PLAN.md` §0.
- Dictations no longer shows the words/speed/wait line (Insights has it).
- Night 2: who spoke automatic, app menus + full-screen focus fix, live pill glass with 10 % steps, Insights page, demo-video runner (blocked: Screen Recording permission not actually granted — also means meetings hear only the mic).
- Text card multi-line + dynamic height; reopening shows the window; AI answers collapsed; Objective-C double-class crash fixed. `docs/MAC_TEST_PLAN.md`: Part A (tested by Claude) + B1–B32 for the founder.
- Dropped-ending test: one real case (s38, `no_timestamps` makes the model stop after the first sentence); the rest were test-file faults. Retry fix designed and measured, not built (tiny gain, junk risk). The long_15min reference timings need fixing.

## 2026-10-15 (afternoon) · Claude Code (Opus 5.5) · Mac fixes

**Next step:** founder names what they miss from Wispr; then build personal word fixes + Esc cancel, and test a 60 s hold.

- Mac hotkey died when the default mic (a Bluetooth headset, off) failed to open. Fixed with a mic fallback; founder tested.
- Android and Mac apps separated: Mac has its own model link and spelling list.
- Leftover `whisper-server` processes (3 × 574 MB) after crashes; the app now clears them at startup.
- Critic review of Wispr-like Mac features (see HANDOFF "Mac fixes").
- Built: your own word fixes (`my_fixes.txt`, menu item) and Esc-to-cancel. Founder says both work.
- 60 s hold test: 75% words wrong at 62 s. Fixed by cutting long holds at quiet points: 19.0% at 62 s, 19.7% at 93 s.
- Log was empty (buffered prints); launcher now `python -u`.
- Evening: full screen (own Space), hands-free key + taps, transparency slider, notes/stars/To do, files in-app, AI (9 actions, improve keeps original), backup/restore, setup screen, meeting recording (mic + system audio), who spoke (59/60, 56/60), accuracy passes (clean 19.9% → 14.4%). All committed feature by feature.
- Pill animation fixed (underline glitch, blurred tick, abrupt cuts); capture checked from the log; MAC_PLAN holds R1–R27 + all answers + built-vs-planned.
- Founder's list R1–R24 (MAC_PLAN §3). Built: hands-free, ⌃⌘V, sounds, mic picker (old 'remember what worked' never saved), drag strip, clear glass pill + border + writing animation. Critic opinions on to-do, improve-with-original, assistant, meeting capture, install, commercial use.
- Android vs Mac and Wispr Flow research → `docs/MAC_PLAN.md`; critic: "all Android features" is the wrong goal. Built password guard, fix-a-word from history, Transcribe a file (web app), Login Items help. `mac/README.md` rewritten (was stale).
- Window redesigned (white, design-critic reviewed); Clear history fixed (it never worked); Liquid Glass pill; "nan" no longer typed.

## 2026-10-13/14 · Claude Code (Opus 5) · builds 16-29

**Next step:** founder's hand check of everything since build 15; back up the signing key; a new OpenRouter key so
an AI feature can answer on the phone for the first time; then the ₹15k phone and the install-size decision.

**Live dictation is under 10 seconds for the first time with accuracy intact: 9.6 s median, 17.1% words wrong,
15-min import unchanged at 25.0%, speakers 96.7%** (build 29, phone 33.5 → 36.9 °C).

- **The engine fix.** `Pauses.audioCtx` sizes the window to the piece instead of using a flat number. Two wrong turns
  first, both caught by the phone test: a flat 512 truncated 11 s pieces (live WER 18.3 → 32.8%), and the test
  override shipped enabled in build 28 so every piece got a 10.2 s window (15-min import 25.0 → 75.7%). `AudioCtxTest`
  now fails on all three mistakes.
- **`adb install` is 60x slower than push + `pm install`** for a 681 MB APK: 34 minutes vs 30 seconds. Three installs
  failed before this was found. Recorded in HANDOFF section 3.
- **Built:** restorable backup with a format version; one AI door replacing three duplicate buttons and a ten-label
  menu; per-paragraph speaker correction with merge and "Not sure"; retry one failed part; briefs linking tasks back to
  their paragraph; task states; keyboard rewrite chips; "say this calmly"; delete asks audio/text/both; reminders that
  ring on the alarm stream and stop every way a user might try.
- **Audit (Stage A) delivered:** 37 findings, coverage register, eight batches, published as an artifact. Stage B ran
  batches 1-5 and 8; R01 and R02 remain partly open (R02's speed half is now done).
- **Licence question closed:** the Hinglish model is Apache 2.0 — commercial use allowed, no permission needed.
  whisper.cpp is MIT. The repo still has no LICENSE of its own.
- **Corrections to earlier claims:** the model does *not* invent sentences from silence (it writes `nan`); the
  "invented words" in the scorer are real speech whose timestamps drift into a silence window. Whisper's own VAD was
  measured and rejected for transcription: 1,017 real words lost against 748 without it.
- Housekeeping: 2.4 GB of old speed-test APKs deleted (test audio kept), 4.3 GB free; `docs/PRD.md` written.

---

## 2026-10-11 (early) · Claude Code (Opus 5) · builds 12-14

**Next step:** alarm volume up, then Settings → Reminders → Test the sound. If it still doesn't ring, read the line
under the button. Then a new OpenRouter key → `apodex/apodex-1.1-mini:free` → one "Rewrite to send" end to end.

- **Merged the cloud branch** (automatic speaker labels, reminder diagnostics + test button, Translate language fix,
  Formal version). Three conflicts resolved by hand; pushed to GitHub (`df70283..caff151`).
- **Why AI features did nothing:** a saved OpenRouter key only counted if "Answer inside indite" was also ticked under
  "Where AI requests go". A working key is now always a route.
- **Why the reminder was silent:** a notification channel freezes its sound and stream at creation.
  `reminders_ring_v2` was born while the alarm switch was off (`usage=USAGE_NOTIFICATION`), so every later change was
  ignored. Channel ids now carry a fingerprint of their sound settings; stale `reminders*` channels are deleted.
  Verified after the fix: new channel, right sound, importance 4, no blocking setting. **Sound at the ear: unverified**
  (alarm volume is 5/16; the phone left the cable mid-test).
- **Rewrite to send**: one request with 9 styles (formal, polite, WhatsApp Hinglish, casual Hinglish, email, firm,
  apology, thank-you, short-and-crisp) or your own. Replaces "Formal version".
- **Delete asks what to delete**: audio only, text only, or the whole note, with the size. Now on the home long-press
  menu as well as inside the note — one shared dialog.
- **Free-model test (Mac, 45 requests):** `apodex/apodex-1.1-mini:free` 15/15, median 25 s, keeps Roman Hinglish and the
  `task | who | by when` format. `dots-3-note` translates to English and is slow. `gemma-4-31b` is rate-limited upstream.
- **Accessibility vs banking apps (researched + critic):** no test or certification exists; bank security SDKs flag any
  enabled third-party accessibility service. Never set `isAccessibilityTool="true"` (Play policy strike). Keep the
  service personal-only; the keyboard types with `commitText()` and never touches the clipboard.
- **Multiple keys to raise the free limit: no.** OpenRouter governs capacity per account, not per key.
- Invented words in silence: both model-side filters measured and killed (no_speech_prob 0.000 even on pure silence;
  95.5% word confidence on noise). Reverted; the finding is recorded in `NoteService.kt`.

---

## 2026-10-10 (night) · Claude Code (Opus 5)

---

## 2026-10-10 (night) · Claude Code (Opus 5, cloud session) · reminder sound, translation, formal version

**Next step:** build 11 on the Mac, install, then Settings -> Reminders -> **Test the reminder sound** (switch ON, then
OFF), one real 2-minute reminder with the phone locked, one Translate, one Formal version. **Nothing in this entry was
compiled:** the cloud container has no Android SDK, no model assets and no signing key.

The founder reported three hand-check failures: "alarm is not giving me sound", "the translations are not working", and
"making formal statement out of the context I have shared" does not work.

**Reminder sound.** Ranked causes, after an independent critic knocked down the first theory:
1. **"Ring like an alarm" defaulted to OFF** (`Reminders.ringLikeAlarm` returned `false`), so every reminder was a
   2.6 s chime on the notification stream - muted by silent/vibrate, Do Not Disturb or a low notification volume.
   Request #84 was "alarm-like sound" and it shipped as an opt-in switch, off, buried in Settings. **Now ON by default**,
   and the alarm path is the channel's own sound with `USAGE_ALARM` + `FLAG_INSISTENT` (alarm stream, alarm volume,
   repeated by the phone until seen, through silent mode and through DND wherever DND allows alarms).
2. **POST_NOTIFICATIONS was only ever requested when recording or importing**, never when a reminder was set. Denied =
   nothing appears and nothing sounds. `RemindDialog` now asks when it opens, `show()` reports whether the phone took
   the notification, and `fire()` marks a reminder `fired` only then, so one that could not be shown is not lost.
3. **OxygenOS force-stopping indite** drops its alarms. Settings -> Reminders now says so and opens the phone's battery
   setting; that button existed only under the floating-mic section before.

**Wrong theory, recorded so nobody repeats it:** that the channel's sound URI used the numeric `R.raw.reminder` id and
that AAPT2 had moved it. `reminder.wav`, the channel ids and `setSound` all arrived in one commit (`3d42717`) and
`res/raw` has not changed since, so the stored number still resolved. The URI is named anyway (via
`getResourceEntryName`, which also keeps a code reference so resource shrinking can't strip the WAV), and the channel
ids went to `_v2` because a channel's sound is frozen at creation and the `USAGE_ALARM` change needed a new id. ⚠ A
further change needs `_v3`: deleting a channel does not reset it - recreating the same id restores the old settings.

**Written and then deleted: a foreground service that played the alarm itself** (`notes/AlarmRing.kt`). The critic was
right that it was over-engineering: it marked a reminder `fired` before the notification was confirmed, and opening
indite removed its own ongoing notification - both ways to lose a reminder, inside the fix for a lost reminder. The
channel route does the same job with the system playing the sound. Add a player back only if a device test shows the
phone cutting the channel sound short.

Also fixed: a missed reminder re-announced itself on every app open (`rescheduleAll` notified every past reminder and
nothing marked it done) - now a `fired` flag in `reminders.json`, shown once, quietly. And there is now a way to test
the sound in 2 seconds: Settings -> Reminders -> **Test the reminder sound** + Stop, `soundProblem()` naming the
blocking phone setting (notifications off, channel blocked or muted, silent/vibrate, notification volume 0, DND, alarm
volume 0), and a "Last reminder: ..." line recording what happened the last time one fired.

**Translate.** Two real bugs: *Ask my AI -> Translate* called `ask("Translate")` with no language, so `{lang}` became
"English" - and the Hinglish rule was already skipped for Translate, so a Hinglish note came back looking almost
unchanged; it now opens the language picker. And the Google Translate route (free, offline, no key) was the last line of
a scrolling dialog; it is now the first button when the app is installed. **But the real block is configuration:**
indite has no translator or AI of its own, `MacCompanion` needs Tailscale and `OpenRouter` needs a key, so every AI
request can today only hand the text to another app and wait for a paste. Settings -> AI now prints one line
(`aiRouteNow()`) saying exactly what will happen. **An OpenRouter key is the highest-value thing the founder can do.**

**Another wrong theory, checked against Google's docs:** that Android 11+ package visibility made
`startActivity(setPackage(...))` throw for Google Translate and the AI apps. It does not - `startActivity()` needs no
package visibility, for implicit or explicit intents; filtering hits *queries* and starting another app's *service*.
`<queries>` was kept for one package only, because `installed()` asks whether Google Translate is there.

**"Formal version" added** to `AskPrompts`: formal English, every fact/name/number/date kept, nothing invented,
"(unclear)" where it can't tell. It and Translate are in `OwnLanguage`, so the "reply in Hinglish" rule is skipped -
that rule would have wrecked a formal English statement.

**Speaker labels now run by themselves** (founder: "why does speaker diarization not work automatically? ... the
initial speaker diarization should be done by you"). The honest answer to "why": **nothing ever decided it had to be
manual.** It was built as an on-demand card and request #60 removed the *count* question but left the tap. No technical
blocker either - PLAN.md line 230 records 15.9 s on the phone for a 15-minute file, about 1 s per minute of audio.
- `NoteService` now labels every note it just finished, once the queue has nothing left to transcribe, inside the
  foreground service (so Android cannot kill it half-done). Only notes *this run* finished - never a sweep of the whole
  back catalogue. Dropped rather than queued when the phone is hot or the battery is low: labels are not urgent, and
  `waitUntilSafe()` would have pinned the foreground service open (it never gives up on a low battery) for a note whose
  text was already finished.
- ⚠ **Corrected after the critic:** "never delays a live dictation" was false and had been written into the code, the
  commit message and three docs. `labelFinished()` runs in the one queue job and `onStartCommand` only starts a queue
  `if (job?.isActive != true)`, so a recording started mid-pass waits for it - and with `Notes.transcribing` false the
  recorder would have cut 1 s pieces that piled up unprocessed. Mitigations (both unmeasured on a device):
  `Notes.transcribing = true` while labelling, and an abort check passed into the pass and tested every 50 windows
  (~1-2 s of phone time), which saves nothing and leaves the note for the next run.
- `catch (e: Exception)` became `runCatching` (Throwable): a failed sherpa-onnx native load throws `UnsatisfiedLinkError`
  and a big `readPcm` can throw `OutOfMemoryError`, neither of which is an `Exception`, and both would have killed the
  queue coroutine - at the end of every long note instead of only when the user tapped. `Notes.import` already used
  `Throwable` for the same reason.
- The one-voice test counts `seg`, not just `of`: a second speaker can live entirely inside paragraphs (the short
  interview question, which is the shape of the real 15-min recording) and never win one, and the first version would
  have thrown all those per-sentence turns away.
- An explicit "2" that collapses to one voice used to show nothing at all, so the run looked like a no-op. The note
  screen now says "indite could only hear one voice in this note".
- Gate: over 60 s, 2+ paragraphs, no speakers file yet, and not a `test` note, so `phone_test.sh`'s `--ei k 2` scoring
  is untouched.
- `Speakers.labelAuto()` and `Speakers.status` (a MutableStateFlow: `Speakers.running` is a plain set and not
  observable, so the note screen could not show a run it did not start). The note screen now has one `busy` value for
  "something is working on this note", whoever started it.
- **One voice = no labels at all**, however the run started. An explicit "1" used to write "Speaker 1" on every
  paragraph. `heardOne()` saves `skipped=true, k=1, guessed=<indite decided it>`, and the note screen shows a one-line
  "indite heard one voice. Two people spoke?" only when indite decided it, not when the user chose 1.
- The existing "indite heard N people. Is that right?" card is unchanged: that is the "ask and update later" half.
- The "one voice = no labels" rule is the part that matters most: before it, once `speakers.json` existed there was no
  way back to plain text (the "Just me" button needs `speakers == null`, and the confirm card's "1" wrote `k=1`
  *labelled*, putting "Speaker 1" on every paragraph). **A wrong automatic guess is now undoable in one tap.**
- Consent framing: the only place that said "when you record others, tell them first" was the card that automatic
  labelling makes disappear. That line moved onto the "indite heard N people" card, and `privacy.txt` / `docs/privacy.md`
  now say what this does - compared on the phone, within one recording only, no voiceprint saved. `speakers.json` holds
  only ints, sample offsets and names the user typed; the fingerprints live in RAM for one note and are never written.
- No setting added on purpose. ⚠ **This is ahead of the project's own gate.** PLAN.md line 230 already says "auto count
  fragile on real audio", `phone_test.sh` only ever scores a *given* count (so 96.7% / 93.3% are given-count numbers),
  and #61 "can I trust Find who spoke?" is still waiting on the founder's listen-check - and the guess is now the
  default output for every long note. `auto()`'s 1-vs-2 call rests on one threshold (centres >= 0.35 cosine distance
  apart, and 3 windows ~ 4.5 s is enough to declare a second speaker on a 60 s note), so the expected failure is
  splitting one person into two: background TV, or music, which Silero hears as speech. Keep it in the personal build;
  it must not reach testers until measured. Also unmeasured: "15.9 s for a 15-min file" is a `--ei k 2` run, while
  `auto()` runs k-means for k = 2..5 (embedding extraction, the expensive part, still happens once).
  **Next action, no new code:** `--es test_label "<name>" --ei k 0` runs `auto()` on a benchmark note and writes the
  labels and `label_ms`; `score.py diar` scores it. Both dialogues plus the 15-min 3-voice file, ~20 min of phone time,
  answers accuracy and cost together. Numbers go in PLAN.md section 7.
- Known and not fixed: "Copy all text" on a labelled note joins consecutive turns by the same speaker into one block
  (`allText()`), so an interview where one person speaks five paragraphs running becomes one wall of text - pre-existing,
  but automatic labelling makes it the default. Floating-mic dictations over 60 s with 2+ paragraphs also pass the gate,
  so a long solo dictation with a TV on can pick up labels (the pasted text is unaffected).

Docs: founder requests 178 (reminder sound), 179 (translation), 180 (formal statement), 181 (automatic speaker labels);
summary counts corrected to 181 rows; ROADMAP "Now" item 0; HANDOFF section 5 tables with the ranked causes and both
dead theories.

**Open question for the founder:** when the reminder was due, did it appear on screen with no sound, or did nothing
appear at all? Silent-but-visible points at cause 1; nothing at all points at 2 or 3.

**Untested:** all of the above, plus everything from builds 8-10 that has not been hand-checked.

---

## 2026-10-10 (later) · Claude Code (Opus 5 / Opus 5.5) · builds 8-10

**Next step:** founder's 20-minute hand check of builds 9–10. Then the Sarvam Edge / Gboard Roman-Hinglish desk check
(1 h), the import-vs-live cut-point run (1 h), real-voice WER on ~6 min (2 h). Batch A (build 11) only after that.

- **Full phone test of build 10 passed the 15-min gate** (`SKIP_LIVE=1 ./phone_test.sh`, phone 34.7–36.8 °C):
  import WER 25.3% (build 7: 28.7%; Mac: 24.7%), 39 parts, 1.16x real time, no crash or memory failure.
  Similar voices 93.3% / 86.4%; 2-speaker dialogue 98.3% / 96.6%.
- **New finding:** 2 of 5 no-speech stretches produced invented text (10 words in pink noise, 4 in fan noise; 14 of 1545).
- **Trap found and documented:** `SKIP_LIVE=1` reuses the live result on the phone — here the ROUND=64 A/B arm, so the
  printed live numbers (87.3 s, 17.9%) are not build 10's.
- Independent critic reviewed a 17-item research / improvement / use-case list. Dropped: thread-emulation of a ₹15k phone
  (PLAN section 7 already has the numbers, and nothing calibrates it), cutting pieces earlier (a 5.3 s piece costs the
  same ~9 s of engine as a 10.0 s one, and short pieces score worse), deleting the dropped-text re-run, and all six "new
  use cases" (already built or already ruled out — recruitment copy, not code). Kept: Sarvam/Gboard check,
  start-temperature line in the test script, import-vs-live cut-point run, real-voice WER, note format version.
- **Critic's find:** `Pauses.audioCtx` is a flat 768 (15 s window) for every piece under ~13 s, so short sentences pay
  full price. A per-piece 512 (10.2 s, still a multiple of 256) could move the live wait from ~9 s toward ~6 s. Untested.
- **Recorded, not acted on:** the signing key still has one copy (5-minute founder task); "model downloads on first open"
  conflicts with the public build having no INTERNET permission, and a Play asset pack (~512 MB limit) may not fit the
  574 MB model — check the limit before writing code.
- ChatGPT: in-app login is still not a legal route (preview is application-only, no mobile; faking Codex's client risks
  the founder's own account). Founder's alternative — genuine Codex CLI under Termux on the phone — is unproven and needs
  a critic plus a 1-hour install test before it becomes a plan.

---

## 2026-10-10 (evening) · Claude Code (Opus 5.5)

**Next step:** founder hand check of builds 9–10; full phone test on a cool phone; then build 11 per ROADMAP.

- Root cause of "same audio, different text" confirmed on the phone: audio window rounded to 256 → identical text across
  runs; A/B vs old rounding: live wait 9.1/14.1 s vs 78.8/87.3 s. Heat (+1 °C) costs ~5 s. Kept 256.
- Added: Mac route can answer with ChatGPT via the founder's own Codex CLI; Settings → Your stats dashboard; header and
  subtitle fixes; chips padding; A/B test hook + `phone_test.sh` ROUND= / LIVE_ONLY=.
- ChatGPT login inside the app: not allowed yet (application-only preview, no mobile); founder may apply.
- Repo: GitHub `vaibhavk93/Indite` (public) at `790924c`; local is 32 commits ahead (not pushed).

## 2026-10-10 (afternoon) · Claude Code (Opus 5.5)

**Next step:** quick phone test of build 10 (engine fix), founder hand check, then build 11 per ROADMAP plan.

- Root cause of "same audio, different text": flash attention + audio windows not a multiple of 256. Fixed (`a69dab5`).
- Builds 9–10: reminders, floating-mic switch rework + tile, cards/menus/sticky dates, swipe hint, keyboard redesign,
  password guard, Undo/Redo, Settings Reminders/Tutorial, header/subtitle polish. Tags `build-9`, `build-10`.
- Research: one-speaker focus (feasible for turn-taking; overlap not now), value-adds per journey (top 8), vernacular
  Roman script (demand check first), iOS costs. All critic-reviewed.
- New doc: `docs/FOUNDER_REQUESTS.md` (every founder request + status).

## 2026-10-10 · Claude Code (Opus 5.5)

**Next step:** founder tries build 7; then `QUICK=1` phone test; record the 15-min run-to-run finding.

Later the same day (build 7, tag `build-7`): Settings in 6 groups; bubble hide → notification; OpenRouter key +
"where AI requests go"; Remind me; password/OTP guard; versioning (0.7, build 7, git hash in About); handoff docs;
look-and-feel batch (transitions, voice glow, fade-in, "All written", day headers, swipe-right copy).

Built (all committed; pushed up to `738a118`):
- v0.6 part 2: export, privacy policy, debug info, auto titles, storage check, consent reminder, test hooks personal-only.
- Floating mic "no speech" fixed (mic service type dropped on stop cut the last read; last piece now saved in `finally`).
- Bubble: spinner while writing, green copy button, hold 0.4 s to cancel, shrink when idle, drag away = hidden with a
  "Tap to show" notification. Keyboard: listening → writing → typed in; skips password/OTP boxes.
- Personal build: accessibility auto-paste into the focused box; OpenRouter key (answers saved inside indite).
- Speaker labels per sentence (51.7% → 96.7% on the phone test); guess the count, then confirm.
- Make notes / Action items / Translate buttons; meeting notes include task rows (Calendar, Remind me, Share);
  "where AI requests go" (tick several); language picker; AI requests v2 (date, title, transcript-is-data).
- Settings split into 6 groups; floating Record button on home.
- Imports: dropped-text re-run limited to live recordings (it made the 15-min file worse).
- `phone_test.sh`: `QUICK=1` mode (~12 min).
- Docs: ROADMAP.md merged into one roadmap (+ page); research reports on translation, iOS, UI/UX, Wispr Flow.

Untested on the phone: Settings groups, bubble hide notification, OpenRouter, Remind me, keyboard password guard.

Decisions (founder): bubble without accessibility now, accessibility add-on later (personal has it); guess-then-confirm
speaker count; iPhone not now (trigger: 5+ tester asks); one roadmap.

## 15 Oct 2026 (evening) — Wispr Flow screenshots: gap check, critic pass, plan

The founder sent 15 Wispr Flow screenshots and asked which features indite lacks, which are easy, which are not.
Checked each against the code (not from memory), then put the whole list past an independent critic.

**The result overturned most of the list.** 5 of 14 "missing" features are already built:
- Snippets = the existing word fixes (`store.apply_my_fixes`; the file's own example is a full postal address).
- The Dictionary page, add/remove, and "teach this" from a past dictation all exist (`ui/app.html:452`, `:1300`).
- Words per minute, time saved, by app, by hour, day streak and the heat map are all on Insights (`:1368`-`1394`).
  Note the contradiction: ROADMAP says "no streaks", the code shows one. Someone should decide which is right.

**Build now (~2 h):** W1 one example phrase row on the Dictionary page; W2 "teach this word" one click from the
Dictations list; W3 a "fixes made" count on Insights.

**Gated:** W4 feed the Dictionary to whisper as `initial_prompt` — the only item that can actually lower the error
rate, and the only one whose failure is invisible (the model already wrote `nan` into a real app on a 1.7 s hold).
Gate: the 360-clip bench must improve *and* show 0 false insertions of dictionary words. W5 "Light" clean-up with no
AI at all (strip a fixed filler list in `tidy()`, keep the raw text) — gate: 30 real dictations, 0 real words removed.

**Dropped, 11 items** — AI clean-up on every dictation (4-7x slower, spends the founder's quota, replaces the raw
text), transforms hotkey, per-app styles, command mode, stacked messages, Dock-icon toggle (would break the pill over
full-screen apps), mute music, LaunchAgent login, scratchpad, IDE file reading, extra languages, team/sync/referrals.
Reasons in `docs/MAC_PLAN.md` section 6.

**What the critic said matters more:** (1) Screen & System Audio Recording is still not granted, so meeting recording
and the demo video are built-but-dead; (2) the 53 real dictations have never been scored — every accuracy number is
from 360 synthetic clips, and `digits.py` admits its pass changed 0 of those 53; (3) nothing is signed or notarised,
and 10 items are still "built, founder to check". Also: the public repo has no LICENSE file, and the keystore still
has one copy.

Corrected in this session: I first reported snippets, the Dictionary UI and the Insights stats as missing. They are
all present. The error came from checking for new files instead of reading the ones that exist.

## 16 Oct 2026 · Mac: ready for the leadership demo

- **Long dictation no longer crawls in** (founder, request 244). pynput sends two key events per character, so a
  paragraph was hundreds of events and Chromium apps drained them a frame at a time. One macOS key event can carry
  20 UTF-16 units instead — about 40x fewer events. Measured through indite itself: TextEdit 0.23–0.61 s, a Chrome
  textarea 0.48–0.85 s, character-exact at 197 / 788 / 1576 chars. Numbers in
  `docs/research/mac_typing_speed_2026-10-16.txt`. The clipboard is still never touched.
  **The clipboard route was rejected** by the critic: a restore racing a slow app can paste the *previous* clipboard
  (a password manager entry) into the target, and a missed secure-field check would leave a spoken secret on the
  clipboard. It would also adopt the mechanism MAC_PLAN names as Wispr's weakness.
- **Word fixes no longer break contractions.** With `don = Dawn`, "don't go" became "Dawn't go". Found by the
  research agent, reproduced, fixed, covered by `store.py`'s self-check. Possessives are left alone too, on purpose.
- **Demo script updated** (request 242): a scene for the gold AI edge, "Make it a prompt" named in the Ask AI line,
  AI usage named in the Insights line, the "about a second" claim narrowed to "a second for a sentence like that",
  and `stage()` pre-answers the meeting→AI warning so the modal cannot interrupt a take.
- **"Make it a prompt" rebuilt** (request 243) to Anthropic's published guidance: says why the rules exist, five
  numbered parts, one worked Hinglish→prompt example, keeps Indian words with a gloss. `max_tokens` 4000 → 8000 and
  a cut-off answer now says so instead of looking finished.
- **`docs/WISPR_DEEPDIVE.md`** (732 lines, request 238): how Wispr builds each feature we lack, every option for us,
  the best two each, challenges and workarounds, multi-language routes, the AI-review algorithms, profanity design.
  Three findings that change decisions: the offline near-miss check only passes its gate when gated on the engine's
  own confidence (1.9 → 0.4 false alarms per 100 words); feeding the Dictionary to whisper as `initial_prompt` makes
  overall accuracy *worse* in published measurements, and collapsed on German (6.3% → 15.2%), and our model is a
  non-English fine-tune; the tester keystore is byte-identical to `~/.android/debug.keystore`.
- Founder's decision: the Android release key waits for the next Android build; the Mac demo comes first.

**Still open:** swear masking is stored rather than shown (breaks R5 — see HANDOFF §5). Slack and VS Code typing
untested. The note-before-instructions change for all 13 AI actions is deliberately **not** done before the demo.

## 16 Oct 2026 (early hours) · Mac: four bugs found by testing the whole app, demo cut built

Full end-to-end run, 21 checks. First pass: 16 passed, 5 failed. Final: **21 of 21**.

**Bugs found and fixed**
1. **CoreAudio deadlock.** Four threads wedged in `FinishStoppingStream` → `std::recursive_mutex::lock()`. Dictation
   worked once, then every press was dead: pill up, bars frozen, nothing written. `_drop()` now aborts instead of
   stopping, closes on its own thread and abandons the stream after 1.5 s.
2. **PortAudio left shut down** — caused by the first fix. The per-press device rescan is `Pa_Terminate` +
   `Pa_Initialize`; when the terminate wedged and we moved on, it finished later with nothing to re-initialise, so
   every open after that failed with "Error querying device -1". The rescan now runs only after every device has
   failed to open, and `_alive()` restarts PortAudio before each use.
3. **The consent dialog landed in `who_spoke()` as well as `ask_ai()`** (my edit, 15 Oct). Speaker detection is
   entirely local, so it asked about a send that never happens — and crashed, since `NSAlert` is imported in
   `ask_ai`. Every file transcribed fine and was then reported "file failed", with no speakers. Removed.
4. **The app was breaking its own signature every run.** Python wrote `.pyc` files into the bundle (249 found), the
   seal broke, and macOS dropped Accessibility mid-session — the log shows `allowed: True` → `not trusted` →
   `allowed: False`. `PYTHONDONTWRITEBYTECODE=1`, bundle cleaned and re-signed, `build_app.sh` now verifies the seal
   and refuses a build that does not hold, and `signature_broken()` warns at start-up.

**Measured after:** 6 recordings back to back; 389 characters typed exactly in 0.32 s; 230 s two-speaker file → 31 s
to transcribe, 58 s to find 2 voices; all 8 pages draw; signature still valid after a full run.

**Demo:** `docs/DEMO_PLAN.md` (researched, critic-reviewed — it overturned 6 of its own 8 first recommendations).
22 scenes → 8 beats, 6–8 min → 3:20, hero at second zero, Wi-Fi off on camera instead of a privacy sentence, live
meeting recording cut because its permission is still unproven in a real call. `demo.py --short` built.
Biggest finding: every sound in the current demo is synthetic, including the Hinglish spoken *into* the app.

**Open:** the founder's narration, and whether to show a real error on camera. Signing certificate: after the demo.
