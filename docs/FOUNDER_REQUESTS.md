# Founder requests: everything you asked for, and where it stands

**Last updated:** 2026-10-10 (reminder sound, translation and "formal version" fixes)

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
| ✅ Built / answered | 121 |
| 🧪 Built, not tested on phone | 15 |
| 🟡 Partly | 17 |
| ⏳ Pending | 10 |
| 🔬 Researching / needs decision | 9 |
| ❌ Not doing | 6 |
| ❓ Unclear | 3 |
| **Total** | **181** |

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
| 60 | **Find the speaker count automatically** | Don't make me say 2, 3 or 4 people; "guess and then confirm" | 10 Oct | ✅ | indite guesses, you confirm (`cf0337f`). It still needed a tap to start, which you raised again — see **#181** |
| 61 | **Can I trust "Find who spoke"?** | It seems to work, but I can't check the quality | 10 Oct | ⏳ | You listen at 1:34–1:47, 7:00–7:14, 13:07–13:28. "Show only [name]" filter is in the next build |
| 62 | **Focus on one speaker among many** | If 4–5 voices come in at once, can we tell them apart? Feasibility test | 10 Oct | 🔬 | Folded into #63. Many voices at once is not handled today |
| 63 | **Keep the 2–3 s when people talk over each other** | Track them, or convince me it's not worth it | 10 Oct | ⏳ | Deferred, with a measurement plan: record 3 real conversations; build only if > ~3% of words are lost |
| 181 | **Do the first speaker pass without being asked** | "Why does speaker diarization not work automatically? It is possible to ask and update at a later stage, but the initial speaker diarization should be done by you" | 10 Oct | 🧪 | **Nothing decided that it had to be manual** — it was built as a button and the trigger was never removed; #60 took away the *count* question but left the tap. **Now:** as soon as the text is ready, indite labels who spoke by itself, for any recording over a minute with 2+ paragraphs. It runs after all transcription is done, and is skipped when the phone is hot or the battery is low. The count is still a guess, so the note screen asks "indite heard N people. Is that right?" — your "ask and update later". One voice = no labels at all (a solo dictation no longer gets "Speaker 1" on every paragraph, which an explicit "1" used to do too), with a one-line "Two people spoke?" underneath — **that rule is what makes a wrong guess undoable in one tap.** ⚠ **This is ahead of your own gate:** the guess has never been scored on real audio (the phone test only ever scores a *given* count, so 96.7% / 93.3% are given-count numbers) and #61 is still waiting on your listen-check, yet the guess is now the default for every long note. The likely failure is **splitting one person into two** (background TV; music, which the speech detector hears as speech). Keep it in your personal build; it must not reach testers until measured — `--es test_label "<name>" --ei k 0` scores it today with no new code (~20 min) |
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
| 180 | **Make a formal statement out of what I dictated** | "Making formal statement out of the context I have shared" | 10 Oct | 🧪 | New **Formal version** request under Ask my AI: formal English, every fact / name / number / date kept, nothing added, "(unclear)" where it can't tell. It needs an AI route, so see #179 |

