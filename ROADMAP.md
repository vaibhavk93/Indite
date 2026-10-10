# indite roadmap

Last updated: 2026-10-10 (after the v0.6 phone test). **This file is the one roadmap.** The roadmap page
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
| Wispr Flow comparison | Done: password/OTP guard built; snippets later; no accounts, streaks or per-app tone |
| Mac web app: restarting still starts jobs from scratch (PLAN §5) | Next (web) |
| Check whether Sarvam Edge / Gboard already do Roman Hinglish | Research, before testers |
| Repo has no LICENSE (public repo) | Founder decision, before testers |
| Home-screen widget / quick tile for dictation | Re-assess (dictation now exists) |
| Native Mac app vs the web app | Not assessed |
| Restore notes on a new phone (export exists, import doesn't) | Unreviewed idea |
| Battery use of the always-on bubble / keyboard | Unreviewed; measure before testers |
| One setup checklist for all permissions | Unreviewed; fits the try-it onboarding |
| Play internal testing track for testers (instead of sideloaded APKs) | Unreviewed |

## Now

1. **Phone test of the latest build** (running): speaker labels per sentence (goal: well above 52%), 15-min file back to ~25%
   errors, live numbers unchanged.
2. **Founder's 20-minute hand check** (12 items: bubble, auto-paste, Find who spoke, Make notes, Action items, Translate,
   practice scores, export, "no speech" screen). Then fix what fails.
3. **Speaker labels before testers:** founder listens to the real 15-min interview split (1:34–1:47, 7:00–7:14, 13:07–13:28
   should be the second speaker; 0:20–0:55 the main one); 2–3 real recordings with hand-marked turns.
   Known limits: the count guess is fragile on real audio (you confirm it); very short replies ("haan") can get the wrong
   label; overlapping speech isn't handled.
4. **Check Google Translate with spoken Hinglish** (2 minutes): decides whether the hand-off is enough.

## Next build (planned, critic-reviewed)

**Look and feel** (research: colours and font are fine; what feels "AI-made" is no motion and everything looking the same):
1. Screen transitions (S) · 2. "Done" moment: check-mark + haptic on the note screen (S) · 3. Writing dots → real progress,
paragraphs fade in (S) · 4. **Settings split into 6 groups:** Look & feel, Dictation, AI, Word fixes, Storage & privacy, About (M)
· 5. Stop button pulses with your voice (S) · 6. Record button press spring (S) · 7. Home: plain rows instead of boxed cards (S)
· 8. Bigger title, Today / Yesterday headers, one-line help text (S) · 9. Custom icons (S) · 10. Animations respect
"Remove animations" (S). Cut: framework upgrade, shared-element transitions, Lottie/Rive, settings search.

**Your own API key (personal build first):** first a 1-hour test: 3 free OpenRouter models × 5 real Hinglish notes vs Claude
on the Mac. Stop if clearly worse. If good: OpenRouter only; order = Mac → key → your AI app; on error, a "Send to my AI app"
button; no "Both" setting. ⚠ About half the free models may train on what you send: one-time warning before meeting notes.
Public app stays internet-free; a tester-only key build only if interviews ask (15–25 h).

## Before testers

- Try-it screen for first-time users; smaller install (model downloads on first open)
- Test on a ₹15k phone (parked by the founder; still the biggest unknown)
- Give it to 10–20 people; interviews alongside; ask an open question about translation; sign-up asks "Android or iPhone?"

## Next

- **Speaker labels in the web app** + rename: reuse the phone recipe instead of pyannote/Hugging Face (Sarvam's paid labels stay
  the fallback). The old "speaker test 2" (pyannote on the 56-min file) is superseded.
- **Windows support** (founder decision): setup script, whisper.cpp Windows build (CUDA / Vulkan / CPU); speed unmeasured, needs
  a real Windows PC.
- **v0.8 · Your own AI key:** separate "indite AI" build with the user's own key (OpenAI / Gemini / OpenRouter / Anthropic); the
  default app stays offline. Only if testers want in-app AI. Plus a test of a small on-phone AI (Gemma) on 20 real brain dumps.
