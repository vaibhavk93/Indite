# Work log

Newest first. One entry per session: date, who, what changed, what's untested, next step. See `docs/HANDOFF.md`.

---

## 2026-10-10 · Claude Code (Opus 5.5)

**Next step:** finish the look-and-feel top 10, install, `QUICK=1` phone test, founder hand check.

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
