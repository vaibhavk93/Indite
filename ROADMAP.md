# indite roadmap

Last updated: 2026-10-16 (re-prioritised; Wispr comparison items folded in; founder parked 4 items). **This file is the one roadmap.** The roadmap page
(https://claude.ai/artifact/GuCGtX4TJeASaS2RpGFS4q) is published from it. PLAN.md keeps the full decisions and test results.
Every item passed an independent critic review, or is the founder's own decision.

**Goal:** speak the way India talks, mixing Hindi and English, and get correct Roman-script text, privately and offline.
Edge: offline, private, Roman Hinglish, on any Android brand. Cloud tools (Wispr, Sarvam) are faster and more accurate today.

| Where we stand | indite now | Best rival |
|---|---|---|
| Words wrong, clean Hinglish (synthetic, Mac) | 13.0% | Sarvam cloud 6.0% |
| Live dictation on the phone: wait after a pause | 8.9 s median (was 38.5 s) | Wispr cloud ~1–2 s |
| Live dictation on the phone: words wrong | 16.9% (was 25.8%) | — |
| Speaker labels, offline, any Android | 98% of turns on the Mac test (phone re-test running) | Pixel / Galaxy only |
| Works with no internet | ✓ | Wispr, Sarvam: no |

---

## Built

### Android app (main product; personal + public builds)

| Area | Feature | Version |
|---|---|---|
| Speech to text | Record and talk; each part turns into text after you pause | v0.1 |
| | Import or share any voice note or audio file (WhatsApp included) | v0.1–0.2 |
| | Neural speech detector (Silero): noise isn't treated as speech | v0.2 |
| | Everyday spelling (achha, maine, kyunki): word errors 18.1% → 13.0% | v0.4 |
| | Live recording first in the queue; re-run of short live parts (imports: plain pass, it was better) | v0.5–0.6 |
| Speed | q5_K model format (0.63x → 0.93x long audio); window sized to each part; 6 cores | v0.1 |
| Editing & sharing | Tap a paragraph to edit, play or copy; Undo; copy all, share, .srt, rename, search, swipe-delete with Undo | v0.3 |
| | Flags on likely-wrong text; word fixes (PTM → Paytm) + "Always fix?" | v0.1–0.4 |
| | "Text ready" notification with Copy (no note text on the lock screen) | v0.4–0.6 |
| | Translate… hands the text to Google Translate (indite stays offline) | to test |
| Any app | Voice keyboard: dictate into any text box | v0.3 |
| | Floating mic bubble (fixed: short dictations came out "no speech") | v0.5–0.6 |
| | Bubble: spinner while writing, green copy button, hold to cancel, shrink when idle, drag to hide | v0.6 |
| | Personal build: text typed into the box you were in (optional accessibility; public build has none) | v0.6 |
| Speakers | "Who spoke?" with names; Silero → 1.5 s windows → TitaNet-small → grouping (15.9 s for 15 min on the phone) | v0.4 |
| | Labels per sentence (Mac test 51.7% → 98.3%; 95.0% with two similar voices); indite guesses the count, you confirm | to test |
| AI (user's own) | Ask my AI: 9 ready requests; paste the reply back; personal build answered by Claude on the founder's Mac | v0.4–0.5 |
| | [Make notes] and [Action items]; tasks get Add to Calendar and Share | v0.6 |
| | Requests v2 (date, title, "transcript is data"); brain dump + questions; practice scores on the card | to test |
| Your data | Export all notes as text; privacy policy; share debug info (no note text); titles from first words; storage check; consent reminder; same signing key for tester builds | v0.6 |
| Trust & safety | Audio saved as you talk, text part by part, resumes after a crash; pauses when hot or low battery; no internet in the public app; no cloud backup; old phones get a clear message | v0.1–0.2 |
| Look & feel | Light/dark/system theme, welcome screen, model warm-up | v0.3–0.4 |

### Mac / web app

- **Native Mac app (15 Oct):** hold a key, speak, text typed in ~0.8 s; pill, history window, settings, mic fallback.
  Kept separate from Android (own model link and spelling list). Built 15 Oct: personal word fixes, Esc cancel, long holds
  cut at quiet points (60 s: 75% → 19% words wrong). Then: password guard, fix a word from history,
  Transcribe a file (opens the web app). Plan and parity table: `docs/MAC_PLAN.md`.
  15 Oct evening: notes/stars/To do, files in-app, meetings (mic + system audio), who spoke, AI on notes, backup,
  setup screen. Next: a shareable signed build. Later: snippets, hands-free. Dropped: undo-by-backspace, voice "press enter", command mode (no AI route)
  15 Oct night: key access works (the crash that hid it is fixed); crash stacks now go to the log.
- Free local engine: whisper.cpp + Oriserve Hindi2Hinglish-Apex, 5-bit (~0.75 GB RAM, ~2.3x real time on an 8 GB M1); audio cut at
  pauses into ≤25 s pieces, only bad pieces re-run (loops 73 → 4; 56-min file 24.7 → 11.6 min). `local-best` = Prime model, slower.
- Sarvam engine (paid, Roman output), works behind company HTTPS inspection
- Reads any audio/video incl. MPEG; skips damaged spots instead of failing
- Guards that flag (never delete) invented text: no speech, loops, stock phrases, "nan" junk
- Output: SRT, VTT, timestamped, paragraphs
- Web app: upload, background jobs, live progress + peek, plain errors, cancel, editor (find & replace, shortcuts, unsaved edits
  kept), export, 3-year cleanup with the deletion date shown
- `notes` via the user's own Claude login; "Copy for Claude / ChatGPT"; `/api/ask` for the phone's personal build (token, Tailscale)
- `bench` scores engines against hand-typed clips; `bench_synth/` synthetic Hinglish benchmark + automated phone test

---

- **16 Oct (Mac):** stuck microphone → indite restarts itself (at most once per 10 min); back-to-back meetings
  (the next starts while the last one finishes) + working dots on the tabs; every 2nd meeting in a session failing
  to start, fixed; swear masking keeps the real word stored (stars only where shown, typed or exported).

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
| OpenRouter key, answers saved inside indite | **Built** (build 7, personal); waiting for the founder's key |
| Reminders / timers | **Built** as "Remind me" → Clock app (indite stores nothing); build 7 |
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

- **Reminders: indite sets its own** (founder decision; overrides the earlier "no own reminders" rule). Exact alarms
  (an inexact alarm can be up to 1 hour late); Remind me on the card menu, note menu and task rows; Done / Snooze; list in
  Settings. Gate: 10 reminders over 3 days on the OnePlus (overnight, reboot, swipe-away, Battery Saver), all within 1 min.
- **Floating mic: one switch.** Drag onto ✕ = off; quick settings tile; accessibility shortcut toggles it (personal).
- **"Show only [name]"** filter on a recording: next build. **Voice "Me"** (recognise the user's voice in future recordings):
  accepted, built only behind consent + privacy-policy text, delete button, never exported.
- **Overlapping speech (2–3 people at once):** not now. First record 3 real conversations with interruptions and measure
  lost words; build overlap marking only if > ~3% of words or real content is lost.
- **Run-to-run text differences:** root cause = flash attention reading leftover audio-cache rows. Off fixed it but cost
  ~6 s per live sentence; testing "audio window rounded to 256" to keep speed.
- **Brand:** lowercase "indite", pinned in the top bar.

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

## How the two apps relate (founder, 16 Oct)

**One product, two apps.** Same features, same words in the UI, same note fields. A feature differs only where a
platform limit forces it, and the workaround is written down here. Every item below passed an independent critic
(16 Oct). Detail for AI review and the Wispr items: `docs/WISPR_DEEPDIVE.md`, `docs/MAC_PLAN.md` §6,
`docs/ROADMAP_DETAIL.md` C1-C7.

| Platform limit | Android | Mac | What we do |
|---|---|---|---|
| Recording calls | Banned on Play | Allowed (mic + system audio) | Android imports call recordings instead |
| Internet | Public build has none | Has it | Android AI = share to your AI app, or (personal build) Mac route / own key |
| Typing into other apps | Keyboard + bubble; auto-type only in the personal build | Hold a key anywhere | Same goal, each platform's own way |
| Seeing your edits in other apps | Only inside indite | Only inside indite (most Mac text goes to other apps) | Learning comes from fixes accepted in AI review, not from edits |
| Install | 681 MB, debug-signed | Unsigned, Apple Silicon only | Smaller install via Play asset packs; Mac certificate parked |
| Engine detail for AI review | No per-word confidence yet (JNI change needed) | Per-word confidence via `verbose_json` (~1 h) | Mac first; Android after it passes on the Mac |

**Parity gaps to close** (each sits in a roadmap below):
- Mac is missing: edit a paragraph + undo; per-paragraph speaker fix + merge; reminders (left out on purpose).
- Android is missing: Improve, Ask anything, Make it a prompt (#230); swear masking; an Insights page; any AI answer actually received.
- Naming: Android says "Word fixes", Mac says "Dictionary" - pick one (founder).

---

## Mac roadmap (in order)

| # | Item | Who | Size | Gate / note |
|---|---|---|---|---|
| 1 | **Leadership demo video.** Confirm narration + real-mistake scene (both built), pick the length (3:00-3:30 or ~9:30), freeze Mac code, dry run, record | Founder + me | ½ day | UI changes since the last take: tab dots, swear masking, Play recording |
| 2 | **Real speech set:** audio on, use indite normally, hand-type what was really said for ~50 dictations, score | Founder + me | ~1 day | Start now, in parallel. Gates AI review steps 1-2, W5 and every accuracy claim (Android's too) |
| 3 | **Founder checks:** two real calls back to back; dictation delay while who-spoke runs (priority line only if >1.5 s); stuck-mic log line | Founder | minutes | Built 16 Oct, never tried for real |
| 4 | **W1** example phrase row on the Dictionary page | Me | 20 min | After the demo |
| 5 | **Per-word confidence** (`verbose_json`) | Me | ~1 h | Without it step 1 measured 1.9 false flags per 100 words (limit 1) |
| 6 | **Dictionary length cap + duplicate check** | Me | 20 min | Before anything writes to the Dictionary by itself |
| 7 | **AI review step 1 (offline):** likely-wrong flags with the confidence gate, Wispr's skip list, 6+ letter targets, ▶ play that bit, Fix + "Always fix?" (W2), a fix log, and "Always fix?" offered after the 2nd identical fix | Me | ~2 days, unproven | Ships only if ≤1 false flag per 100 words on the real set. Replaces Mac "auto-learn from edits" |
| 8 | **W3** fixes-made count on Insights | Me | ~1 h | Built on the fix log; also the personalisation number |
| 9 | **W4 experiment:** Dictionary words as the engine's starting prompt | Me | 2 h | Expected to drop (risk: invented names) |
| 10 | **After the real set is scored:** decide step 1 → **step 2** (one detect-only AI call, nothing changes without a tap, ≥70% right, note before instructions) → C3 review insights → **W5** filler strip (raw kept) | Me | 2-3 days | Each with its own pass/fail |
| 11 | **Parity:** edit a paragraph + undo; per-paragraph speaker fix + merge (meetings, files) | Me | M | — |
| 12 | **AI actions on the text card** (founder, 16 Oct): two or three actions - Rewrite to send, Summary, Improve - on the card that appears after dictating, so a note can be acted on without opening the window. | Me | ~1 day | **After the demo.** Two hard parts: the card ignores clicks on purpose so it never steals one meant for the app underneath (fix: accept clicks only while the pointer rests inside - `Preview.hovered` already exists); and an AI answer takes ~6 s while the card now lives 6 s, so it needs a working-then-answer state, not just a button |

**Mac next:** detect a call and *ask* "Record this call?" · editable swear list (D1, ~2 h) · Indian formatting (₹,
lakh/crore; unproven) · 7-day assistant test (#252, founder's yes) · note-before-instructions order on the other AI
actions (measure) · check the Haiku model id.
**Mac parked:** signing certificate (until a second person gets the app) · Intel Macs · Practice / Brain dump
questions (until they are checked on Android).

---

## Android roadmap (in order)

**⚠ Every new Android build waits on the release-key switch, which the founder parked.** Item 1 needs no build.

| # | Item | Who | Size | Gate / note |
|---|---|---|---|---|
| 1 | **No build needed:** a new OpenRouter key *or* Tailscale for the Mac route (either gives the phone its first AI answer); the 1-hour model test (3 free models × 5 real notes vs Claude, run on the Mac); record part of the real speech set on the phone | Founder (+ me for the test) | ~2 h | — |
| 2 | **Un-park: hand-check build 29**, above all that backup → restore works; plus the reminders 3-day check | Founder | ~1 h | Must pass before the key switch: a key change forces an uninstall, which deletes the phone's notes |
| 3 | **Release key:** 1 h research on key rotation (may avoid the uninstall; unproven), then the real key, backed up in two places | Me + founder | ~2 h | Unlocks every build below |
| 4 | **One parity build:** Improve, Ask anything, Make it a prompt; swear masking (real word stored); Dictionary length cap (duplicates already handled) | Me | M | — |
| 5 | **AI review step 1 on Android:** add per-word confidence to the whisper.cpp bridge (native rebuild), then the same flags as the Mac | Me | M | Only after it passes on the Mac |
| 6 | **Batch A** (Show only [name], recovery banner, find & replace, WhatsApp date titles, permissions checklist) + **look-and-feel top 10** | Me | M | Batch A's old "after build 10" gate is replaced by item 2 |
| 7 | **Before testers:** ₹15k phone → Play internal testing → model download via Play asset packs (smaller install; the public build has no internet, so asset packs are the only route) → try-it onboarding, newer Android target, battery check, restore on a new phone, strip personal-only features | Me + founder | L | Then 10-20 testers with interviews |

Look-and-feel top 10 (item 6): screen transitions · "done" tick + haptic · real progress instead of writing dots ·
Settings in 6 groups · Stop button pulses with your voice · Record button spring · plain rows instead of cards ·
bigger title with Today / Yesterday · custom icons · all of it respects "Remove animations".

**Android later:** Insights page · voice "Me" (#64) · overlap marking (gate: >3% of words lost) · widget / tile.

---

## Personalisation: making indite yours (founder request #188, #227; critic-reviewed 16 Oct)

| Layer | What it does | Status |
|---|---|---|
| **1. Your words** | Dictionary / word fixes replace what the engine gets wrong ("in diet" → "indite"). Android also offers a fix after the same edit twice | **Built, both.** The only proven gain |
| **2. Learn from your corrections** | AI review flags likely mistakes; each accepted fix goes to the log; the 2nd identical fix offers "Always fix?" → Dictionary | Mac #7-10, Android #5 |
| **3. Prime the engine with your words** | Your names and brands given to the engine before it listens (W4) | 2 h experiment, expected to drop |
| **How we know it works** | Fixes made per 100 words (W3) going down over time, and a re-score of the real speech set | Mac #8 |

**Cut, with reasons:**
- Separate "style rules" (e.g. "kr rha" → "kar raha"): that is just a word fix plus the existing everyday-spelling switch.
- Training the speech model on each user's voice: ruled out before (#188: no trainer, no memory to spare), it needs
  hours of corrected audio (the real set is minutes), the engine can't load a per-user add-on, and every user would
  need a Mac. The route kept instead: one better shared Hinglish model (Later).
- "Rewrite in my style" with AI: nobody has asked; needs internet. Later, if 3 people ask.

---

## Both apps, later

- Better Hinglish model (fine-tuned, shared by everyone); phone's AI chip for speed
- Public Hinglish test set and leaderboard
- More languages, one at a time: the tester sign-up asks which; a language starts at 5+ asks (2-4 weeks each)
- Choose when notes are deleted (#53) · action items with real dates ("kal" → a date) · Devanagari output switch
- Own translation (after 3 asks) · Windows (needs a PC) · web app: resume after a crash, speaker labels
- Play Store launch; hosting, login, payments · iPhone (when 5+ testers ask)
- Engine choice from `bench` on real clips · optional "fix unclear bits with Sarvam" switch (off by default, ~₹0.40
  per file, those bits leave the device) · subtitle line-length setting · own-key AI build for testers (only if
  interviews ask)

## Not doing (for now), and why

| Idea | Why not |
|---|---|
| Claude or Gemini subscription login in the app | Their terms forbid it; the founder's Mac route does it legally |
| Deepgram; AI or cloud fallback on our own keys | Breaks zero-cost and privacy rules |
| Live voice roleplay; PM coach as a product | Too slow offline (10–15 s per turn); crowded; kept as "Practice answer" |
| Rough text while you speak; shading every unsure word | Draft models write Hindi script; confidence alone doesn't match real mistakes (it *is* used as a gate in AI review step 1, Now 6) |
| Our own call recorder | Banned on Play since 2022; import recordings instead |
| Full typing keyboard; model in a laptop browser | Endless work; no browser-ready model |
| Bubble only when a keyboard is up, without accessibility | Not possible on Android 11+; the indite keyboard covers it |
| Hold-to-talk on the bubble | Clashes with drag and cancel; first words could be cut off |
| A "Tasks" tab with Done ticks | Makes indite a to-do app (own reminders are now built: founder decision 10 Oct) |
| Our own translator / speak-the-translation loop (for now) | 14–15 s per turn on a flagship; weak demand evidence; Google Translate hand-off instead |
| Voice cloning, live interpreter, own Indian-language voices, NLLB | Non-commercial licences, fraud/consent risk, or too slow |
| "Most words wins" re-run on imports | Picked noise gibberish; 15-min test got worse (25.5% → 30.6%) |
| Slower Prime model, q8, beam search by default | Tested: no better, or slower, or worse in noise |
| Noise cleanup before transcription | Hurts accuracy |
| Android's built-in recognizer; ML Kit GenAI speech | Devanagari output, short clips, crashed on OnePlus; Pixel-only alpha |
| Dubbing, language learning, call-centre QA, bookkeeping, creator-subtitle focus | Different products or crowded markets |
| Search across transcripts (web), in-browser recording, YouTube import, meeting bot, collaboration, editing audio by editing text | Out of scope for now |
| Bookmark a moment while recording; pin / tags / folders | Unproven; search exists |
| Wispr: AI clean-up on every dictation (Auto Cleanup) | ~6 s AI call on a 0.8-1.6 s transcription: 4-7x slower, spends the founder's own quota, and types the rewrite instead of the raw text. Wispr withdrew its own "High" level |
| Wispr: transforms on a hotkey; command mode; stacked messages | "Ask anything" already exists; the new part is reading and replacing other apps' selection. A misheard "delete that" has no undo |
| Wispr: show/hide the Dock icon | Harmful: indite is a normal app only while its window is in front, so the pill would stop appearing over full-screen apps |
| Wispr: mute music while dictating; launch at login as a LaunchAgent | Unasked; a LaunchAgent would lose Accessibility (Login Items -> indite.app keeps it) |
| Wispr: scratchpad with its own hotkey | The window is already one (Dictations, To do, stars, search) |
| Wispr: read the IDE's open file for code variable names | Continuously reading another app's document; the free 80% is ~20 identifiers in the Dictionary |
| Wispr: team dictionary, cloud sync, referrals | Breaks audio-never-leaves, zero-cost and no-account |
| Personal-assistant layer (send to Slack / Gmail / Drive, notify people, chase ETAs) | Claude and Gemini already do the actions through their own connectors; it needs sign-ins, an online AI and breaks the no-internet phone rule. Sharing to Claude already exists. Revisit: WhatsApp pre-fill if testers ask (founder question, 16 Oct, critic-reviewed) |

## Competitors noted

- Truecaller AI call recording: Hindi/English transcripts, ₹75/month (calls only; price reference)
- Wispr Flow: cloud; Android bubble uses accessibility; Hinglish since 2026; ₹320/month; India 14% of installs, ~2% of revenue
- Sarvam Edge: on-device models for 10 Indian languages with phone makers (Feb 2026); the main threat to the offline edge
- Google offline Live Translate: Pixel 9–11 only, English on one side; BhashaGo: offline Indian-language translator, <1k installs