- Action items v2: real dates ("kal" → a date) once JSON modes exist; practice "Your tries" history (after 3 testers retry)
- Engine choice from `bench` on real clips (3–5 files per user group, plus a fixed hand-checked test set)
- **Choose when each transcript is deleted** (founder request): 30 days / 1 year / 3 years / never
- Custom vocabulary (names, brands); Indian formatting (₹, lakh, dates, numbers)
- Optional "fix unclear bits with Sarvam" switch for the local engine (off by default; ~₹0.40 per file; those bits leave the Mac)
- Subtitle line-length setting (check the 56-min SRT first)
- Later bubble ideas, only if testers ask: snooze for 10 min, snippets, filler-word removal, spoken "new line"

## Later

- Better Hinglish model (fine-tuned) to close the gap to Sarvam; phone's AI chip for speed
- Public Hinglish test set and leaderboard
- Indian English, then Marathi/Bengali, then Tamil
- Translation of our own (on-phone engine + spoken output): only after 3 real people ask; then a 1-day test (Google Translate vs
  Tencent Hy-MT2 on 30 Hinglish sentences, RAM check on a cheap phone). Research: reports/Offline translation and speech output.md
- Accessibility add-on in the public build (decide after Play's review cost is known)
- Play Store launch (asset packs, newer Android target, policy declarations for overlay, special-use service, keyboard)
- Hosting, Google login, payments (Razorpay / UPI), installable web app, DOCX export, batch upload, Devanagari output,
  subtitle burn-in, autosave to server, "Sign in with ChatGPT" (apply via OpenAI's form)
- **iPhone app** (critic-reviewed 2026-10-10): not now. Trigger: 5+ testers ask for iPhone (tester sign-up asks "Android or
  iPhone?"). First step then: a 1-day speed test of whisper.cpp's own iOS example on a real iPhone (free Apple ID install).
  iOS blocks the floating bubble, mic in keyboards and auto-paste; the $99/yr developer account is needed to give it to others.

## Not doing (for now), and why

| Idea | Why not |
|---|---|
| Claude or Gemini subscription login in the app | Their terms forbid it; the founder's Mac route does it legally |
| Deepgram; AI or cloud fallback on our own keys | Breaks zero-cost and privacy rules |
| Live voice roleplay; PM coach as a product | Too slow offline (10–15 s per turn); crowded; kept as "Practice answer" |
| Rough text while you speak; shading unsure words | Draft models write Hindi script; confidence doesn't match real mistakes |
| Our own call recorder | Banned on Play since 2022; import recordings instead |
| Full typing keyboard; model in a laptop browser | Endless work; no browser-ready model |
| Bubble only when a keyboard is up, without accessibility | Not possible on Android 11+; the indite keyboard covers it |
| Hold-to-talk on the bubble | Clashes with drag and cancel; first words could be cut off |
| A "Tasks" tab with Done ticks; our own reminders | Makes indite a to-do app; tasks go to the user's calendar or task app |
| Our own translator / speak-the-translation loop (for now) | 14–15 s per turn on a flagship; weak demand evidence; Google Translate hand-off instead |
| Voice cloning, live interpreter, own Indian-language voices, NLLB | Non-commercial licences, fraud/consent risk, or too slow |
| "Most words wins" re-run on imports | Picked noise gibberish; 15-min test got worse (25.5% → 30.6%) |
| Slower Prime model, q8, beam search by default | Tested: no better, or slower, or worse in noise |
| Noise cleanup before transcription | Hurts accuracy |
| Android's built-in recognizer; ML Kit GenAI speech | Devanagari output, short clips, crashed on OnePlus; Pixel-only alpha |
| Dubbing, language learning, call-centre QA, bookkeeping, creator-subtitle focus | Different products or crowded markets |
| Search across transcripts (web), in-browser recording, YouTube import, meeting bot, collaboration, editing audio by editing text | Out of scope for now |
| Bookmark a moment while recording; pin / tags / folders | Unproven; search exists |

## Competitors noted

- Truecaller AI call recording: Hindi/English transcripts, ₹75/month (calls only; price reference)
- Wispr Flow: cloud; Android bubble uses accessibility; Hinglish since 2026; ₹320/month; India 14% of installs, ~2% of revenue
- Sarvam Edge: on-device models for 10 Indian languages with phone makers (Feb 2026); the main threat to the offline edge
- Google offline Live Translate: Pixel 9–11 only, English on one side; BhashaGo: offline Indian-language translator, <1k installs