### 7. Reminders & tasks

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 81 | **Timers / reminders** | "I don't see it yet" | 10 Oct | ✅ | First built as a hand-off to the Clock app. **You overrode the "no own reminders" rule**, so indite now has its own (`d5d0188`) |
| 82 | **"Remind me" in the long-press menu, and wherever it fits** | e.g. grocery list at 5 pm after office | 10 Oct | ✅ | Card menu, note menu, task rows; quick picks + any date/time; Done / Snooze 1 h |
| 83 | **Check the note → task → reminder flow** | Test it end to end; improve it | 10 Oct | ✅ | Calendar pre-fills clear dates; "by when" label |
| 84 | **Alarm-like sound + nudge vibration** | Better sound, vibration nudges | 10 Oct | 🧪 | `3d42717`: soft chime + nudges; "ring like an alarm until I respond" was built as a switch that defaulted to **off**, which is why you heard nothing — see **#178**. Stays 🧪 until you confirm on the phone |
| 85 | **Confirm before cancelling; tidy reminders list** | Separator per reminder; better close button | 10 Oct | 🧪 | `3d42717` |
| 86 | **Icons in the menu?** | Check from a UX view whether to add a reminder icon | 10 Oct | 🧪 | Menu icons added (`3d42717`) |
| 178 | **The reminder makes no sound** | "Alarm is not working properly. It is not giving me sound." (#84 again, after the build) | 10 Oct | 🧪 | **Most likely cause: the "Ring like an alarm" switch was off by default**, so every reminder was a soft chime on the notification volume — which silent mode, Do Not Disturb and a low notification volume all mute. You asked for an alarm-like sound in #84 and it shipped as an opt-in switch, off, inside Settings. **Now on by default**, on the alarm volume, repeating until you see it. **Second possible cause:** indite only asked for notification permission when you recorded or imported, never when you set a reminder; the Remind me dialog asks now, and a reminder the phone refuses to show is no longer quietly thrown away. **Third:** this phone force-stopping indite, which deletes its alarms — Settings → Reminders now says so and opens the battery setting. Also new: **Test the reminder sound**, a line naming whichever phone setting is blocking it, and "Last reminder: …". A missed reminder also stopped re-appearing on every app open. ⚠ **One question only you can answer:** when it was due, did it appear on screen with no sound, or not appear at all? |

### 8. Translation & languages

| # | Request | What you asked, with context | Date | Status | Where it stands / why not |
|---|---|---|---|---|---|
| 87 | **Live two-way translation** | Chinese ↔ Hindi conversation, each sees/hears their own language | 9 Oct | ❌ | Not for now: Google/Samsung already do it free. Start only when 3 real people ask |
| 88 | **Speak English, get Chinese/Tamil/Telugu/Arabic** | Research it; does it make sense? | 10 Oct | 🟡 | Translate button + language picker → your AI app or Google Translate. Own offline translator: no for now. Report: `reports/Offline translation and speech output.md` |
| 89 | **Read the translation aloud** | Speak it out in the chosen language | 10 Oct | ❌ | Parked: 14–15 s per turn on a flagship; little evidence people want it |
| 90 | **Pick the language once; prompt goes with the text** | No asking for the language again | 10 Oct | ✅ | Remembered language (`087931d`) |
| 91 | **More languages (vision)** | Beyond English/Hinglish | 9 Oct | ⏳ | Later: Indian English → Marathi/Bengali → Tamil (2028+) |
| 179 | **Translation isn't working** | "The translations are not working" | 10 Oct | 🟡 | **Two real bugs fixed:** Translate in the *Ask my AI* list never asked which language, so it quietly translated into English; and the one route that works with no key and no internet (the Google Translate app) was the last line of a scrolling dialog — it is now the first button. ⚠ **indite has no translator of its own.** For a translation written back into the note you need your Mac link or an OpenRouter key, and neither is set up yet. Settings → AI now says in one line what will happen when you tap an AI request. **Fastest unblock: an OpenRouter key** (2-minute signup) — it makes Translate, Formal version and every other request answer inside indite straight away; Tailscale for the Mac route is the harder, second ask |
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
| 190 | **Run the 1-hour free-model test** | Does it need my phone? | 10 Oct | ✅ | Mac only, no phone. 45 requests (3 free models × 3 prompts × 5 notes) on real transcript text. **Winner: `apodex/apodex-1.1-mini:free`** — 15/15 worked, median 25 s, kept Roman Hinglish everywhere, followed the `task | who | by when` format, no Devanagari, no invented tasks. `dots-3-note`: 15/15 but median 46 s (up to 80 s) and it **translated action items into English**. `gemma-4-31b`: 13 of 15 failed — Google AI Studio rate-limits that free endpoint upstream. Outputs saved locally. Key stored at `~/.indite/openrouter.key` (outside the repo, 600); **rotate it, it was pasted in chat** |


### Added 10 Oct (late night) — build 12

| # | Request | What you asked | Date | Status | Where it stands |
|---|---|---|---|---|---|
| 191 | **Key added but AI features do nothing** | OpenRouter key saved, nothing answers | 10 Oct | 🧪 | **Root cause:** a saved key only worked if "Answer inside indite" was *also* ticked under Settings → AI → Where AI requests go. It never was. Now a working key is always a route (build 12) |
| 192 | **Alarm still silent after turning the switch on; sound should be the default** | — | 10 Oct | 🧪 | The default-on change was built *after* build 11 was installed, so your phone never had it. Build 12 has it, plus the cloud session's "Test the sound" button, a line naming the phone setting that is muting it, and "Last reminder: …" |
| 193 | **Formal / email / informal / tones conversion** | Convert a recording to a sendable message | 10 Oct | 🧪 | **Rewrite to send** under Ask my AI, with a style picker: formal English, polite request, WhatsApp Hinglish, casual Hinglish, email with subject, firm, apology, thank-you, short-and-crisp, or type your own. Replaces the narrower "Formal version". Needs an AI route (key or Mac) |
| 194 | **Speaker labels by default, correct them later** | — | 🧪 | Automatic labelling came from the cloud branch (runs when the text is ready, skipped when hot or low battery). Correction already exists: the note asks "indite heard N people. Is that right?", and ⋮ → Who spoke? re-runs with a count you choose or a fresh guess |
| 195 | **Choose audio / text / both when deleting** | — | 10 Oct | 🧪 | Delete now asks: audio only (keeps the text), text only (keeps the recording), or the whole note. It shows how many MB the note uses |
| 196 | **Accessibility: can we pass a test so banks don't flag indite?** | — | 10 Oct | ✅ | **No such test exists** (researched + critic-reviewed). Banks' security SDKs flag *any* enabled third-party accessibility service, not specific flags; allowlists are per-bank and need a Play-store install. Setting `isAccessibilityTool="true"` would be a Play policy strike — never do it. The public build already ships no service; the keyboard types with `commitText()` (no accessibility, no clipboard). Decision: keep the service personal-only, switch it off before banking apps |
| 197 | **Several keys + rotation to raise the 50/day limit** | 50 → 150 or 200 | 10 Oct | ❌ | OpenRouter's own docs: *"Making additional accounts or API keys will not affect your rate limits, as we govern capacity globally."* Limits are per account, not per key, and multi-accounting risks a ban. The only supported raise is ≥10 credits once: 50 → 1000 a day |
| 198 | **Key disabled** | I disabled the key I pasted | 10 Oct | ✅ | Local copy deleted from `~/.indite/openrouter.key` |


### Added 13–14 Oct — builds 16–29

| # | Request | What you asked | Date | Status | Where it stands |
|---|---|---|---|---|---|
| 199 | **Dictation is still slow** | the wait after a pause | 13 Oct | ✅ | **9.6 s median, 17.1% words wrong** (build 29). The audio window now follows the piece instead of being a flat 15 s. Two wrong turns on the way, both caught by the phone test |
| 200 | **Logo: smaller, orange dots on the i's** | — | 13 Oct | ✅ | Smaller wordmark; the two i's are orange. Hand-drawn dots were tried and dropped — a circle placed from glyph metrics drifts when the font scales. A dot-only logo needs a vector asset, not code |
| 201 | **"Writing part 1 of 1" is half the screen** | — | 14 Oct | ✅ | The bar was literally coded to half width and looped instead of filling. Now full width, real progress, and a one-piece note says "Writing it now…" |
| 202 | **UI breaks after using Ask AI a few times** | — | 13 Oct | 🧪 | Cause found: every AI answer added a chip to a single-line row, which overflowed the card. Capped at two chips plus a count; the time truncates instead of being pushed off |
| 203 | **Turn anger or abuse into a formal message** | — | 13 Oct | 🟡 | Critic-reviewed. Built as the style **"say this calmly — the insults taken out"**, with a prompt carve-out that removes insults and keeps the request, and says "(nothing to send — this is a vent)" when nothing remains. Refused: any "sharper / firmer" sibling style. **Gate: 10 real angry messages, 7 of 10 sent unedited** |
| 204 | **A Mac and Windows app like Wispr Flow** | — | 14 Oct | 🔬 | Mac engine, web UI and benchmarks already exist (910 lines of Python). Missing on both: global hotkey, typing into the focused app, tray presence, installer, signing. **Blocker before any of it: desktop latency has never been measured.** Windows deferred by your decision; Mac first |
| 205 | **Is the model licence OK?** | can we ship and sell this | 14 Oct | ✅ | **Apache 2.0 — commercial use allowed, no permission needed.** Verified on the model card and Oriserve's own announcement. whisper.cpp is MIT. Keep the licence text and notices (`res/raw/licenses.txt`). ⚠ Your own repo still has no LICENSE |
| 206 | **Can I test a Mac app without paying $99/yr?** | — | 14 Oct | ✅ | **Yes.** Build and run on your own Mac for free; macOS asks once ("Open Anyway"). The $99 only matters when someone else installs it — without notarization they see "developer cannot be verified" |
| 207 | **Keep the project in the cloud and locally** | — | 14 Oct | 🟡 | Code: both (GitHub, pushed). Not in the cloud by design: 587 MB models, 2 GB tools, test audio, reports. **⚠ The signing key is still in one place and is the only irreplaceable file** |
| 208 | **Can indite keep working when I switch apps?** | — | 14 Oct | ✅ | Yes — transcription runs as a foreground service with its own notification. Caveat: OnePlus freezes background apps unless battery optimisation is off for indite |


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
| 178 | **Mac app: something wrong, check it** | It stopped responding | 15 Oct | ✅ | A Bluetooth headset that was off crashed the hotkey. Fixed (`9a374e8`), tested by you with the headset off |
| 179 | **Keep Android and Mac apps separate** | Improve both without one affecting the other | 15 Oct | ✅ | Mac has its own model and spelling list; neither reads the other's folder |
| 180 | **More Wispr Flow features on the Mac** | — | 15 Oct | 🟡 | **Word fixes and Esc cancel built, you confirmed both. 60 s hold was 75% wrong; fixed to 19%.** Critic-reviewed: test 60 s hold; later snippets, hands-free; drop undo, voice enter, command mode. **Your input:** what do you actually miss from Wispr? |
| 181 | **Smaller pill with a glass look** | Bulky, hides the desktop | 15 Oct | 🧪 | 116 x 30 (was 168 x 44), macOS 26 Liquid Glass. Your look pending |
| 182 | **Better Mac UI/UX, white, designer details** | — | 15 Oct | 🧪 | Redesigned and reviewed by a design critic; fixes applied (contrast, no streak, native clear dialog). Your look pending |
| 183 | **All Android capabilities on the Mac, plus Wispr's flows** | Improve the Mac app; keep docs | 15 Oct | 🟡 | Critic: the web app already covers files/editing/export; porting all of Android is the wrong goal. Built: password guard, fix a word from history, Transcribe a file, Login Items help. **Your call:** hands-free, AI actions. Full table: `docs/MAC_PLAN.md` |
| 184 | **Mac: the full list (R1–R24)** — translucent pill + border + writing animation, drag, full screen, install for a colleague, commercial use, files in-app, AI, hands-free, to-do section, assistant, improve-with-original, speakers, meeting recording, backup, stars, setup screen, sounds, mic picker, paste last | 15 Oct | 🟡 | Tracked line by line in `docs/MAC_PLAN.md` §3. Done this session: R1–R4, R7–R10 |
| 185 | **Build everything buildable; fix full screen; hands-free key + taps; more transparent pill; find error patterns; show/hide the written words; keep saving progress** | 15 Oct | 🟡 | Built and committed (R11–R19, R28–R31). Waiting on you: real-world checks (meeting audio permission, full screen, drag), and what "show/hide" meant (R31). Shareable build (R20) is next |
| 186 | **A build to share with the boss** | Ask before including any login | 15 Oct | ✅ | Asked: API key option + his own Claude login, unsigned zip. `dist-share/indite-mac.zip` (624 MB), tested in a bare environment |
| 187 | **AI on/off and login/API key in Settings** | — | 15 Oct | ✅ | Settings → AI: on/off, Claude login status + Sign in, or an Anthropic/OpenAI/OpenRouter key in the Keychain |
| 188 | **UX/UI is bad, especially Settings** | Fix it | 15 Oct | 🟡 | Restructured after a review; real-window snapshot found a blank window (fixed), too-wide full screen (fixed), backwards slider (fixed). **Your input:** what still feels bad |
| 189 | **Pill hides over Terminal; hands-free 3 taps** | — | 15 Oct | 🧪 | Cause: Dock-app panels cannot enter another app's full screen; fixed. 3 taps likely worked with the pill hidden |
| 190 | **Final roadmap: done / pending / future tables** | — | 15 Oct | ✅ | `docs/MAC_PLAN.md` §0 |
| 191 | **Add or update handoff docs** | — | 15 Oct | ✅ | HANDOFF §5 "The Mac app now" + lessons; README; WORKLOG |
| 192 | **Analyse 15 Wispr Flow screenshots: which features we lack, which are easy, which are not; then a detailed plan and roadmap** | 15 Oct | ✅ | Checked against the code and critic-reviewed. **5 of 14 were already built** (snippets = word fixes, Dictionary page, wpm / time saved / by app / by hour / streak). Build now: 3 small Dictionary items (~2 h). Gated: Dictionary → whisper prompt (bench, 0 false insertions); no-AI filler strip (30 real dictations). Dropped 11, including AI clean-up on every dictation (4–7× slower, spends your own quota, replaces the raw text) and the Dock-icon toggle (would break the pill over full-screen apps). Full reasoning: `docs/MAC_PLAN.md` §6. **Beats all of it:** Screen Recording still not granted (meeting recording + demo video are dead), the 53 real dictations are unscored, nothing is signed |
| 209 | **Check Accessibility end to end, then tell me to add it** | Removed and re-added many times | 15 Oct | ✅ | Key access works; three dictations typed. Real cause: indite crashed as soon as keys reached it (fixed); its log was checking the wrong permission (fixed) |
| 210 | **Make sure such issues don't occur again** | — | 15 Oct | ✅ | Crash stacks now land in the log; the pynput version is pinned; the log checks both key permissions; rule added to HANDOFF |
| 211 | **I can't see the app window** | — | 15 Oct | 🟡 | A frozen old copy takes your Dock clicks. Opened the live window for you; **restart the Mac** to clear it for good |
| 213 | **Still see "indite can't hear the hotkey, open Settings"** | — | 15 Oct | ✅ | False alarm: the warning checked Input Monitoring. It now checks Accessibility, which the hotkey really uses |
| 212 | **Don't touch the GitHub history** | — | 15 Oct | ✅ | Not rewritten; nothing pushed |
| 214 | **Ask AI still has UX/UI issues** | Fix before the Mac restart and the demo | 15 Oct | 🧪 | Found with real screenshots + critic: the panel redrew itself every few seconds (scroll jumped, the Ask box lost the cursor while dictating); answers showed raw # and **; long answers buried the Ask box; errors hid behind the panel; dictating into the Ask box also saved a new note. All fixed. Your look pending |
| 215 | **Settings → AI: say clearly what an AI login or key unlocks** | — | 15 Oct | 🧪 | Two lists: with AI (the Ask AI panel actions) vs always offline (dictation, meetings, who spoke, files, dictionary, to do, insights, backup); login and key unlock the same features |
| 216 | **Ask AI: shift the list instead of covering it; show the note as selected** | Will that be good UX? | 15 Oct | 🧪 | Critic: side by side only when the window is wide (≥1180 px), else the panel stays on top but no longer dims the list; the note is highlighted. Built |
| 217 | **Ask AI close button too small** | — | 15 Oct | 🧪 | 32 px round button; Esc also closes |
| 218 | **Ask AI sections look messy (double separators)** | Separate Make it better / Turn it into / Send it | 15 Oct | 🧪 | One divider, three plain sections; critic renamed "Send it" to "Rewrite or translate" (nothing is sent) |
| 219 | **Our own popup for Rewrite as / Translate to** | — | 15 Oct | 🧪 | indite's menu; picking runs it at once |
| 220 | **Does "Answers come from Claude (email)" change per user?** | — | 15 Oct | ✅ | Yes: it is whoever is signed in to Claude on that Mac. Kept |
| 221 | **The box shows only one line of what I said** | — | 15 Oct | 🧪 | The Ask box was one line; now grows to ~6 lines (Enter asks, Shift+Enter new line). The after-dictation card already wraps (checked) |
| 222 | **Long question: title and time spacing** | — | 15 Oct | 🧪 | Title wraps to 2 lines, stays clear of the time (measured); the full question is kept (two alike no longer overwrite) |
| 223 | **Test the whole app yourself before the demo** | Front end, back end, runtime | 15 Oct | ✅ | All automated checks pass; every page opens with no errors; live AI and file tests pass. Not testable by me: your voice into the Ask box |
| 224 | **Ask AI UX is still bad; maybe worse** | Answers vs options, distinct sections, proper Rewrite/Translate, loading, background, not "AI-vibe-coded" | 15 Oct | 🧪 | Rebuilt after a critic: answers as plain documents on top; options on a sunken surface in grouped lists; Rewrite (Tone / For / Purpose) and Translate as one-click chips; loading bar + "you can close this"; ready/failed message; orange glows and tints removed app-wide; own icon |
| 225 | **Summary not capped at 5 bullets** | — | 15 Oct | ✅ | Scales with the note (1-2 for short, up to ~12 for a long meeting). Android's copy of the prompt not changed yet |
| 226 | **Does Rewrite cover the usual cases?** | — | 15 Oct | ✅ | It didn't: added Friendly, Slack/Teams, LinkedIn post, Follow-up, Request (13 total); 3 more languages (13) |
| 227 | **AI review of a recording: find transcription mistakes, fix them, learn; insights; regional personalisation** | Add to the roadmap | 15 Oct | 🔬 | Planned (`docs/ROADMAP_DETAIL.md` C1-C7, ROADMAP "Now" 7): offline near-miss check first, then AI review with guards |
| 228 | **Roadmap in simple tables + Wispr Flow comparison** | Use the earlier Wispr screenshot analysis + web research | 15 Oct | ✅ | `docs/ROADMAP_DETAIL.md` sections A and B (sources dated) |
| 229 | **AI usage in Insights** | — | 15 Oct | 🧪 | Small card: answers, notes, top 3 actions, "See the notes with AI →" (new "With AI" filter). Critic trimmed weekly counts (no dates on improved wording) |
| 230 | **Make a structured prompt from what I said** | Best prompt-engineering practice | 15 Oct | 🧪 | Ask AI → "For another AI" → Make it a prompt (Role, Context, Task, Constraints, Output format; English; [fill in] for gaps). Critic dropped a separate "shorten" (Summary covers it). Android copy not yet |
| 231 | **Golden border on the AI chip, click to see what AI made** | — | 15 Oct | 🧪 | Gold edge + icon, no fill or glow (critic preferred icon only; your call kept). "AI is writing…" stays neutral |
| 232 | **Ask AI must not stay open on other pages** | — | 15 Oct | 🧪 | Closes when you switch pages |
| 233 | **Pill disappears after minimise/maximise** | — | 15 Oct | 🧪 | Cause: the pill trusted its own "showing" flag after macOS hid it. Now asks the window; also can't be hidden with the app. Tested with indite hidden |
| 234 | **How do I back up the Android signing key?** | — | 15 Oct | ✅ | Steps given (copy to 2 places + checksum check). Still your 5-minute task |
| 235 | **₹15k phone test last; AI review steps 1-2 first** | — | 15 Oct | ✅ | ROADMAP and ROADMAP_DETAIL reordered |
| 236 | **Hide swear words** | — | 15 Oct | 🧪 | Settings → Writing, off by default, ~40 clear-cut words (everyday words like "saala" left out). Since 16 Oct the saved note keeps the **real** word; stars only where it is shown, typed or exported (#253) |
| 237 | **Warn before sending meetings to AI (others' voices, training)** | — | 15 Oct | 🧪 | Asks every time for meetings and files; "Don't ask again" box |
| 238 | **How Wispr builds each feature; our best 2 options; challenges; more languages** | Research | 15 Oct | ✅ | Done: `docs/WISPR_DEEPDIVE.md` (16 Oct). Its build items are now in ROADMAP.md |
| 239 | **Remind me about the Android signing key change at Google Play publishing time** | 15 Oct | ✅ | ROADMAP "Before testers" now carries the warning: the build uses Android's debug key (alias `androiddebugkey`, password `android`, both public in `android/app/build.gradle:42`). Play rejects it; switch to a real release key before strangers install, because a later key change forces every tester to uninstall |
| 240 | **Long dictation is slow and arrives in chunks** | 15 Oct | ✅ | Fixed 16 Oct (same cause as #244): ~40x fewer key events, character-exact at 1,576 chars in TextEdit and Chrome |
| 241 | **Remind me about the signing key at the next Android build, not now** | Mac app + leadership demo come first | 16 Oct | ✅ | ROADMAP "Before testers" now opens with a trigger line: next Android build, do the release key first. Confirmed the tester keystore is byte-identical to `~/.android/debug.keystore` |
| 242 | **Update the demo with the suggested changes** | 16 Oct | 🧪 | `mac/demo.py`: gold-edge scene added (22 lines now), Ask AI line names "Make it a prompt", Insights line names AI usage, the "about a second" claim narrowed to "a second for a sentence", and the meeting→AI warning is pre-answered in `stage()` so it cannot interrupt a take |
| 243 | **Improve "Make it a prompt"** | 16 Oct | 🧪 | Rewritten to Anthropic's published guidance: says *why* (the other AI cannot hear the recording), five numbered parts, one worked Hinglish→prompt example, and a rule to keep Indian words with a gloss. Also `max_tokens` 4000 → 8000 and a cut-off answer now says so instead of looking complete |
| 244 | **Long dictation into an input field arrives slowly, in bursts** | 16 Oct | ✅ | Fixed 16 Oct: text typed in chunks instead of one key event per character (~40x fewer), checked in TextEdit and a Chrome textarea |
| 245 | **Put the swear-masking fix on the roadmap** | 16 Oct | ✅ | ROADMAP "Now" item 8. Masking currently deletes the real word before the note is saved, which breaks R5 (nothing is deleted silently). Fix is to mask on display and on output, keeping the raw text stored. Off by default, so nothing lost yet |
| 246 | **Accessibility keeps breaking — solve it once and for all** | 16 Oct | ✅ | Root cause: the app broke its own signature every run (Python wrote 249 `.pyc` files into the bundle; macOS ties Accessibility to that signature). Fixed, verified the seal survives a full run, and indite now warns at start-up if it ever breaks again. One trigger left — rebuilding — which the signing certificate will close after the demo |
| 247 | **Pill shows but recording is stuck; nothing written** (asked again 16 Oct, after a meeting) | 16 Oct | ✅ | A CoreAudio deadlock (macOS's audio system), caught with a stack trace. The first fix (abandon the stuck close) **did not hold**: the lock stays held until the app quits. Now indite notices it (close stuck, or an open that takes over 8 s) and restarts itself on the next press, at most once in 10 min, else it says "restart the Mac". Critic-reviewed. It has since restarted indite by itself 3 times on real lock-ups (log, 17 Oct) |
| 248 | **Full end-to-end test before the demo** | 16 Oct | ✅ | 21 of 21 pass. Four real bugs found and fixed on the way (two of them introduced by me the night before) |
| 249 | **Plan the demo from the research, then record it** | 16 Oct | 🟡 | `docs/DEMO_PLAN.md` + `demo.py --short` (3:20, 8 beats) built. Waiting on you: your narration or synthetic, show a real error or not, and private windows closed before the screen recording starts |
| 250 | **Should indite become a personal assistant (Slack, email, Gmail, Drive, "notify him and ask for an ETA"), or just use Claude?** | 16 Oct | ✅ | Answered, critic-reviewed: use Claude (or Gemini) for actions; build nothing new now. indite = capture (offline Hinglish, hotkey, meetings, archive); sharing to Claude already exists. Only real gap: WhatsApp, where a one-tap pre-filled message is the cheap option if testers ask (unproven) |
| 251 | **Record back-to-back meetings without waiting; show a working dot on the recording and the tab until it's done** | 16 Oct | 🧪 | Built and tested in the real app with sample audio: meeting B started while A was still finishing; each kept only its own words. Red dot on Meetings while recording, grey while anything is still working (Files and Dictations too); rows say "Finishing the last words…" then "Finding who spoke…". Also fixed: **a 2nd meeting in one session never started at all** (macOS refused a class defined twice), a 2nd meeting kept the 1st's lines, and a failed start left the mic on. Not yet tried on a real call |
| 252 | **Evaluate the personal-assistant idea more deeply (two-way, agentic, one app, onboarding)** | 16 Oct | 🔬 | Critic-reviewed: no general agent (free Hindi assistants; reading the ETA reply from WhatsApp/Gmail breaks WhatsApp's terms and the no-internet rule). The only differentiated slice is "talk to your own recordings + follow-up drafts". Proposed zero-code test: 7 days of Claude Code over indite's notes, pass/fail bar set in advance |
| 253 | **Swear masking: don't delete the word; keep the first letter, the rest as stars** | 16 Oct | ✅ | Fixed: the note now stores the real word; masking ("c******") happens only where text is shown, typed, copied, previewed or exported. Check in `mac/store.py`. Off by default |
| 254 | **Where is the Wispr Flow comparison, and why isn't it in the roadmap? Give me a prioritised roadmap; park ₹15k phone, Mac certificate, build 29 check, Android key backup** | 16 Oct | ✅ | Found in 3 docs (MAC_PLAN §6, ROADMAP_DETAIL, WISPR_DEEPDIVE); ROADMAP.md only pointed at them. ROADMAP "Now" rewritten (9 items, critic-reviewed) with the Wispr items in; a "Parked" table holds the 4 parked items; stale lines fixed |
| 255 | **Separate Android and Mac roadmaps, same app on both, adapting only to platform limits; combine every past plan; prioritise** | 16 Oct | ✅ | ROADMAP.md now has: how the two apps relate (limits table, parity gaps), a Mac roadmap (11 items), an Android roadmap (7 items, gated on the release key), and "both apps, later". Built from an inventory of every planning doc; critic changed 4 orders (e.g. Android backup check before the key switch) |
| 256 | **Can't access recordings even with "Keep audio" on** | 16 Oct | ✅ | They were saved (28 files) but the window had no way to open them. A note's ⋯ menu now has "Play recording" and "Show recording in Finder" (meetings open both tracks). Tested Show in Finder |
| 257 | **Personalisation: learn each user's way of speaking** | 16 Oct (asked before as #188, #227) | 🔬 | Plan in ROADMAP.md "Personalisation": your words (built) → learn from accepted fixes (AI review) → engine priming (experiment); measured by fixes per 100 words. Cut by critic: per-user voice training (no data, no way to load it), style rules (= word fixes), "rewrite in my style" (no asks) |

| 250 | **Text card: cap it at 6 seconds, keep the dynamic timing, and keep it visible while the pointer is on it** | 16 Oct | ✅ | `Preview.CAP = 6.0`; the 4 s + 0.25 s/word rule stays below that. Hover keeps it up — read by asking where the pointer is, not by a tracking area, so the card still never swallows a click. Also fixed: nothing cleared the card when the next dictation started, and Settings claimed "4 seconds" |
| 251 | **AI actions inside that card** | 16 Oct | 📋 | On the roadmap ("Now" item 9), not built. Needs the card to accept clicks only while hovered, plus a working/answer state, because an AI answer takes longer than the card lives |
| 258 | **Text card buttons: Ask AI, Make it a prompt, Translate** (asked 16 Oct as the 2nd #251; built now) | 17 Oct | 🧪 | Built: three buttons under the text, only with AI on and only for a saved note. The card takes clicks only while the pointer rests on it. Prompt / Translate keep the card up with "working…", then show the answer and copy it. Ask AI opens that note's Ask AI panel. Looks right on screen; not yet clicked through on a real dictation |
| 259 | **"Always fix" could break a word that is right in another context** | 17 Oct | ✅ planned | Critic: real for fixes whose wrong side is a real word ("in diet", "B"); safe for gibberish ("Rohith"). Added to Mac #7: warn with how often the wrong words appear un-fixed elsewhere, and store the engine's original text so a bad rule can be undone. Android #4: auto-learn refuses one-letter words |
| 260 | **Are all the Wispr items on the roadmap?** | 17 Oct | ✅ | Four were missing (confidence-only flags, two-call review, Topics in Insights, name packs) plus a whispered-speech test: added under "Mac later". ⚠ Request numbers 250 and 251 are used twice (two sessions) |
| 261 | **Card: Ask AI fixed; other buttons = favourites; drop "Translate to English"** | 17 Oct | 🧪 | Built smaller (critic): Ask AI fixed; slots 2-3 = your two most-asked AI actions with their last style/language, starting as Make it a prompt + Rewrite · Formal; changes only at restart. Pin setting only if asked after a week |
| 262 | **Say "to do …" and it goes straight to the To do list** | 17 Oct | 🔬 not now | Critic: would fire on your normal sentences to Claude; no undo. In ROADMAP "Not doing" with a trigger (~30 real to-dos) and a smaller option (a To do button on the card) |
| 263 | **Tags on To do: Office / Personal / Daily life / Rules** | 17 Oct | 🔬 not now | 2 to-dos exist. Same trigger as #262 |
| 264 | **Copy gave my original words, not the prompt (card and in-app Copy)** | 17 Oct | ✅ | Both copy paths tested and copy the right text. Causes were UX: the card's answer takes ~9 s, so pasting early gives the old clipboard; the note's big copy icon copies what you said, while the answer's Copy sits in the Ask AI panel. Fixed: card says "copied when ready - paste after the tick", a sound when copied, "✓ Make it a prompt copied"; the note's icon is "Copy what you said" and points to Ask AI when answers exist; toasts name what was copied |
| 265 | **To do button on the card** | 17 Oct | ✅ | 4th button, works with AI off too; one tap adds the note to To do. Tested |
| 266 | **First-principles UX pass on every flow; then build one by one** | 17 Oct | 🧪 | Audit of 11 flows → critic → 6 fixes built (Copy at the top of answers, retry via the card's buttons, To do empty-state wording, no setup-time Python alert, sound for the hotkey during a meeting, Fix a word fixes this note) + 4 bugs (#268). Next: offer the card in setup. Dropped list in ROADMAP |
| 267 | **Insights: proper KPIs, charts, dashboard, data-vis thinking** (asked again: keep the old page, add and group) | 17 Oct | 🧪 | My rebuild was rolled back. The original page is kept, grouped under Usage / Speed / Where & when / Meetings, files & AI; added: dictations today, words in a typical dictation, typical and slow wait (instead of the average), AI answers by action. Weekday pattern, speakers found and accuracy wait for data |
| 268 | **Bugs found by the UX audit** | 17 Oct | ✅ | Long AI answers on the card lost their "copied" line (now keeps the start); a meeting stayed LIVE after a restart (cleared at start-up); who-spoke failures said "The AI couldn't answer" (own title now); the card could catch a click if the pointer was already resting where it appeared (clicks now wait until the pointer moves) |
| 269 | **Copy UI was made inconvenient; redo it from first principles; check copy end to end** | 17 Oct | ✅ | Earlier copy changes rolled back. Now one copy icon everywhere, on the text it copies, turning into ✓. Tested end to end: note text, prompt, translate, improved, original, card. Also fixed: copying or exporting a meeting ignored renamed speakers |
| 270 | **After speaking, the words should be on the clipboard; after any AI action, the answer should be on the clipboard; the card's copy icon is not needed** | 17 Oct | ✅ | New setting "Also keep it on the clipboard" (on): typed words are copied too, and every AI answer (card buttons, Rewrite · Formal, Ask AI panel) is copied the moment it lands. Card copy icon removed; card answers now wrap properly and hide markdown stars. Tested end to end in TextEdit: dictation → clipboard = your words; card Rewrite · Formal → clipboard = the rewrite; Ask AI Summary → clipboard = the summary |
| 271 | **One combined roadmap: Android and Mac apart, done and next apart, every older roadmap folded in so this is never redone** | 17 Oct | ✅ | ROADMAP.md rewritten: Mac (done / next in order / later / parked), Android (same), personalisation, both-apps later, founder decisions, not doing. The 10 Oct sections moved to docs/ROADMAP_ARCHIVE.md after their open items were carried over. ROADMAP_DETAIL, MAC_PLAN, WISPR_DEEPDIVE and AI_MODES now say "detail only - ROADMAP.md wins" |
| 272 | **Real speech test after 50 recordings; should I also record sentences you give me?** | 17 Oct | ✅ answered | Waits for 50 dictations with audio. Recommended mix: ~35 of your normal dictations (you type what you really said) + ~15 sentences I write, read aloud (names, numbers, ₹, Hinglish) - read speech is cleaner, so it flatters the score |
| 273 | **Build the remaining Mac features** | 17 Oct | 🟡 | Done: #3 Mark likely mistakes (tested end to end), #4 fixes count on Insights, #5 engine-hint test (not shipped: +1 word on 60 clips), #7 part 1 edit + Undo (tested). Left: meeting line edits + per-line speaker fix (#7 part 2); #6 waits for the real speech set |
| 274 | **Did we include everything discussed across timelines and accounts?** | 17 Oct | ✅ | Audit of every request row, the work log, 185 commits and 302 founder messages from 9 chat logs: nothing large was lost; 11 small items and 8 pending decisions were added to ROADMAP.md, 7 statuses fixed. ⚠ Request numbers 178-192 and 250-251 are used twice (two sessions numbered in parallel) |
| 275 | **Research Google voice typing (Gboard) and plan competitor research** | 17 Oct | ✅ | `docs/research/COMPETITORS.md`: Gboard's best voice features need a Pixel and English; for Hindi it likely types Devanagari (Roman Hinglish by voice unverified - a 10-min hands-on test is first). Ideas to test: spoken "comma / new line", undo the last typed text, say a word again, mic stays on across messages. Plan: first 5 = Gboard, Sarvam Edge, Samsung/OnePlus, Superwhisper, Wispr refresh; one 15-sentence script through each; monthly refresh. Desk research only, no critic yet |
| 276 | **Keep the decisions waiting on me in a separate file; roadmap says to solve them** | 17 Oct | ✅ | `docs/DECISIONS.md` (13 waiting, 3 decided); ROADMAP.md points to it |
| 277 | **"Dragging is not working"** | 17 Oct | ❓ | The Mac pill was never draggable (it ignores the mouse so it never steals a click); the window drags by its top strip. Asked: which one? (D13) |
| 278 | **(My misreading of #279)** - I planned a read-aloud speech-test recorder instead | 17 Oct | ⚠ misread | Kept because the speech test is still Mac next #1: `docs/SPEECH_SET_PLAN.md`, critic-reviewed (Dictionary must grow to ~20 names first). No code was changed |
| 279 | **An in-app player for recordings: a UI while it plays, the matching transcript part highlighted; change that part; pause / stop; more** | 17 Oct | 🟡 | Built: Listen view (controls, speed, You/Others track, lit line, click to jump, Space/←/→), Edit / Copy / ▶ line on every line with Undo (word times kept), and the **word being spoken lit, every word clickable** (word times lined up once per note in the background). Tested: unit tests, live (muted) before the rule, headless after it. Left: the meetings' two-track clock (bug), and a visible check once you OK it |
| 280 | **Highlight the exact part being played in the text, so the recording and text are linked and corrections are easy** | 17 Oct | 🧪 | The spoken word lights up inside its line; click any word to play from it. Needs the engine's word times (full window, timestamps on per request): ~4 s per 20 s of audio, once per note, kept as "wt". ⚠ While it runs, a dictation can wait up to ~4 s |
| 281 | **Rule: our own design guidelines, not the common AI look; always add to them and refer to them** | 17 Oct | ✅ | `docs/DESIGN.md` (built from the current app); rule in CLAUDE.md and HANDOFF; memory saved |
| 282 | **Rule: test in a separate full-screen space, not on my screen** | 17 Oct | 🟡 | Rule in CLAUDE.md and HANDOFF; memory saved. Research: a separate Space can't be created on macOS; a hidden **test copy** of indite can (own data folder, engine port 8712, no hotkey/pill/card/menu icon, window off-screen) - on the roadmap. Done now: an `eval:` hook so tests read the window without your clipboard, and restarts in the background (`open -g`) |

| 283 | **Listen view and its transcript box should look like the rest of indite** | 17 Oct | 🧪 | Restyled to the note list's look: 22 px gutter, speaker colours as in the list, 14 px text, hairline rows; player is one grey strip with a round play button and a thin orange slider; no orange box or bar on the playing line (grey instead), the spoken word in soft orange; line actions are icons on hover; Listen tab got a speaker icon. Checked off-screen (headless render, light + dark), page reloaded in the background. Pattern added to `docs/DESIGN.md` |
| 284 | **Pick the card's favourite buttons myself** ("favourite selection is not available") | 17 Oct | 🧪 | Settings → Look & sounds → Card buttons: two dropdowns, each Automatic (your most used) or any AI action, Rewrite style or Translate language. Applies at once. The 17 Oct critic said "pin setting only if asked" - now asked. Tested hidden: saved, read back, reset to Automatic |
| 285 | **Keep building the Mac roadmap one by one, test, fix bugs, put what needs me in the decisions file; evaluate every text in the app** | 17 Oct | 🧪 | Built today: card buttons in Settings, Both tracks + one clock, test copy, Record this call?, own hidden words, setup step 5, per-line speaker fix + join, speech-test tools. Decisions D14-D19 added. Copy: an independent review found 12 must-fix and ~35 clarity issues; all musts and most others fixed (63 rows reviewed). Left: menu-bar emoji icon, AI wait-time hint (needs real timings) |
| 286 | **Can Wispr-style cleanup levels (None / Light / Medium / High) work without AI?** | 17 Oct | ✅ answered | None: yes. Light: filler words yes (rules), grammar no. Medium/High: need a language model - possibly a small one on the Mac (offline, unproven for Hinglish, D17). Critic before any build |
| 287 | **Listen orange highlight not working end to end; call recording with headphones didn't capture the others** | 17 Oct | 🧪 | Highlight: the engine sometimes answers "nan" with timestamps on - now retried with 0.5 s lead-in, else times estimated from the sound. Calls: the call's sound capture died 7 s into a 13-min call (headphones) and was never restarted - now reconnects on an error or 4 s of nothing, and says so; the meeting shows and logs which mic it uses. Needs one real call (D20) |
| 288 | **Full UI/UX review + end-to-end test of every screen and flow; fix bugs and improve** | 17 Oct | 🧪 | Two independent agents: 41 screens reviewed (37-item plan), 17 bugs found off-screen. Fixed: all 4 high and 5 medium bugs, the low ones, and UI plan items 1-21 (no behaviour change). Behaviour changes (items 24-37) wait for the critic |
| 289 | **Speech test: is "To check" manual?** | 17 Oct | ✅ answered | Yes, on purpose: only you know what you said; an AI checking itself proves nothing. Critic: time 5 notes first; a quicker check mode only if one takes > 45 s |
| 290 | **The app didn't run on my boss's Mac ("nothing happened")** | 17 Oct | 🧪 | Cause: it was a shell around this Mac's project folder, built for macOS 26 only, engine tied to an old folder. Built `dist/portable/indite-mac.zip`: self-contained, macOS 14+, any Apple Silicon, shows a message instead of quitting silently, READ ME FIRST + Help section inside. Checks stop a bad build (D21) |
| 291 | **Run the critic on the 14 behaviour changes; build what passes; polish items** | 18 Oct | 🧪 | Critic: build 6, smaller 7, drop 2 (row click opens panel; new speaker menu). Built: pill/card on the screen you work on; Stop for long files (keeps parts done); ↑↓ in menus; ⌘Z after delete; Undo for Dictionary/AI-answer removal; search on Meetings and Files; Try again on AI errors; Settings… ⌘, and Transcribe a file… ⌘O; long dictations fold to 6 lines; Listen: play from the time, select text freely; card says when words were only copied; Speech test moved to Writing; Someone new…; click a Dictionary entry to edit. Kept red hands-free dot (DESIGN: red = recording). Open: one unexplained Who spoke error in the test copy (not reproduced; a lock added) |
| 292 | **Two small Mac items: own menu-bar icon, AI wait-time hint** | 18 Oct | 🧪 | Menu bar: indite's own five-bar mark (template image, light and dark) instead of the 🎙 emoji; status as ⚠ … ● 3/10 beside it. Ask AI: "Usually about 8 s" from the last 30 real answers (your log: 34 answers, typical 8.1 s, 1 in 10 over 11.6 s); nothing shown until there are 3 |
| 293 | **Do the pending items: UI leftovers, long names, roadmap page, handoff; then the Who spoke error; then competitor research** | 18 Oct | 🧪 | Done: AI settings order, To do box, no repeated answer heading, lone Insights tile folded in, names cut at a word; roadmap page republished (same link); handoff updated. Who spoke: not reproduced in 3 runs (lock kept), but found and fixed a real bug - a stopped file ran Who spoke over the whole source (229 s). Competitor desk research running |
| 294 | **"Don't save the next dictation": how it works, then build it** | 18 Oct | 🧪 | Menu bar → "Don't save the next dictation" (tick + "private" beside the icon). The next dictation is typed but not saved, not copied, no audio, not logged; card says "Not saved"; switches itself off. Tested in the hidden copy. Help explains it |
| 295 | (found while restarting) **indite had crashed overnight** | 18 Oct | ✅ fixed | Cause: a volume / brightness / play key; the keyboard library handled it on a background thread, which macOS 26 kills. Media keys are now ignored before it sees them (indite never uses them). Hotkeys unaffected |
| 296 | **Start creating the remaining capabilities** | 18 Oct | 🧪 | AI review step 2 built (switch, on for you): Ask AI → Review with AI. Filler-word removal dropped on evidence (critic agreed): the engine already drops um/uh; fillers in 7 of 310 dictations. On-Mac AI clean-up still needs D15/D17 |
| 297 | **Check the meeting I just recorded** | 18 Oct | 🧪 | Both meetings (9:02, 9:08) recorded fine; macOS stopped the call's sound twice and indite reconnected both times (the 17 Oct fix, proven live). Found: in an in-person conversation everyone came out as "You" (Who spoke split only the silent call track). Fixed: a silent call track now means the mic track is split (dry run: 3 and 5 voices; counts are guesses). Re-run ⋯ → Who spoke? on those two after the restart |
| 298 | **Pick several transcripts (Android), run Ask AI on the whole lot at once** | 23 Oct | 🧪 | Long-press a note → "Select (combine with others)" → tap 2–10 → bottom bar "Ask AI combined" → opens a new combined note whose text is each source's full transcript under a "— Clip N: name · date —" header; the normal AI drawer runs on it. Snapshot by design: deleting a source doesn't touch the combined note. Compiles clean (personal + public); not yet installed on the phone — version not bumped |
| 299 | **"Typed in" sometimes just copies to clipboard even though an input box is focused** | 23 Oct | 🧪 | Diagnosis first: `AutoPaste.paste()` now logs one of five reasons when it falls back to clipboard (A no focused editable box at tap, B node couldn't be refreshed, C focus moved away, D1 no longer editable, D2 now sensitive, E app refused ACTION_PASTE). Behaviour unchanged. Next real occurrence should surface the code in `adb logcat -s indite` and the real fix can be targeted |
| 300 | **Mac: hide the REC pill while sharing the screen** | 23 Oct | 🧪 | `setSharingType_(0)` on the Pill and the text Card (NSWindowSharingNone): macOS excludes them from Zoom/Meet/Teams/Loom shares, QuickTime screen recording, and ⌘⇧3 screenshots. One-liner, standard API. Not yet proven in a live share — needs one quick Zoom test |
| 301 | **Mac: multi-select transcripts → Ask AI combined (same as Android)** | 23 Oct | 🧪 | Dictations tab → kebab menu → "Select (combine with others)" → tick 2–10 → bottom bar "Ask AI combined" opens a new combined note. Snapshot by design: the full transcript of each source is copied under "— Clip N: title · date —" headers. `kind="combined"` protects it from the plain-dictation CAP. Self-check extended in `mac/store.py` (passes). Verified in the hidden test copy without touching your screen (bar renders, bars match selection, message to Python is the right shape). Needs restart `open -n -g dist/indite.app` after the log is quiet 2 min |
| 302 | **Use the critic only where it's needed; pick model and effort to save usage** | 24 Oct | ✅ done | Critic now only for features, app behaviour, security/privacy/data, or hard-to-undo changes; a quick test beats a critic; one critic, under 300 words, "critic: no change" if nothing changed. Updated in global instructions, CLAUDE.md, AGENTS.md, HANDOFF. Default model now Sonnet 5.5 + high (Opus 5.5 stays at medium for hard tasks via `/model opus`); the AI says when a task needs Opus |
| 303 | **How is AI cost calculated, is it exact? Add the missing 5.5 models** | 24 Oct | 🧪 | Answer: token counts are real, prices are a typed-in table, so it's an estimate. Added Opus/Sonnet/Fable 5.x and fixed wrong old prices (Haiku 5.5 was ~10x too high). OpenAI prices not re-checked; needs an app restart |
| 304 | **Dictation inside indite with no box focused was not saved; the card after it had no AI buttons** | 24 Oct | 🧪 | Cause: the app skipped saving whenever indite was in front, and macOS reports "box focused" when unsure. Founder's decision: save everything. Done; the page now tells the app about focus (typing vs clipboard only). Needs one real test on the Dictations page |
| 305 | **Make the card's AI buttons (Ask AI, Make it formal...) optional in Settings** | 24 Oct | 🧪 | Already existed: card on/off and the two button pickers. Added "AI buttons on the card" (off = To do only) |
| 306 | **Add two to-dos: wash clothes; an interview-prep agent** | 24 Oct | ✅ done | Both are on the To do page |
| 307 | **Is there a voice command like "make it formal" / "add to to-do" / "ask AI to translate"?** | 24 Oct | ✅ answered | No. Parked 18 Oct (revisit at ~30 real to-dos); today you use the card buttons or the note's AI actions |
| 308 | **Card buttons: darken on hover, show a clear pressed effect, and show that something is processing, then that it changed** | 24 Oct | 🧪 | Hover and press tints (only when a click would count); a pulsing "Make it a prompt…" line while the AI works, then the "Copied" answer. Tested headless; needs a look on the real card after a restart |
| 309 | **The two to-dos were not on the To do page** | 24 Oct | 🧪 | My mistake: saved as `True`, the page lists only `"open"`. Fixed in the data |
| 310 | **AI cost not showing; Insights shows 0** | 24 Oct | 🧪 | Cause: AI runs through the Claude login and the app discarded the CLI's usage. Now carried (list price, a chip on each new answer and the Insights "This month" line). Older answers stay "no cost reported" |
| 311 | **When "AI buttons on the card" is off, disable the two pickers instead of hiding them; improve that settings UI** | 24 Oct | 🧪 | Dependent rows are indented and disabled with a reason, never hidden (rule added to DESIGN.md) |
| 312 | **Let the user choose the model (the Claude login ignored the AI-model setting)** | 24 Oct | 🧪 | Model row now shows for the Claude login: account default / haiku / sonnet / opus / custom. Haiku measured ~40x cheaper than the default on one rewrite; quality unproven |
| 313 | **Ask Anthropic / Codex etc. which models and effort levels exist; let the user pick a version and an effort** | 24 Oct | 🧪 | Built: model + effort pickers fed by a catalog (live from Anthropic with an API key, built-in table otherwise), effort sent to the Claude CLI and Anthropic API. Live refresh untested (no key here); Codex not built (not installed here) |
| 314 | **Show AI cost in rupees at a rate the user types** | 24 Oct | 🧪 | Settings → AI → "Show AI cost in": Dollars / Rupees + "Rupees per US dollar". Used on the cost chip and Insights. No rate is guessed |
| 315 | **Search, filter and sort wherever they are needed; documented; proper UI/UX** | 24 Oct | 🧪 | One toolbar on Dictations, Meetings, Files, To do and Dictionary: filter chips, When, App, Group, Sort, count + Clear, multi-word search with marks. Help page "Find things"; DESIGN.md pattern; tested in headless Chrome |
| 316 | **Design it as if used for 2-3 years (grouping, search, filter, sort at that size)** | 24 Oct | 🧪 | Measured at 25,800 made-up notes: 100 rows at a time, month/year headings and filters, speed fixes (save 465 -> 0 ms, read 175 -> 8 ms). Limit: the page gets all notes on each update, fine to ~10,000 dictations |
| 317 | **(follows from #316) Keep more than 500 dictations** | 24 Oct | 🧪 | Settings → Privacy → "How many to keep": 500 (default), 5,000, Everything; asks before deleting. The founder was at 475 of 500 |
| 318 | **Filter and sort UI not appropriate / not on the design theme** | 24 Oct | 🧪 | Our own menus (chip-like buttons, filled when active) instead of system dropdowns; rules in DESIGN.md |
| 319 | **"How many to keep" UI not appropriate** | 24 Oct | 🧪 | Segmented choice + a banner that asks before deleting; option order fixed |
| 320 | **Search inside one long meeting transcript** | 24 Oct | 🧪 | Listen → "Find in this transcript": lit lines, marks, ↑ ↓ / Return, ⌘F |
| 321 | **Search "with codes" is not working** | 24 Oct | 🧪 | Read as "quotes": curly quotes returned nothing (fixed); accents ignored; codes like JIRA-123 and ₹4,500 tested. **If you meant something else, tell me what you typed** |
| 322 | **Filter / search by Fix, Always fix, Not a mistake** | 24 Oct | 🧪 | "Mistake review" menu on Dictations; each decision is now kept on the note (earlier decisions were never tied to a note) |
| 323 | **Delete must ask: transcript, recording or both** | 24 Oct | 🧪 | "Delete what?" with note and recording / recording only / words only, each with Undo |
| 324 | **Test everything end to end; audit; fix; commit** | 24 Oct | ✅ done | `docs/AUDIT_24OCT.md`: 24 findings fixed, 45 tests, real-code run with 0 errors |
| 325 | **Dictionary: keep capitals (jira → Jira, Widget Serve)** | 24 Oct | 🧪 | Capital-only fixes are allowed and apply the exact capitals |
| 326 | **Menu number did not match the list ("Terminal 315" showed 6; "Claude today" showed nothing)** | 24 Oct | 🧪 | Cause: counts ignored the other filters that were on. Now every count is faceted and matches the list; the toolbar names every filter that is on. Verified on invented notes and on your real notes (61 states, 0 mismatches) |
| 327 | **"How many to keep" warning keeps coming back after switching tabs** | 24 Oct | 🧪 | Cause: Settings un-hid every row on switching sections. The warning is now drawn only while a choice waits, and dropped when you leave |
| 328 | **Test everything properly: normal, negative, corner cases, every feature** | 24 Oct | ✅ done | 58 automated tests + 78 real-app checks, plus screenshots; found and fixed 9 more bugs, including silence saved as a note |
