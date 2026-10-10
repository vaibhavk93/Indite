# Work log

Newest first. One entry per session: date, who, what changed, what's untested, next step. See `docs/HANDOFF.md`.

---

## 2026-10-10 (night) · Claude Code (Opus 5)

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
