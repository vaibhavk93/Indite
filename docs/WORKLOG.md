# Work log

Newest first. One entry per session: date, who, what changed, what's untested, next step. See `docs/HANDOFF.md`.

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
