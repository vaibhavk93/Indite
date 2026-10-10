# Work log

Newest first. One entry per session: date, who, what changed, what's untested, next step. See `docs/HANDOFF.md`.

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
- `NoteService` now labels every note it just finished, but only once the queue has nothing left to transcribe (so a
  live dictation is never delayed), inside the foreground service (so Android cannot kill it half-done), after
  `waitUntilSafe()`, and it bails out if a recording starts. Only notes *this run* finished - never a sweep of the
  whole back catalogue.
- Gate: over 60 s, 2+ paragraphs, no speakers file yet, and not a `test` note, so `phone_test.sh`'s `--ei k 2` scoring
  is untouched.
- `Speakers.labelAuto()` and `Speakers.status` (a MutableStateFlow: `Speakers.running` is a plain set and not
  observable, so the note screen could not show a run it did not start). The note screen now has one `busy` value for
  "something is working on this note", whoever started it.
- **One voice = no labels at all**, however the run started. An explicit "1" used to write "Speaker 1" on every
  paragraph. `heardOne()` saves `skipped=true, k=1, guessed=<indite decided it>`, and the note screen shows a one-line
  "indite heard one voice. Two people spoke?" only when indite decided it, not when the user chose 1.
- The existing "indite heard N people. Is that right?" card is unchanged: that is the "ask and update later" half.
- No setting added on purpose. ⚠ **The count guess is unmeasured on real audio** (PLAN.md: "auto count fragile on real
  audio"; the phone test only scores a given count, so 96.7% / 93.3% are given-count numbers). Before testers: score
  the guess on the 3 real recordings, and measure battery and heat for auto-labelling a 15-min import. If either is
  bad, add a switch - the hook is one `if`.

Docs: founder requests 178 (reminder sound), 179 (translation), 180 (formal statement), 181 (automatic speaker labels);
summary counts corrected to 181 rows; ROADMAP "Now" item 0; HANDOFF section 5 tables with the ranked causes and both
dead theories.

**Open question for the founder:** when the reminder was due, did it appear on screen with no sound, or did nothing
appear at all? Silent-but-visible points at cause 1; nothing at all points at 2 or 3.

**Untested:** all of the above, plus everything from builds 8-10 that has not been hand-checked.

---

## 2026-10-10 (later) · Claude Code (Opus 5 / Opus 5.5) · builds 8-10

**Next step:** plug the phone in -> install build 10 -> screenshot the italic subtitle -> `QUICK=1 ./phone_test.sh`.
Then run the Mac test of "audio window rounded to 256" (it never ran: the agent died on a usage limit).

Built (21 commits, `af9ea88`..`7b3259c`, all local; last pushed is `738a118`):
- Engine: found that run-to-run text differences come from flash attention reading leftover audio-cache rows
  (`420bb28`). Off = repeatable and more accurate on the Mac (27.6% -> 25.1%) but ~6 s slower per live sentence on the
  phone, so it is back on (`9af355a`). Untried: `audio_ctx` rounded to 256.
- Privacy: the keyboard and the bubble share one password/PIN/OTP rule (`1044bf4`, `63a5b7a`).
- Floating mic: one switch, drag onto the X to turn it off, quick settings tile (`7d4f227`); drag polish - magnetic X,
  a buzz on arrival, springy edge snap, remembers where you left it.
- Reminders (founder decision, overrides the old "no own reminders"): exact alarms, Remind me on the card, note menu and
  task rows, quick picks + any date/time, Done / Snooze 1 h, re-set on open/reboot/update, list in Settings (`d5d0188`);
  soft two-note chime + nudge vibration, optional "ring like an alarm until I respond" (`3d42717`).
- Home and notes: cards with a border, Copy button, long-press menu (`6b291cd`); header back to the original size and
  weight, pinned (`84ea88b`), then slightly smaller with less space below (`3d42717`); search-bar line removed; the empty
  brown button was "Done" squeezed to zero width - buttons now sit on two rows, plus Undo/Redo and "Back to original"
  (`3d42717`); menu icons; swipe-hint animation replaces the tip card (card peeks right = Copy, left = Delete, once a
  day, switch + "Show it again" under Settings -> Look & feel -> Tutorial) (`963545b`).
- Keyboard redesign: gradient mic orb with a halo that swells with your voice, live level bars, status pill, springy
  keys, a "done" pop (`963545b`). Italic subtitle using Figtree's real italic file, not a slanted fake.
- Docs: `docs/FOUNDER_REQUESTS.md` - all 172 founder requests with status, why and open questions; agents must keep it
  current (`7b3259c`). Roadmap: reminders decision, plan forward (build 10 -> Rs 15k phone test -> tester build ->
  testers), overlap deferred with a measurement plan (`671c8c8`).
- Research (critic-reviewed, local only in `reports/` and `research_notes/`): value-adds per journey (top 8) and Gujarati
  / Marathi into Roman script (possible in two steps, demand unproven - ask on tester sign-up first).

**Untested:** everything in builds 8-10. The phone was unplugged when build 10 finished, and the session then hit a
usage limit mid-handoff, so this entry and HANDOFF section 5 were written in the next session from the git log.

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
