# Roadmap archive: the 10 Oct snapshot

Moved out of ROADMAP.md on 17 Oct. **Not a plan.** Every item still open here was carried into ROADMAP.md (Android "Later" and "Open" lists). Kept for history only.

## Founder's requests (10 Oct 2026) and their status

| Request | Status |
|---|---|
| Bubble: show processing, copy button, typed into the box (personal), cancel, shrink, hide | **Built** (cancel at 0.4 s hold; hiding is temporary) |
| Keyboard: show recording → writing → typed in, like the bubble | **Built**, to test |
| Notes and action items as their own buttons; action items with Calendar / Share | **Built**; Meeting notes also give action items |
| Request opens your AI app directly with the prompt + text (no app list) | **Built** (Settings → Your AI app) |
| AI replies saved back without copy-paste | **Personal: Mac route** (needs Tailscale, founder setup); others: copy → Paste reply (card now waits). Share-back not built (no tap saved) |
| Translate: pick a language, prompt goes with the text | **Built** (remembered language; Google Translate as offline option) |
| Speaker count: guess, then confirm | **Built**; speaker labels 51.7% → 96.7% on the phone test |
| Shorter phone test | **Built** (`QUICK=1`, ~12 min) |
| Sleeker home screen (record button) | **Built** (floating Record button) |
| Bubble only when a keyboard is up | **Later:** needs the accessibility add-on (public build decision pending) |
| Modern look, themes, animations ("feels made by AI") | **Planned (critic-reviewed):** motion first, palette stays; top 10 list below |
| Settings split into sections instead of one long scroll | **Planned:** 6 rows with sub-screens |
| Optional API key (e.g. OpenRouter free models): key / share / both | **Planned, personal build first:** 1-hour quality test of free models before any code; no "Both" setting |
| Editable AI prompts (incl. translation prompt) | **Later:** language choice covers the main need |
| Check speaker-label quality yourself (e.g. play one speaker's parts) | **To review** |
| Speak the translation aloud; live interpreter | **Parked** (14–15 s per turn; waits for 3 real asks) |
| iPhone app | **Not now** (trigger: 5+ tester asks) |

### Also open (found in a full review of the chat, 10 Oct)

| Item | Status |
|---|---|
| Accessibility shortcut should toggle the floating mic | Not possible on Android (it only controls the accessibility setting); Settings explains it; build 7 |
| "Where AI requests go": tick several | **Built** (build 7) |
| OpenRouter key, answers saved inside inditeflow | **Built** (build 7, personal); waiting for the founder's key |
| Reminders / timers | **Built** as "Remind me" → Clock app (inditeflow stores nothing); build 7 |
| Wispr Flow comparison | Done (15-16 Oct): `docs/MAC_PLAN.md` §6, `docs/WISPR_DEEPDIVE.md`. Snippets = word fixes and the streak are built; build items now in "Now" |
| Mac web app: restarting still starts jobs from scratch (PLAN §5) | Next (web) |
| Check whether Sarvam Edge / Gboard already do Roman Hinglish | Research, before testers |
| Repo has no LICENSE (public repo) | Founder decision, before testers |
| Home-screen widget / quick tile for dictation | Re-assess (dictation now exists) |
| Native Mac app vs the web app | Not assessed |
| Restore notes on a new phone (export exists, import doesn't) | Unreviewed idea |
| Battery use of the always-on bubble / keyboard | Unreviewed; measure before testers |
| One setup checklist for all permissions | Unreviewed; fits the try-it onboarding |
| Play internal testing track for testers (instead of sideloaded APKs) | Unreviewed |

## Decisions on 10 Oct (latest) and the plan forward

- **Reminders: inditeflow sets its own** (founder decision; overrides the earlier "no own reminders" rule). Exact alarms
  (an inexact alarm can be up to 1 hour late); Remind me on the card menu, note menu and task rows; Done / Snooze; list in
  Settings. Gate: 10 reminders over 3 days on the OnePlus (overnight, reboot, swipe-away, Battery Saver), all within 1 min.
- **Floating mic: one switch.** Drag onto ✕ = off; quick settings tile; accessibility shortcut toggles it (personal).
- **"Show only [name]"** filter on a recording: next build. **Voice "Me"** (recognise the user's voice in future recordings):
  accepted, built only behind consent + privacy-policy text, delete button, never exported.
- **Overlapping speech (2–3 people at once):** not now. First record 3 real conversations with interruptions and measure
  lost words; build overlap marking only if > ~3% of words or real content is lost.
- **Run-to-run text differences:** root cause = flash attention reading leftover audio-cache rows. Off fixed it but cost
  ~6 s per live sentence; testing "audio window rounded to 256" to keep speed.
- **Brand:** lowercase "inditeflow", pinned in the top bar.

**Plan (critic-reviewed):**
| Phase | Contents | Gate |
|---|---|---|
| Build 9/10 | Engine fix confirmed; reminders; Show only [name] | No regression on bench clips; reminder 3-day gate |
| **₹15k phone test** (alongside, ~2 h) | Dictation time, 15-min import, RAM | Dictation ≤ ~15 s, no crashes; else speed work first |
| Build 11 = tester build | Try-it onboarding + one permissions checklist; model download on first open; targetSdk up; battery check; Play internal testing | 3 friends install from a link unaided; battery < ~5%/day |
| Testers | 10–20 people + interviews | 5+ use it in week 2 unprompted |

Deferred until testers ask: voice "Me", overlap marking, OpenRouter (no key yet), rest of the look-and-feel list, web
items, Windows, retention setting, custom vocabulary. Biggest risk: speed on a ₹15k phone.

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

