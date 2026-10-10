# Founder requests: everything you asked for, and where it stands

**Last updated:** 2026-10-10

## What this is

- **One list of every request you made** in every chat about indite, from the first PRD (8 Oct) to today.
- Each request appears **once**. Repeats are merged and marked "asked again on <date>".
- Each row says what you asked, when, and what happened: built, pending, or dropped, and why.
- Sources: all chat transcripts, `git log`, `ROADMAP.md`, `PLAN.md`, `docs/HANDOFF.md`, `docs/WORKLOG.md`,
  `docs/AI_MODES.md` and the Android code.

## How to use it

1. **Looking for a feature?** Find its theme below. Or search for a word (e.g. "bubble", "reminder").
2. **Want what's left?** Search for ⏳, 🔬 or ❓.
3. **Something missing or wrong?** Tell the coding agent. It fixes this file in the same session.

**⚠ Remember:** "Built" means the code is in git. It doesn't mean it's been tested on your phone. 🧪 marks
those that haven't been.

## Status legend

| Mark | Meaning |
|---|---|
| ✅ | Built (version or commit given), or the question was answered |
| 🧪 | Built, not yet tested on the phone |
| 🟡 | Partly done (says what's missing) |
| ⏳ | Pending (planned) |
| 🔬 | Researching, or needs a decision |
| ❌ | Not doing (reason given) |
| ❓ | Unclear (needs your clarification) |

Versions: "v0.6" = app version; "build 9" = the 9th installed build (tag `build-9`); a 7-letter code like `3d42717`
is a git commit.

---

## Summary

| Status | Count |
|---|---|
| ✅ Built / answered | 118 |
| 🧪 Built, not tested on phone | 11 |
| 🟡 Partly | 16 |
| ⏳ Pending | 10 |
| 🔬 Researching / needs decision | 9 |
| ❌ Not doing | 6 |
| ❓ Unclear | 2 |
| **Total** | **172** |

**Bottom line:** most of what you asked for is built. What's left falls into four groups:

- **Things only you can do:** OpenRouter key, Tailscale, recordings, the ₹15k phone, the speaker listen-check.
- **Built today, not yet on your phone:** the keyboard redesign, the swipe-hint animation, the italic subtitle and the bubble's new drag (`963545b`, build 10 being prepared).
- **Research done today:** value-adds per journey (top 8, critic-reviewed) and Indian languages in Roman script (not now; demand check first). See the rows below.
- **Parked on purpose, with a trigger:** iPhone, translation by voice, overlapping speakers, Windows.

---

## Main table

### 1. Engine & accuracy

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 1 | **Build from my PRD** | Analyse the "Adaptive Speech Intelligence" PRD, research improvements, plan in simple language with flow charts and mocks | 8 Oct | 🟡 | Plan page made. Scope narrowed (with you) to offline Roman Hinglish. Built: local engine, pause cutting, bad-piece re-runs, flags. Not built: noise profiling, model ensemble, enhancement routing, API/enterprise |
| 2 | **LLM use and cost** | Will we use an LLM, for what, what will it cost, anything free? | 8 Oct | ✅ | Answered. The LLM is never the transcriber. It's only used for notes, via your own AI app, your own key or your Mac. Engine is free (whisper.cpp) |
| 3 | **Free vs paid budget** | Can it be free, what do we give up vs paid, by how much? | 8 Oct | ✅ | Answered. Free local engine: 13.0% words wrong vs Sarvam cloud 6.0% (synthetic Hinglish test) |
| 4 | **Transcript pipeline to PRD point 6** | Focus on the transcript pipeline first, steps 4–6 | 8 Oct | ✅ | Built on Mac (`a04f895`) |
| 5 | **Roman script; name it "indite"** | Output in Roman letters; product name indite | 8 Oct | ✅ | Built |
| 6 | **Shrink the model with whisper.cpp** | Make the model smaller | 8 Oct | ✅ | 5-bit model, ~0.75 GB RAM on Mac; phone uses q5_K (574 MB) |
| 7 | **Local model as default** | Free local model first; Sarvam optional (you added the Sarvam key) | 8 Oct | ✅ | Built |
| 8 | **Compare local vs Sarvam** | You ran both; analyse quality. Should I run Sarvam too? | 8 Oct | ✅ | Analysed. Sarvam more accurate, paid, cloud |
| 9 | **Improve the free model** | Find ways, try them all and compare; try Prime; "go with option 2" | 8 Oct | ✅ | Tested. Loops 73 → 4 by cutting at pauses and re-running bad pieces. Prime: slower, worse in noise (26.2%) so not used |
| 10 | **How does OnePlus transcribe?** | Check what models OnePlus uses, to learn from it | 9 Oct | ✅ | Researched (`d20746f`) |
| 11 | **Mac accuracy test** | Run the accuracy test on Mac too | 9 Oct | ✅ | `indite bench` + `bench_synth/` synthetic Hinglish benchmark |
| 12 | **Deep research: speed + accuracy** | Research all options on the web, then discuss what gives a real edge | 9 Oct | ✅ | Report: `reports/Hinglish speech speed and accuracy.md`. Everyday spelling cut errors 18.1% → 13.0% |
| 13 | **Flag non-Roman script** | Add the non-Latin script flag (e.g. Cyrillic "У нас" turned up) | 9 Oct | ✅ | `bad28ba` |
| 14 | **Noise not separated** | Noise isn't being separated properly; fix it | 9 Oct | ✅ | Neural speech detector (Silero) in v0.2. Noise *cleanup* itself is not used: it hurt accuracy |
| 15 | **Word fixes** | Can we suggest word fixes (PTM → Paytm)? | 10 Oct | ✅ | v0.4, with "Always fix?" |
| 16 | **Same audio, different text: find the root cause** | Same model and voice give different text; find out why and fix it | 10 Oct | 🟡 | Cause found: a speed setting (flash attention) read leftover audio from earlier pieces. Turning it off fixed it (Mac 27.6% → 25.1%) but added ~6 s per sentence (9.1 → 14.8 s). **So it's back on (`9af355a`) and differences can return.** A fix that keeps the speed (window rounded to 256) is being tested |
| 17 | **Our own models?** | Would building our own model help? | 9 Oct | 🔬 | Later, and only if dictation is still over ~5 s after cheaper fixes. A fine-tuned Hinglish model is in "Later" |
| 18 | **Use users' good phones for free** | Use high-end phones to do the work free, instead of paid models | 9 Oct | ✅ | Everything runs on the phone. Per-phone tuning: see #24 |

### 2. Speed

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 19 | **Very, very fast dictation, like Wispr Flow** | Speak and get text almost at once, with the best accuracy | 9 Oct | 🟡 | Wait after a pause on the phone: 8.9 s median (was 38.5 s). Wispr: ~1–2 s, but it runs in the cloud. Faster offline needs a phone AI chip or a smaller model (Later) |
| 20 | **How do Wispr Flow / GitHub apps get their speed?** | Research them and copy what works | 9 Oct | ✅ | Researched. Their speed comes from cloud servers, which breaks our offline/privacy edge |
| 21 | **Why a phone speed test?** | Why are we running this, when the task is speech-to-text? | 9 Oct | ✅ | Answered. It checks whether the phone can keep up offline. Results: 0.54x → 0.63x → 0.93x on long audio (q5_K) |
| 22 | **Use 6 cores** | Build the voice-notes app with 6 cores (fastest in your test: 13.7 s) | 9 Oct | ✅ | Built v0.1 |
| 23 | **More speed** | Still ~0.63x and 39 °C; anything else? | 9 Oct | 🟡 | q5_K format + audio window sized to each piece: 0.93x. Phone AI chip is a later option |
| 24 | **Benchmark per phone, one app for all phones** | Pros and cons, then your opinion | 9 Oct | 🔬 | Later. Only once budget-phone logs show a gain of ≥ 1.5x from a different setup |
| 25 | **Test on a ₹15k phone** | You parked borrowing one (9 Oct); it's back in the plan | 9 Oct | ⏳ | Planned alongside build 10 (~2 h). **Biggest risk to the plan.** Waiting on you to get the phone |
| 26 | **Check WhatsApp voice-note lengths** | Parked by you on 9 Oct | 9 Oct | ⏳ | Parked |

### 3. Dictation: keyboard & floating mic

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 27 | **Dictate in the app** | Open the app, turn on the mic, speak, get text fast | 9 Oct | ✅ | v0.1 (text after each pause) |
| 28 | **Dictate into any app** | When there's a text box, dictate into it the way Wispr Flow does | 9 Oct | ✅ | Voice keyboard (v0.3) + floating mic (v0.5) |
| 29 | **Floating mic button like Wispr** | "Not yet built" | 9 Oct | ✅ | v0.5 |
| 30 | **Bubble: say no speech heard** | "indite didn't hear any speech" (asked again 10 Oct) | 10 Oct | ✅ | Fixed (`7c6fb4f`): the last piece was lost on stop |
| 31 | **Bubble: show processing** | Show that it's working, so I know to wait | 10 Oct | ✅ | Spinner while writing (`ddfb78b`) |
| 32 | **Paste straight into the box I'm in** | Text should land in the field I tapped | 10 Oct | ✅ | Personal build (accessibility). Public build: copy, or the indite keyboard types it |
| 33 | **Bubble only when a keyboard is up** | Show the bubble only when typing | 10 Oct | ❌ | Android 11+ doesn't allow this without accessibility. Possible later with an accessibility add-on (public build decision pending) |
| 34 | **Record, then copy with a separate icon** | Copy to clipboard with a second button | 10 Oct | ✅ | Green copy button on the bubble |
| 35 | **Keyboard shows its progress** | The keyboard had no recording → writing → pasted steps | 10 Oct | ✅ | `087931d` |
| 36 | **Smooth hold-to-cancel** | Cancel took over a second of holding | 10 Oct | ✅ | 0.4 s hold |
| 37 | **Bubble lost after drag to bottom** | It vanished, and turning it back on didn't bring it back (asked again 10 Oct ×3) | 10 Oct | ✅ | `7d4f227`: one switch; drag onto ✕ = off; quick settings tile "indite mic" |
| 38 | **Accessibility shortcut should toggle the bubble** | It toggled "Type into box for me" instead | 10 Oct | ✅ | `7d4f227` (personal build). Earlier the agent said this wasn't possible; it was fixed later |
| 39 | **One switch for the bubble** | Hidden = off; no "Tap to show" (you overrode the earlier "hiding is temporary" design) | 10 Oct | ✅ | `7d4f227` |
| 40 | **Better drag-down / drop zone** | Research and improve how the bubble is dragged away | 10 Oct | 🧪 | `963545b`: magnetic ✕ with a buzz on target, springy edge snap, remembers its position |
| 41 | **Keyboard redesign with wow factor** | "Doesn't look good at all": sophisticated, smooth, wow | 10 Oct | 🧪 | `963545b`: gradient mic orb with a voice halo, level bars, status pill, springy keys, "done" pop |
| 42 | **Learn from Wispr Flow's site and app** | Feature list, personal/work email; what we have, lack, should add (asked 10 Oct ×2) | 10 Oct | ✅ | Compared. Built: password/OTP guard. Later: snippets. Not doing: accounts, streaks, per-app tone |
| 43 | **Learn from FreeFlow** | github.com/zachlatta/freeflow: take what helps | 9 Oct | ✅ | PLAN §5c: "Always replace" list, raw text kept, raw text is the default |
| 44 | **Where dictated text goes** | Save both recording and text in the app, linked (may help train later) | 9 Oct | ✅ | Built. Training on it needs consent; other people's audio is never exported |

### 4. Recording & import

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 45 | **55-minute audio file** | Will a 55-min recording work? | 8 Oct | ✅ | 56-min file: 24.7 → 11.6 min to transcribe on Mac |
| 46 | **MPEG files** | Support .mpeg | 8 Oct | ✅ | Any audio/video |
| 47 | **"Invalid data" (avcodec) error** | Fix the crash on a damaged file | 8 Oct | ✅ | Damaged spots skipped instead of failing |
| 48 | **Record everything, transcribe at its own pace** | Capture all audio first; slow model catches up in parallel | 9 Oct | ✅ | Audio saved as you talk; queue runs behind |
| 49 | **Never start from scratch after a crash** | Save progress in parallel; resume old work | 9 Oct | 🟡 | Phone: ✅ resumes from the last piece. **Web/Mac: a restart still redoes the whole file** (⏳ PLAN §5) |
| 50 | **Plan for breaks in live dictation / translation** | What happens if something breaks mid-way? | 9 Oct | ✅ | Design rules in PLAN §5 |
| 51 | **WhatsApp voice-note decoding test** | "Go ahead with the voice note decoding test" | 9 Oct | ✅ | Share a voice note into the app (`d1ad57b`) |
| 52 | **Keep files 3 years** | 3 years, not 3 days | 8 Oct | ✅ | Built, with the deletion date shown |
| 53 | **Choose deletion time per transcript** | Custom delete date for each transcript | 8 Oct | ⏳ | Roadmap "Next": 30 days / 1 year / 3 years / never |
| 54 | **Copy, edit, and flag doubtful parts** | Copy button; fix mistakes; flag parts that may be wrong | 9 Oct | ✅ | v0.1–0.4 |
| 55 | **Delete one recording or one piece of text** | Delete a specific item | 10 Oct | ✅ | Card menu / swipe delete with Undo; delete one paragraph with Undo (`1044bf4`) |
| 56 | **Retry button on a card** | Only if it makes sense; otherwise skip it | 10 Oct | ❓ | Not built; no decision recorded. See Open questions |

### 5. Speakers

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 57 | **Separate the speakers** | Will it tell speakers apart? You approved free local speaker separation | 8 Oct | 🟡 | Phone: ✅ v0.4. **Web app: ⏳** (re-use the phone method) |
| 58 | **Speaker tests 1 and 2** | Run them (you accepted the model terms) | 8–9 Oct | ✅ | Test 1 done. Test 2 replaced by the phone method |
| 59 | **Speakers are not being told apart** | "We discussed this capability" | 10 Oct | ✅ | Fixed: labels per sentence. 51.7% → 96.7% on the phone test |
| 60 | **Find the speaker count automatically** | Don't make me say 2, 3 or 4 people; "guess and then confirm" | 10 Oct | ✅ | indite guesses, you confirm (`cf0337f`) |
| 61 | **Can I trust "Find who spoke"?** | It seems to work, but I can't check the quality | 10 Oct | ⏳ | You listen at 1:34–1:47, 7:00–7:14, 13:07–13:28. "Show only [name]" filter is in the next build |
| 62 | **Focus on one speaker among many** | If 4–5 voices come in at once, can we tell them apart? Feasibility test | 10 Oct | 🔬 | Folded into #63. Many voices at once is not handled today |
| 63 | **Keep the 2–3 s when people talk over each other** | Track them, or convince me it's not worth it | 10 Oct | ⏳ | Deferred, with a measurement plan: record 3 real conversations; build only if > ~3% of words are lost |
| 64 | **Recognise my voice ("Me")** | You accepted it if there's consent and a privacy-policy line | 10 Oct | ⏳ | Accepted. Built only with consent, a delete button, and never exported |

### 6. Notes / AI features

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 65 | **Brain dump** | Voice brainstorming, possibly agent-like, with an LLM key | 9 Oct | ✅ | "Brain dump" and "Brain dump + questions" requests (v0.4–v0.6) |
| 66 | **Note-taking** | Make notes from a recording | 9 Oct | ✅ | Meeting notes / Lecture notes |
| 67 | **Action items** | Make an action-item list | 9 Oct | ✅ | Rows with Calendar / Remind me / Share |
| 68 | **PM learning coach** | A coach to learn PM | 9 Oct | 🟡 | Built as a "Practice answer" mode with scores. Not a separate product (crowded market) |
| 69 | **Hard-conversation rehearsal; voice roleplay** | Salary, feedback, pitch; score clarity, retry (future) | 9 Oct | ❌ | Not now: ~10–15 s per turn offline; free ChatGPT voice is ~1 s. Cheap version exists: record → Practice score → retry |
| 70 | **Log in with Claude / ChatGPT subscription in the app** | Use subscription tokens instead of API tokens | 9 Oct | ❌ | Anthropic's and Google's terms forbid it. "Sign in with ChatGPT": apply via OpenAI's form (your step) |
| 71 | **Use my Claude subscription for personal use** | Personal build only; remove before launch | 9 Oct | ✅ | Phone → your Mac → your own `claude` tool (v0.5). **Needs Tailscale set up (your step)** |
| 72 | **AI modes plan** | User flow, UI/UX and tech for each AI feature | 9 Oct | ✅ | `docs/AI_MODES.md` |
| 73 | **Notes / action items as their own section** | Separate buttons and capabilities | 10 Oct | ✅ | Make notes / Action items buttons (`ddfb78b`) |
| 74 | **AI features should work, not just share** | Make notes / Action items only opened a share sheet | 10 Oct | 🟡 | Now opens your chosen AI app with the prompt + text. **Answers saved inside indite only with your Mac or an OpenRouter key** |
| 75 | **Send the prompt with the text** | So I don't copy-paste again (as Brain dump did) | 10 Oct | ✅ | Built |
| 76 | **Bring AI answers back into indite** | Save notes/summaries/action items after ChatGPT or Claude | 10 Oct | 🟡 | "Paste reply" card waits for you; Mac and OpenRouter routes save on their own. Auto share-back from other apps is not built |
| 77 | **Optional API key (OpenRouter free models)** | Use it so nothing goes to ChatGPT/Claude/Gemini; answers saved in-app | 10 Oct | 🧪 | Built in build 7 (personal). **Waiting for your OpenRouter key.** ⚠ About half the free models may train on what you send (a warning is shown) |
| 78 | **Choose where AI goes: key / share / both, multi-select** | Tick several AI apps (asked again 10 Oct) | 10 Oct | ✅ | Tick several (`29aa66e`). You overrode the critic's "no Both setting" |
| 79 | **Where is the API key box? What's the Mac address for?** | Question about Settings | 10 Oct | ✅ | Answered. The "Mac" box is your Mac's Tailscale link (personal build) |
| 80 | **What is Tailscale?** | How does it work? | 10 Oct | ✅ | Answered: a private link between your phone and your Mac |

### 7. Reminders & tasks

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 81 | **Timers / reminders** | "I don't see it yet" | 10 Oct | ✅ | First built as a hand-off to the Clock app. **You overrode the "no own reminders" rule**, so indite now has its own (`d5d0188`) |
| 82 | **"Remind me" in the long-press menu, and wherever it fits** | e.g. grocery list at 5 pm after office | 10 Oct | ✅ | Card menu, note menu, task rows; quick picks + any date/time; Done / Snooze 1 h |
| 83 | **Check the note → task → reminder flow** | Test it end to end; improve it | 10 Oct | ✅ | Calendar pre-fills clear dates; "by when" label |
| 84 | **Alarm-like sound + nudge vibration** | Better sound, vibration nudges | 10 Oct | 🧪 | `3d42717`: soft chime + nudges; optional "ring like an alarm until I respond" |
| 85 | **Confirm before cancelling; tidy reminders list** | Separator per reminder; better close button | 10 Oct | 🧪 | `3d42717` |
| 86 | **Icons in the menu?** | Check from a UX view whether to add a reminder icon | 10 Oct | 🧪 | Menu icons added (`3d42717`) |

### 8. Translation & languages

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 87 | **Live two-way translation** | Chinese ↔ Hindi conversation, each sees/hears their own language | 9 Oct | ❌ | Not for now: Google/Samsung already do it free. Start only when 3 real people ask |
| 88 | **Speak English, get Chinese/Tamil/Telugu/Arabic** | Research it; does it make sense? | 10 Oct | 🟡 | Translate button + language picker → your AI app or Google Translate. Own offline translator: no for now. Report: `reports/Offline translation and speech output.md` |
| 89 | **Read the translation aloud** | Speak it out in the chosen language | 10 Oct | ❌ | Parked: 14–15 s per turn on a flagship; little evidence people want it |
| 90 | **Pick the language once; prompt goes with the text** | No asking for the language again | 10 Oct | ✅ | Remembered language (`087931d`) |
| 91 | **More languages (vision)** | Beyond English/Hinglish | 9 Oct | ⏳ | Later: Indian English → Marathi/Bengali → Tamil (2028+) |
| 92 | **Gujarati, Marathi and others into Roman script, plus a market check** | Will people want it? | 10 Oct | 🔬 | Researched (critic-reviewed): possible via speech → native script → Roman; demand unproven. Plan: ask script on tester sign-up + 10 speakers; 1-week laptop test only if demand shows (Gujarati first on a tie). Not now |

### 9. UI/UX & look

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 93 | **Moving progress bar + peek view (web)** | See what's happening | 8 Oct | ✅ | Built |
| 94 | **Web UI/UX improvement plan** | Review the live and static UI; plan for approval | 8 Oct | ✅ | Built |
| 95 | **A proper app UI** | The first one didn't say what to do or how | 9 Oct | ✅ | v0.3 |
| 96 | **Check runtime, UX and UI of the app** | Review the app | 9 Oct | ✅ | Done |
| 97 | **Clean UI with dark mode** | Follow good UI/UX practice | 9 Oct | ✅ | v0.2–0.3 |
| 98 | **Premium, modern look; not "made by AI"** | Research themes, animations (asked 9 Oct, 10 Oct ×3) | 10 Oct | 🟡 | Built: transitions, glow with your voice, fade-in, "All written" moment, day headers. Not yet: custom icons and the rest of the top-10 list (deferred until testers) |
| 99 | **Sleeker home screen** | The tap-to-speak block takes too much space | 10 Oct | ✅ | Floating Record button |
| 100 | **Cards for each recording** | Card layout; good contrast | 10 Oct | ✅ | Cards with border (`6b291cd`) |
| 101 | **Long-press menu on cards** | You said "double long-press"; built as a normal long-press | 10 Oct | ✅ | Copy / Share / Rename / Remind me / Delete |
| 102 | **Copy button on the card** | At least "Copy to clipboard" | 10 Oct | ✅ | Built |
| 103 | **Teach the swipe gestures** | First a tip; then: animate a card right (Copy) and left (Delete) once a day, switchable in Settings → Tutorial; the tip took too much space | 10 Oct | 🧪 | `963545b`: the card peeks right (Copy) then left (Delete), once a day, until you've used both swipes. Replaces the tip card. Switch in Settings → Look & feel → Tutorial |
| 104 | **Today / Yesterday stand out; sticky headers** | Like other apps | 10 Oct | ✅ | `6b291cd` |
| 105 | **Header brand** | Capital "I"; then "lowercase is fine"; pinned, not scrolling; same boldness | 10 Oct | ✅ | `84ea88b` |
| 106 | **Header smaller, less space below** | Same boldness | 10 Oct | 🧪 | `3d42717` |
| 107 | **Better logo; orange dot on the "i"?** | "Just sharing my thought process" | 10 Oct | 🔬 | Not started; your call |
| 108 | **Line under the search bar** | Remove it | 10 Oct | 🧪 | Removed (`3d42717`) |
| 109 | **Empty brown button when editing** | What is it? Also add undo/redo | 10 Oct | 🧪 | Buttons on two rows (fixes it); Undo/Redo (`3d42717`) |
| 110 | **Italic subtitle** | "Speak in Hindi, English, or both" in italics, only if it looks good | 10 Oct | 🧪 | `963545b` (real Figtree italic, not a slanted fake). You decide if it stays |
| 111 | **Value-adds in each user journey** | What extra value can we add in each flow? | 10 Oct | ✅ | Researched (critic-reviewed). Top 8: recovery banner, speed line, "Your data" screen, space left while recording, merge speakers, find & replace, WhatsApp date titles, search jumps to paragraph. Pending build |

### 10. Settings

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 112 | **A Settings page** | Light/dark switch and other needed settings | 9 Oct | ✅ | v0.2 |
| 113 | **Split Settings into groups** | It was scroll, scroll, scroll | 10 Oct | ✅ | 6 groups (`67f6c22`) |
| 114 | **Toggles right on the list** | Where a switch can sit on the first page | 10 Oct | ✅ | e.g. floating mic switch (`6b291cd`) |
| 115 | **Privacy policy under About** | Move it | 10 Oct | ✅ | `1044bf4` |

### 11. Privacy & safety

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 116 | **Don't record into password boxes** | The bubble typed your password into a password field | 10 Oct | ✅ | Bubble and keyboard skip password/PIN/OTP boxes (`1044bf4`, `63a5b7a`) |
| 117 | **Personal-only features removed at launch** | Subscription route and Mac link only for you | 9 Oct | ⏳ | Kept in the `personal` build only; public build has no internet. Remove before launch |
| 118 | **Keep old app versions?** | Something could go wrong | 10 Oct | ✅ | Every installed build is tagged; one last-good APK in `~/.indite/apks/`. **Back up the signing key (your step)** |

### 12. Testing & process

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 119 | **Finish the app, test end to end, think like a PM** | Find bugs in dictation, speakers etc.; compare with rivals; fix; re-check | 9 Oct | ✅ | Automated phone test, review fixes v0.2–v0.6, critic reviews |
| 120 | **Build → test → fix → test again** | Build what we discussed, test it, improve it, test again (asked again 10 Oct) | 9 Oct | ✅ | Ongoing working loop |
| 121 | **Stop making me install and test again and again** | Why V3 when we had V2? | 9 Oct | 🟡 | Tests now run over USB without you. You still hand-check each new build |
| 122 | **Use my connected phone** | USB debugging is on | 9 Oct | ✅ | Done |
| 123 | **Remove old app versions from my phone** | Unless needed | 9 Oct | ✅ | Speed-test app uninstalled |
| 124 | **Shorter phone test** | For the next run | 10 Oct | ✅ | `QUICK=1` mode, ~12 min (`9f44fb5`) |
| 125 | **Make the latest build, push, run the full phone test** | — | 10 Oct | ✅ | Done |
| 126 | **What is the 20-minute hand check?** | What do I need to do? (asked again: "What do I need to test?") | 10 Oct | ✅ | Explained. Your check of the newest build is still ⏳ |
| 127 | **What are we measuring, and why?** | Plus: "couldn't you find this on the web?" | 9 Oct | ✅ | Answered |
| 128 | **Why was the full phone test blocked?** | Security or something else? | 10 Oct | ✅ | Answered |
| 129 | **More features first, or test first?** | — | 10 Oct | ✅ | Answered |
| 130 | **Use my recordings** | "I'll provide certain recordings" | 9 Oct | ❓ | Not received yet. Needed: 3 real conversations with interruptions (#63) |
| 131 | **Keep working while I use the phone** | Build now; install and test when the phone is free | 10 Oct | ✅ | Done |
| 132 | **Think like a PM: would people buy it outright?** | Quality at UI, feature and speed level | 9 Oct | 🟡 | Tester build + 10–20 testers + interviews planned (ROADMAP) |

### 13. Docs & handoff

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 133 | **Roadmap: done, planned, phase, why** | Asked 8 Oct, 9 Oct ×3, 10 Oct ×4 | 8 Oct | ✅ | `ROADMAP.md` + roadmap page |
| 134 | **Compare with competitors; add the relevant features** | — | 8 Oct | ✅ | ROADMAP "Competitors noted" |
| 135 | **Add LLM / budget notes to the plan page** | "Yes add it to the plan page" | 8 Oct | ✅ | Done |
| 136 | **What's pending from the old roadmap?** | — | 9 Oct | ✅ | Answered |
| 137 | **All features: what survived, what didn't, and why; new products** | In separate tables | 9 Oct | ✅ | PLAN §3–4 |
| 138 | **Save everything we discussed for V2 to a file** | — | 9 Oct | ✅ | `PLAN.md` |
| 139 | **Anything missed in V2? Is it final?** | — | 9 Oct | ✅ | Answered |
| 140 | **Re-share PLAN.md** | — | 9 Oct | ✅ | Done |
| 141 | **BHAG plan** | With a free hand, how would you design this app? | 9 Oct | ✅ | PLAN goal + phases |
| 142 | **Bigger vision** | More features, languages, or something different; in an artifact | 9 Oct | ✅ | Vision page |
| 143 | **Merge the two roadmap files** | — | 10 Oct | ✅ | `790924c` |
| 144 | **Note my recent improvement asks in the roadmap; show what's pending** | — | 10 Oct | ✅ | ROADMAP "Founder's requests" + "Also open" |
| 145 | **Go through the whole chat: covered, not included, why, what else, pending** | — | 10 Oct | ✅ | `717904a` (9 items found) |
| 146 | **Organised, easy-to-read answers** | Group and sort long replies | 10 Oct | ✅ | Rules in `CLAUDE.md` |
| 147 | **Handoff doc for Codex / Claude Code** | Keep it updated, with logs | 10 Oct | ✅ | `docs/HANDOFF.md`, `docs/WORKLOG.md`, `AGENTS.md` (`a5f02fc`) |
| 148 | **Pending features list** | Bold feature name + one line each | 10 Oct | ✅ | Answered in chat |
| 149 | **What did you finalise last time?** | — | 10 Oct | ✅ | Answered |
| 150 | **This document** | Track every prompt, what's done, what's not, why | 10 Oct | ✅ | This file |
| 151 | **Save to GitHub; push** | github.com/vaibhavk93/Indite (asked again 9 Oct ×2) | 9 Oct | 🟡 | Pushed up to `738a118`. **Later commits are only on the Mac** until you say push |
| 152 | **Commit the Android code + plan** | — | 9 Oct | ✅ | Done |

### 14. Platforms (iOS, web, Windows)

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 153 | **Frontend for the system** | "Did we create the frontend?" | 8 Oct | ✅ | Web app |
| 154 | **Windows support** | After the speaker tests | 8 Oct | ⏳ | Planned; needs a real Windows PC to measure speed |
| 155 | **Android app** | Create an Android app for indite | 9 Oct | ✅ | `android/` |
| 156 | **Works offline, no Mac** | — | 9 Oct | ✅ | Everything runs on the phone |
| 157 | **APK I can install directly** | Where is it? How do I install it? | 9 Oct | ✅ | Explained; installed over USB |
| 158 | **iPhone app?** | Can we make one? | 10 Oct | ❌ | Not now. Starts when 5+ testers ask. iOS blocks the bubble, mic in keyboards and auto-paste |
| 159 | **iOS cost to build and launch** | Mandatory charges | 10 Oct | ✅ | Answered: $99/year developer account to give it to others |
| 160 | **Why reinstall every 7 days with free Xcode?** | — | 10 Oct | ✅ | Answered: free Apple ID installs expire after 7 days |
| 161 | **Mobile, web, desktop or Mac app to start** | Use today's device abilities | 9 Oct | 🟡 | Android + web built. Native Mac app: not assessed |
| 162 | **Google login** | Sign in, like Claude's browser login from the terminal | 8 Oct | ⏳ | Later, with hosting and payments |

### 15. Business & market

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 163 | **Free app with in-app charges** | Like others do | 10 Oct | ✅ | Answered. Plan: Pro one-time unlock (₹299 vs ₹999 test) in phase 2; price unproven |
| 164 | **Products from this** | What else could we make? | 9 Oct | ✅ | PLAN §4 (none proven) |
| 165 | **Start small, grow if there's a market** | Explore further only if the market is good | 9 Oct | ✅ | Gates in PLAN §6 |
| 166 | **How long will the app take?** | Time to build | 9 Oct | ✅ | Answered |
| 167 | **Market check: Indian languages in Roman script** | Will people want it? | 10 Oct | 🔬 | Done with #92: Roman typing is common for Hindi, unproven for Gujarati/Marathi and for voice; Gboard does native script free |
| 168 | **Check Sarvam Edge / Gboard** | Do rivals already do offline Roman Hinglish? (from the vision review) | 9 Oct | 🔬 | Research, before testers |
| 169 | **Use WhatsApp?** | "Where did WhatsApp come from?" The key is dictation + speakers | 9 Oct | ✅ | Kept as a share-in source; dictation + speakers are the focus |
| 170 | **Start building the app** | Don't wait for every speed test | 9 Oct | ✅ | Built |
| 171 | **Add more use cases** | Research more uses of the app (translation was one) | 10 Oct | 🟡 | Translation researched (#88); other uses fold into #111 |
| 172 | **Repo licence** | The public repo has no LICENSE (raised in a review) | 10 Oct | 🔬 | Your decision, before testers |

---


### Added 10 Oct (evening)

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 173 | **ChatGPT login inside the app, then use its models** | Clarified: sign in to ChatGPT in indite and use the models for AI features | 10 Oct | 🔬 | **In-app login: not allowed yet.** OpenAI's "Sign in with ChatGPT" for third-party apps is an application-only preview without mobile support (as researched 10 Oct); reusing Codex's login inside indite would impersonate OpenAI's client (terms risk, account ban). **Built instead:** the Mac route can answer with ChatGPT via your own Codex CLI (personal build), and your own API key (OpenRouter). **Next:** founder applies to OpenAI's programme; re-check status before applying |
| 174 | **Stats dashboard** | How many words transcribed, recordings, all of that | 10 Oct | 🧪 | Settings → Your stats: words, minutes, recordings / dictations / imports, this week's words (7-day bars), typical speed, AI answers, labelled notes, reminders. Counted on the phone only |
| 175 | **Subtitle "Speak in Hindi, English or both"** | Mentioned again with the italic request | 10 Oct | ❓ | Italic built (real Figtree italic). If you meant different wording (e.g. a comma instead of a full stop), say so |

### Added 10 Oct (night) — this session

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 178 | **Fix invented words in silence first** | The 15-min test wrote "ji sir swiggy campaign ka ctr 3 percent aaya hai" out of fan noise | 10 Oct | 🔬 | Two fixes tried and measured on the Mac, both dead ends: the model reports **no_speech_prob 0.000 even for pure silence**, and it is *more* confident on invented text (95.5%) than on real speech (94.9%). Filtering after the model cannot work. Next: tighten the speech detector (Silero) so noise never reaches the model |
| 179 | **Keyboard always opens in "copy to clipboard" mode** | It shouldn't | 10 Oct | 🧪 | Root cause found: the reset check asked whether the coroutine running it had finished, so it never reset. Fixed; the keyboard also resets on every open, and "done" now shows a tick, not the copy icon (build 11) |
| 180 | **Keyboard icons don't look right** | Make them optimal | 10 Oct | 🧪 | Backspace and Enter are real icons now (outlined, matching weight); "ABC" used a faked bold — the real Figtree weight 700 is used; less empty space round the mic (build 11) |
| 181 | **Change the Enter button** | The arrow looks bad | 10 Oct | 🧪 | The key now says what it will do in that box: send / search / go / next / done / enter (build 11) |
| 182 | **Which OpenRouter models should I use?** | Free or paid | 10 Oct | ✅ | Checked the live list: 19 free models today. Pick `google/gemma-4-31b-it:free` (Google AI Studio: does not train); also test `dots-studio/dots-3-note-preview:free`. Avoid NVIDIA / Thinking Machines / Liquid free models — those providers may train on your notes. Paid fallback if free fails: claude-haiku-5.5 or gemini-2.5-flash-lite, about ₹0.03 per note |
| 183 | **Should I buy the $10 OpenRouter credit?** | It raises free-model limits | 10 Oct | ✅ | Not yet. It is a threshold, not an offer: buying ≥$10 once raises free models from 50 to 1000 requests a day, permanently. 50/day is more than your use, and the model test needs 15 requests. Buy it when you hit the limit or decide to use Haiku |
| 184 | **Turn training off in OpenRouter** | Privacy | 10 Oct | ⏳ | **Your 30 seconds:** openrouter.ai/settings/privacy, two switches (free and paid). Only 4 of ~95 providers train: DeepSeek, NVIDIA, Liquid, Thinking Machines. Turning it off costs you the NVIDIA and Inkling free models, nothing else |
| 185 | **Reminders only send a notification, not a proper alert** | Should ring and buzz like an alarm | 10 Oct | 🧪 | "Ring like an alarm until I respond" is now **on by default** (alarm volume, works on silent, repeats until seen). It was built in build 10 but defaulted to off, so you only got the soft chime |
| 186 | **Scrolling copies a note instead of scrolling** | Accidental swipe-right | 10 Oct | 🧪 | The copy swipe now needs an 80% pull across the card; delete stays at 50% (it asks first and can be undone) |
| 187 | **Tone conversion: formal / informal before sending** | Rewrite a dictation to send to someone | 10 Oct | 🔬 | Critic-reviewed. "Clean it up" already does a mild version, and the Translate language picker is the same machinery, so the small version is ~0.5 h. **Test first (1 h):** 10 real messages at formal/casual — would you send them unedited? The inline version (tone inside dictation) is ruled out: no AI on the phone, and it would add seconds to a 9-17 s wait |
| 188 | **The app should learn the gaps and improve over time** | Get better with use | 10 Oct | 🟡 | Critic-reviewed. **Mostly built already:** correct the same word twice and indite offers "Always fix PTM → Paytm?" (`Settings.learn`). Impossible: training the model on your voice (no trainer, no RAM). Refused: sending corrections to a server (breaks privacy, cost, DPDP and public-repo rules). The real gap is a personal vocabulary of names fed to the engine — **gated** on a Mac test, because feeding names to a model that invents in silence could make it invent your contacts' names |
| 189 | **Keep adding my prompts to the requests file** | Summarised, as before | 10 Oct | ✅ | This block. Done each session |
| 190 | **Run the 1-hour free-model test** | Does it need my phone? | 10 Oct | 🔬 | No phone needed — Mac only. Running now with your key on 3 free models × 3 prompts × 5 notes. Key stored at `~/.indite/openrouter.key` (outside the repo, 600) |


## Open questions for the founder

**⚠ Remember:** these block work. Nothing below moves until you answer or act.

### Your actions

1. **OpenRouter key.** Needed to test in-app AI answers (#77). Built and waiting.
2. **Tailscale setup.** Needed for "Claude on my Mac" answers from the phone (#71).
3. **Back up the signing key.** `~/.indite/indite-testers.keystore` (password `android`). Put it in a password manager
   or a private Drive folder. **If it's lost, updates can't install over the old app.**
4. **OK to delete old APKs?** `phonetest/` and `APK/` (~2.4 GB; the Mac is nearly full). `phonetest/pieces` may hold
   audio: check it first.
5. **Record 3 real conversations** with people talking over each other. This decides whether overlap handling is built
   (#63). It also covers the recordings you offered on 9 Oct (#130).
6. **₹15k phone.** When can you borrow one? It's the biggest unknown (#25).
7. **Speaker listen-check.** Play 1:34–1:47, 7:00–7:14 and 13:07–13:28 of the 15-min interview (#61).
8. **Hand check of the newest build.** Covers all 🧪 items: the reminder sound and confirm step, header, search bar,
   Undo/Redo, the keyboard redesign, the swipe hint, the bubble drag, and the italic subtitle.
9. **Push to GitHub?** Commits after `738a118` are only on the Mac (#151).
10. **"Sign in with ChatGPT"** interest form at OpenAI, if you want it later (#70).

### Decisions

| Question | Options |
|---|---|
| Repo licence (public repo) | MIT / Apache / none (#172) |
| Accessibility add-on in the public build | Needed for bubble-only-with-keyboard and auto-paste; Play review risk (#33) |
| Retry button on cards | Add it, or drop it (#56) |
| Logo: orange dot on the "i"? | Try it, or keep it as is (#107) |
| Italic subtitle | Keep if it looks good on your phone (#110) |

### Unclear messages

- **"…prompt and transcript. Why check all these features of under Ask my AI to do it."** (10 Oct). This looks
  cut off. Did you mean "why are these features under *Ask my AI* instead of being their own buttons"? Or "send the
  prompt + transcript so the AI does it"? Please clarify.
- **"Double long-press"** (10 Oct). It was built as a normal long-press. Is that what you wanted?

---

## How this doc is kept current

- **The coding agent updates it at the end of every session**, together with `ROADMAP.md` and `docs/WORKLOG.md`
  (and `docs/HANDOFF.md` §5).
- For each new request: add a row under the right theme with the date. If it repeats an old one, update that row and
  add "asked again on <date>".
- When something is built: set ✅ with the commit or build. If it isn't tested on the phone yet, use 🧪 until you've
  checked it.
- When something is dropped: set ❌ with the reason. If you overrule a decision, say so in the row.
- Update the Summary counts and "Last updated" each time.

| 176 | **Same audio, different text: fix without losing speed** | RCA + fix | 10 Oct | ✅ | Root cause: flash attention read leftover audio from the previous piece. Fix: audio window always a multiple of 256 (`a69dab5`). Phone A/B: same text every run; live wait 9.1-14.1 s vs 79-87 s with the old rounding. Heat adds seconds |
| 177 | **Keep the handoff updated as we go** | So work can continue from another account if tokens run out | 10 Oct | ✅ | docs/HANDOFF.md section 5 updated after every build/test; WORKLOG + this file too |
