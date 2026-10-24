# indite roadmap

Last updated: 2026-10-24. **This is the one roadmap.** Design rule: every screen follows `docs/DESIGN.md`. Order and status live only here. Other planning files hold
detail and are not roadmaps: `docs/ROADMAP_DETAIL.md` (AI review design), `docs/MAC_PLAN.md` (Mac vs Android vs Wispr),
`docs/WISPR_DEEPDIVE.md` (measurements), `docs/AI_MODES.md` (AI spec), `PLAN.md` (decisions and test results),
`docs/FOUNDER_REQUESTS.md` (every request and its status), `docs/ROADMAP_ARCHIVE.md` (the old 10 Oct snapshot).
**If any of them disagrees with this file, this file wins - fix the other one.** Every item passed an independent
critic, or is the founder's own decision. The published page (https://claude.ai/artifact/GuCGtX4TJeASaS2RpGFS4q) was
republished from this file on 18 Oct.

**Goal:** speak the way India talks, mixing Hindi and English, and get correct Roman-script text, privately and offline.
Edge: offline, private, Roman Hinglish, on any Android brand. Cloud tools (Wispr, Sarvam) are faster and more accurate today.

| Where we stand | indite now | Best rival |
|---|---|---|
| Words wrong, clean Hinglish (synthetic, Mac) | 13.0% | Sarvam cloud 6.0% |
| Live dictation on the phone: wait after a pause | 8.9 s median (was 38.5 s) | Wispr cloud ~1–2 s |
| Live dictation on the phone: words wrong | 16.9% (was 25.8%) | — |
| Speaker labels, offline, any Android | 98% of turns on the Mac test (phone re-test: no result recorded) | Pixel / Galaxy only |
| Works with no internet | ✓ | Wispr, Sarvam: no |

---

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
- Mac has, Android doesn't: the text card with AI buttons; Insights page; meetings with system audio (Play bans call recording).
- Android is missing: Improve, Ask anything, Make it a prompt (#230); swear masking; an Insights page; any AI answer actually received.
- Naming: Android says "Word fixes", Mac says "Dictionary" - pick one (founder).

---

# Mac app

## Mac: done

- **23-24 Oct (🧪 built, not yet checked by the founder):** pill and text card hidden from screen shares (Zoom, Meet, Loom,
  QuickTime); **Select several notes → "Ask AI combined"** (Finder-style picking, the AI reads the picks as one note;
  same on Android, build not cut); text card restyled; **AI cost under each answer + a this-month total** (an estimate:
  real token counts, a typed-in price table checked against Anthropic's pricing page on 24 Oct; OpenAI prices not
  re-checked); pill says "warming up" on cold start and a failure puts its reason on the card; **design clean-up in 9
  passes** (shared colours and type sizes, themed button hints, one button family, menu subtitles, Settings inputs,
  empty pages; rules in `docs/DESIGN.md` v2). Android: "typed in" fallback now logs its reason (#299).
- **Dictation anywhere:** hold a key (or tap twice for hands-free), speak, text typed in ~0.8 s; Esc cancels; smart
  output (typed into a text box, else copied); typed words **also on the clipboard** (setting, 17 Oct); long holds cut
  at quiet points; password boxes never typed into; long text ~40x fewer key events (16 Oct); pill with live levels.
- **Self-contained app for other Macs (17 Oct):** `./mac/build_portable.sh` → `dist/portable/indite-mac.zip` (630 MB, macOS 14+, Apple Silicon), checked by `mac/portable_check.py`; read-me and Help inside. **Bug sweep (17 Oct):** 4 high, 5 medium and the low bugs from an end-to-end test fixed; UI review items 1-21 done.
- **Calls (17 Oct):** when Zoom, Teams, Slack, FaceTime, WhatsApp or Webex starts using the mic, the card asks "Record this call?" (never records itself; browser calls not noticed). **Your own words to hide** next to swear masking. **Setup** offers the card as an optional step.
- **Text card after a dictation:** your words, then **Ask AI · two AI buttons (your most used, or picked in Settings) · To do** (17 Oct); takes
  clicks only after the pointer moves onto it; answers wrap and are copied the moment they land.
- **Notes window:** Dictations, Meetings, Files, To do, Dictionary, Insights, Settings, Help; stars, search, backup and
  restore; play or show a kept recording (17 Oct); one copy icon everywhere (17 Oct); swear masking keeps the real
  word stored (16 Oct); Fix a word also fixes the note it was made on (17 Oct).
- **Dictionary:** your word fixes; refuses bad entries and says why; examples incl. shortcuts like an address (17 Oct).
- **Meetings and files:** mic + system audio, live text, back-to-back meetings with working dots (16 Oct); who spoke,
  with renamed speakers in copy and export (17 Oct); files transcribed in the app; text and subtitle export.
- **AI on a note (your own Claude login or key):** 11 actions incl. Improve, Make it a prompt, Translate, Ask anything;
  every answer copied when it lands (17 Oct); a consent step before anything leaves the Mac; AI use in Insights.
- **Insights:** grouped as Usage / Speed / Where & when / Meetings, files & AI; typical and slow wait (17 Oct).
- **Reliability:** a stuck microphone restarts indite by itself (worked for real, 17 Oct); the app no longer breaks
  its own signature; crashes leave a stack in the log; stale LIVE cleared; who-spoke errors titled correctly.
- **Groundwork for AI review:** per-word confidence (fetched only when needed), Dictionary checks (17 Oct).

**Engine, web app and tools (shared with the Mac app):**

- **Native Mac app (15 Oct):** hold a key, speak, text typed in ~0.8 s; pill, history window, settings, mic fallback.
  Kept separate from Android (own model link and spelling list). Built 15 Oct: personal word fixes, Esc cancel, long holds
  cut at quiet points (60 s: 75% → 19% words wrong). Then: password guard, fix a word from history,
  Transcribe a file (opens the web app). Plan and parity table: `docs/MAC_PLAN.md`.
  15 Oct evening: notes/stars/To do, files in-app, meetings (mic + system audio), who spoke, AI on notes, backup,
  setup screen. Dropped: undo-by-backspace, voice "press enter", command mode (no AI route)
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


## Mac: next, in order

| # | Item | Who | Size | Gate / note |
|---|---|---|---|---|
| 1 | **Real speech set** (plan: `docs/SPEECH_SET_PLAN.md`, critic-reviewed): first grow the Dictionary to ~20 names of 6+ letters; keep dictating normally with audio kept until there are 50 recordings; then I give you ~15 sentences to read aloud (names, numbers, ₹, Hinglish) and we discuss; you type out what you really said for ~35 of your own; I score all 50 | Founder + me | ~1 day | Unlocks #3 and #6, and every accuracy claim (Android's too) |
| 2 | **Founder checks:** two real calls back to back; dictation delay while who-spoke runs (a priority rule only if >1.5 s); real-use checks - full screen, dragging the window by its top strip (founder: "dragging is not working", 17 Oct - window or pill, to confirm), hands-free over Terminal, ⌃⌘V paste-last (Slack and VS Code typing: confirmed working, 17 Oct); and say yes/no to the 🧪 items: pill size and glass look, Insights grouping, the text card, the UX fixes, Mark likely mistakes | Founder | ~30 min | Built 15-17 Oct, not confirmed by a person |
| 3 | 🧪 **Mark likely mistakes (AI review step 1, offline) - built 17 Oct, on for the founder behind a setting; synthetic bench: 0.19 false flags per 100 words, 4 real catches ("crossin" → Crocin, "jaamton" → Zomato):** flags from the confidence score + Wispr's skip list, ▶ play that bit, Fix + "Always fix?" (offered after the 2nd identical fix, with a warning when the words appear un-fixed in other notes), a fix log, and the engine's original text kept so a bad rule can be undone | Me | done; gate open | Ships to others only if ≤1 false flag per 100 words on the real set |
| 4 | 🧪 **Fixes count on Insights** (W3, built 17 Oct): "likely mistakes fixed · N per 100 words" and how many were not mistakes; hidden until there is data | Me | done | The number should fall over time |
| 5 | ✅ **Engine-hint test** (W4, run 17 Oct on 60 synthetic clips): words wrong 24.9% → 24.7%, Dictionary names right 4/10 → 5/10, nothing invented. **Not shipped:** one word is too small to trust. Re-run on the real speech set | Me | done | Re-test with #1 |
| 6 | 🧪 **AI review step 2 - built 18 Oct behind a switch** (`ai_review`, on for the founder only): Ask AI → "Review with AI" lists likely mistakes as flags with Fix / Always fix / Not a mistake; guards: words must be in the note exactly, no low-sure items, ≤ 10, never applied without a click; dictations only. **Ships to others only if ≥ 70% of suggestions are right on the scored real set (D15).** · ❌ **Filler-word removal dropped (18 Oct, critic):** in 310 real dictations um/uh appear 0 times; W5's own fillers (basically, you know, actually) in 7 of 310 vs the 103 its test needed | Me | done; gate open | Measured with D15 |
| 6b | 🧪 **In-app player - built 17 Oct** (founder #279/#280/#283, plan `docs/PLAYER_PLAN.md`): Listen view in indite's own look, lit line + **lit word** (kept while paused), click a line or word to jump, Edit / Copy / ▶ line with Undo; **meeting tracks now share one clock** and play **Both** together (meetings recorded from 17 Oct); word times rebuilt when a note's words change | Me | done | Founder check |
| 6c | ✅ **Test copy of indite - built 17 Oct** (founder rule #282): `python mac/testcopy.py start/eval/cmd/stop`; own data and engine (port 8712), no keys / mic / typing / clipboard / pill / card / menu icon / focus. Its window can't take pictures (headless Chrome does that). Typing and pill tests still need the real screen with the founder's OK | Me | done | — |
| 7 | 🧪 **Parity with Android - built 17 Oct:** edit a note's text + Undo (⋯ → Edit text); edit a meeting line by line (Listen → ✎); **per-line speaker fix and join with the next line** (Listen → click the speaker name), each with Undo; lines remember their track, so a fixed speaker still plays the right audio | Me | done | Founder check |
| 8 | **Leadership demo video** - on hold (founder, 17 Oct); when it resumes: pick the length (3:00-3:30 or ~9:30), freeze the code, dry run, record | Founder + me | ½ day | — |

## Mac: later

- ₹ / lakh-crore formatting (unproven)
- Live clean-up while dictating with a local model (MAC_PLAN P6; needs a 30-dictation test first)
- 7-day assistant test with Claude Code over your notes (#252, waiting for your yes) · note-before-instructions order
  on the other AI actions (measure first) · ✅ Haiku model id checked 17 Oct (`claude-haiku-5-5`, current)
- From the Wispr comparison: flags from low confidence alone (~3 h) · two-step AI review (only if step 2 < 70%) ·
  topics in Insights · regional name and place packs · a whispered-speech test
- Insights when the data exists: weekday pattern (~4 weeks), speakers found, an honest accuracy measure

## Mac: parked

Signing certificate (until a second person gets the app) · Intel Macs · Practice / Brain dump (until checked on Android)
· voice "to do" command and to-do tags (revisit at ~30 real to-dos)

---

# Android app

## Android: done (build 29 on the founder's phone, all phone gates passed 14 Oct)

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


## Android: next, in order

**⚠ Every new Android build waits on the release-key switch, which the founder parked.** Item 1 needs no build.

| # | Item | Who | Size | Gate / note |
|---|---|---|---|---|
| 1 | **No build needed:** (OpenRouter training already off - founder, 17 Oct) a new OpenRouter key *or* Tailscale for the Mac route (either gives the phone its first AI answer); the 1-hour model test (3 free models × 5 real notes vs Claude, run on the Mac); record part of the real speech set on the phone | Founder (+ me for the test) | ~2 h | — |
| 2 | **Un-park: hand-check build 29**, above all that backup → restore works; plus the reminders 3-day check | Founder | ~1 h | Must pass before the key switch: a key change forces an uninstall, which deletes the phone's notes |
| 3 | **Release key:** 1 h research on key rotation (may avoid the uninstall; unproven), then the real key, backed up in two places | Me + founder | ~2 h | Unlocks every build below |
| 4 | **One parity build:** Improve, Ask anything, Make it a prompt; swear masking (real word stored); Dictionary length cap (duplicates already handled); **auto-learn refuses one-letter wrong words** (today two identical edits of "bhi" → "B" would rewrite every later "B") | Me | M | — |
| 5 | **AI review step 1 on Android:** add per-word confidence to the whisper.cpp bridge (native rebuild), then the same flags as the Mac | Me | M | Only after it passes on the Mac |
| 6 | **Batch A** (Show only [name], recovery banner, find & replace, WhatsApp date titles, permissions checklist) + **look-and-feel top 10** | Me | M | Batch A's old "after build 10" gate is replaced by item 2 |
| 7 | **Before testers:** ₹15k phone → Play internal testing → model download via Play asset packs (smaller install; the public build has no internet, so asset packs are the only route) → try-it onboarding, newer Android target, battery check, restore on a new phone, strip personal-only features | Me + founder | L | Then 10-20 testers with interviews |

Look-and-feel top 10 (item 6): screen transitions · "done" tick + haptic · real progress instead of writing dots ·
Settings in 6 groups · Stop button pulses with your voice · Record button spring · plain rows instead of cards ·
bigger title with Today / Yesterday · custom icons · all of it respects "Remove animations".


## Android: later

- Insights page · voice "Me" (#64, consent first) · overlap marking (gate: >3% of words lost in 3 real recordings) ·
  widget / quick tile · a "Your data" screen · merge speakers · speed line and space-left while recording · search
  jumps to the paragraph
- Bubble only when a keyboard is up (needs the accessibility add-on; public-build decision pending) · editable AI
  prompts · speak the translation aloud (waits for 3 real asks) · per-phone benchmark (only for a ≥1.5x gain)
- Tighten the speech detector so noise never reaches the model (10 Oct ask, still open) · save AI answers that come
  back from other apps without pasting (half built: Mac route only)
- **Open checks:** founder's speaker-label listen-check · whether Sarvam Edge / Gboard already do Roman Hinglish
  (before testers) · battery use of the bubble and keyboard (measure on the tester build)

## Android: parked (founder, 16 Oct)

₹15k phone (just before testers) · check how long WhatsApp voice notes get (parked by the founder) · build 29 hand-check and the release key (both block every new build; see #2-3).

---

## Personalisation: making indite yours (founder request #188, #227; critic-reviewed 16 Oct)

| Layer | What it does | Status |
|---|---|---|
| **1. Your words** | Dictionary / word fixes replace what the engine gets wrong ("in diet" → "indite"). Android also offers a fix after the same edit twice | **Built, both.** The only proven gain |
| **2. Learn from your corrections** | AI review flags likely mistakes; each accepted fix goes to the log; the 2nd identical fix offers "Always fix?" → Dictionary | Mac next #3 (🧪 built), #6; Android next #5 |
| **3. Prime the engine with your words** | Your names and brands given to the engine before it listens (W4) | 2 h experiment, expected to drop |
| **How we know it works** | Fixes made per 100 words (W3) going down over time, and a re-score of the real speech set | Mac next #4 |

**Cut, with reasons:**
- Separate "style rules" (e.g. "kr rha" → "kar raha"): that is just a word fix plus the existing everyday-spelling switch.
- Training the speech model on each user's voice: ruled out before (#188: no trainer, no memory to spare), it needs
  hours of corrected audio (the real set is minutes), the engine can't load a per-user add-on, and every user would
  need a Mac. The route kept instead: one better shared Hinglish model (Later).
- "Rewrite in my style" with AI: nobody has asked; needs internet. Later, if 3 people ask.

---

---

## Both apps, later

- Better Hinglish model (fine-tuned, shared by everyone); phone's AI chip for speed
- Public Hinglish test set and leaderboard
- More languages, one at a time: the tester sign-up asks which; a language starts at 5+ asks (2-4 weeks each)
- Choose when notes are deleted (#53) · action items with real dates ("kal" → a date) · Devanagari output switch
- Own translation (after 3 asks) · Windows (the founder has a Windows PC; waits for focus - Mac first, 14 Oct) · web app: resume after a crash, speaker labels
- Play Store launch; hosting, login, payments · iPhone (when 5+ testers ask)
- Engine choice from `bench` on real clips · optional "fix unclear bits with Sarvam" switch (off by default, ~₹0.40
  per file, those bits leave the device) · subtitle line-length setting · own-key AI build for testers (only if
  interviews ask)

- "Sign in with ChatGPT": apply to OpenAI's programme (only if testers want ChatGPT inside indite)
- **Founder decisions waiting: see `docs/DECISIONS.md`.** These have to be solved too; each one blocks or shapes items above.
- **Competitor research:** plan and the Google voice typing study in `docs/research/COMPETITORS.md`; ideas from it come back here as adopt / test / skip.

---

## Not doing (for now), and why

| Idea | Why not |
|---|---|
| Claude or Gemini subscription login in the app | Their terms forbid it; the founder's Mac route does it legally |
| Deepgram; AI or cloud fallback on our own keys | Breaks zero-cost and privacy rules |
| Live voice roleplay; PM coach as a product | Too slow offline (10–15 s per turn); crowded; kept as "Practice answer" |
| Rough text while you speak; shading every unsure word | Draft models write Hindi script; confidence alone doesn't match real mistakes (it *is* used as a gate in AI review step 1, Mac next #3) |
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
| Saying "to do …" to send a dictation straight to To do (founder idea, 17 Oct) | Fires on normal sentences ("I want you to do…", "To do this…" are in the founder's own dictations to Claude) and has no undo - the same reason command mode is out. Existing routes take 2 taps. Revisit after 2 weeks if real to-dos pass ~30; smaller option: a "To do" button on the text card |
| To do tags: Office / Personal / Daily / Rules (founder idea, 17 Oct) | 2 to-dos exist today. Revisit at ~30 real to-dos; search the To do page first. "My rules" fits notes better than to-dos |
| Personal-assistant layer (send to Slack / Gmail / Drive, notify people, chase ETAs) | Claude and Gemini already do the actions through their own connectors; it needs sign-ins, an online AI and breaks the no-internet phone rule. Sharing to Claude already exists. Revisit: WhatsApp pre-fill if testers ask (founder question, 16 Oct, critic-reviewed) |

## Competitors noted

- Truecaller AI call recording: Hindi/English transcripts, ₹75/month (calls only; price reference)
- Wispr Flow: cloud; Android bubble uses accessibility; Hinglish since 2026; ₹320/month; India 14% of installs, ~2% of revenue
- Sarvam Edge: on-device models for 10 Indian languages with phone makers (Feb 2026); the main threat to the offline edge
- Google offline Live Translate: Pixel 9–11 only, English on one side; BhashaGo: offline Indian-language translator, <1k installs
