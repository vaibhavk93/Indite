# Competitors: Google voice typing, and a plan for the rest

Written 17 Oct 2026; Part 3 added 18 Oct. Desk research only: **nothing here was tested by hand, and no critic has reviewed any idea yet.**
Every idea below is **unproven** until it passes the critic rule (HANDOFF) and, where it says so, a test.

---

## Part 1. Google voice typing (Gboard)

**Verdict: Gboard is free, on every Android phone, and good in English. For Hindi it most likely types Devanagari
(Hindi script), not Roman Hinglish, and its best features are English-only and Pixel-only. That gap is indite's reason to exist, but it is not yet confirmed by a hands-on test.**

**⚠ Remember:** the one question that matters most is still open. Does Gboard's mic, with the "Hinglish" keyboard
language picked, type Roman Hinglish? No source answers it (founder request #168). It needs a 10-minute test on a
real phone, with the 15-sentence script from Part 2.

### What it does, and how it works for the user

Tiers: **All** = any Android with Gboard. **Pixel** = Pixel 6 or later only ("advanced voice typing").

| Feature | How it works | Tier | Source |
|---|---|---|---|
| Works in any app | Mic key on the Gboard keyboard | All | [1] |
| Offline | "Faster voice typing" downloads an on-device engine (~85 MB at launch, English first). Hindi offline: **unverified** | All, per language | [2][3] |
| Hindi voice | Hindi supported for years; output is Devanagari | All | [4][6] |
| Hinglish / mixed speech | One language at a time. English words in Hindi speech often come out *in Devanagari* (e.g. "walk" in Hindi script; "dizzy" became "डीसी") | All | [6][7] |
| "Hinglish" keyboard language | Exists for **typing** (suggests Hindi and English words). Whether it changes the **mic**: **unverified** | All | [4] |
| Auto punctuation | Adds punctuation from your tone and pauses; toggle in Settings → Voice typing | Pixel, 6 languages, no Hindi | [1][5] |
| Spoken punctuation | Say "comma", "period", "question mark", "new line", "new paragraph" | All | [3] |
| Emoji by voice | Say "smiley emoji", "heart emoji" | All (common ones); more on Pixel | [1][3] |
| Simple commands | "Delete last word", "Clear" (last sentence), "Clear all", "Send", "Next" (next field), "Stop", "Undo" | Pixel | [1][3] |
| Editing by voice | "Change X to Y", "Insert X before Y", "Delete X", "Spell X as Y", "Capitalize X" | Pixel 8+, US English | [1] |
| Fix a word by tapping | Tap a word, then say or spell the replacement | Pixel | [3] |
| AI rewrite by voice | "Proofread this", "Make it concise", "Formalize", "Emojify it". Runs on the phone | Pixel 9+ (not 9a) | [1] |
| "Fix it" | Spots a likely error and offers a fix. **Needs internet** | Pixel 8+, US only | [1] |
| Open mic | Tap = one message. Double-tap = mic stays on across messages | Pixel | [1][3] |
| Type while mic is on | Keyboard stays usable while listening | Pixel | [1] |
| Floating voice toolbar | Hides the keyboard; small movable mic bar | All | [3] |
| Auto-switch language | With 2+ languages set, guesses which one you speak | Pixel | [1][3] |
| Learns from corrections | Saves your corrections on the phone; can delete in Settings → Privacy | Pixel | [1] |
| Profanity filter | "Block offensive words", on by default, shows `#` | All | WISPR_DEEPDIVE §5 |
| Help while speaking | An Info (?) button lists what you can say | Pixel | [1][5] |
| Speed | Words appear live as you speak (streaming). No measured numbers found | All | — unverified |
| Privacy | Pixel: dictated text stays on the phone, except "Fix it" and detailed edits (they send text, not audio). Non-Pixel or no offline pack: likely cloud. **Unverified** for Hindi | Mixed | [1] |

**Note:** Samsung phones do not ship Gboard by default [3]. Many testers may never have used it.

### On the Mac

There is no Gboard for Mac and no Chrome dictation that works in every app.

- **Google Docs voice typing:** Tools → Voice typing, in Chrome, Edge or Safari. Hindi is supported. Commands and
  punctuation are English only. Say "Stop listening" to stop [8].
- **Chrome's speech feature for websites** sends the audio to Google's servers [9]. Not offline, not private.
- So on the Mac, Google is not a real rival. Apple Dictation is (see Part 2).

### What indite could take from it

All ideas are **unproven**. Effort: S = hours, M = 1–3 days, L = a week or more.

| Idea | User value | Offline? | Fits rules? | Effort | Call | Why |
|---|---|---|---|---|---|---|
| Run the Gboard Hinglish test first | Tells us if our main edge is real | Yes | Yes | S | **Build (do)** | Every other row depends on it |
| Spoken "new line" / "full stop" / "comma" → symbol | Lists and messages without touching the screen | Yes | Yes | S | Test | Word swap, not a command. Risk: "comma" said as a normal word. Check 30 real dictations for false hits |
| "Undo" for the last thing indite typed | Safe way back after a bad dictation | Yes | Yes (helps "nothing deleted silently") | M | Test | Only undoes our own insert. Needs per-app check on Android |
| Tap a word, re-say it | Fix one wrong word fast on a phone | Yes | Yes | M | Test | Pencil-on-dictation exists on Mac; check if Android already covers it |
| Open mic across several messages | Long chats without re-tapping | Yes | Yes | M | Test | Battery and "is it still listening?" risk; ask testers first |
| Emoji by name ("heart emoji") | Small fun win | Yes | Yes | S | Skip for now | No one has asked; can already be a word fix (`heart emoji = ❤️`) |
| "Send", "Delete", "Clear all" by voice | Hands-free | Yes | **No** | M | Skip | Command mode was dropped: misfires, no undo (ROADMAP "Not doing") |
| Auto-switch language | No language picker | Yes | Partly | L | Skip | Already decided: picker, not auto-detect (WISPR_DEEPDIVE §0 C) |
| Live words while you speak | Feels fast | Yes | Yes | L | Skip | Dropped: draft models write Hindi script |
| Learns from corrections | Fewer repeat mistakes | Yes | Yes | — | Skip (have it) | Word fixes + Dictionary already do this |
| AI rewrite by voice | Polished text | Needs AI | Yes, via user's AI app | — | Skip (have it) | indite's AI actions already cover it |
| Profanity filter | Clean text | Yes | Yes | — | Skip (have it) | Shipped (WISPR_DEEPDIVE §5) |
| "Fix it" (spot likely errors) | Catches mistakes | Ours can be | Yes | — | Already planned | Matches "AI review step 1" (WISPR_DEEPDIVE §0 A) |

---

## Part 2. Plan for researching the other competitors

**Verdict: study 5 first (Gboard, Sarvam, Samsung voice input, Superwhisper, Wispr Flow refresh), with one fixed
Hinglish test, one table and an adopt / test / skip call per idea.**

### Who, grouped, and why

| Group | Who | Why study them |
|---|---|---|
| Indian-language voice | Gboard, Sarvam (Edge), Krutrim, Bhashini | Free or state-backed; Sarvam Edge is the main threat to "offline" |
| Dictation (Mac / PC) | Wispr Flow, Superwhisper, MacWhisper, Apple Dictation, Windows voice typing, Aqua Voice, Willow | The Mac app's direct rivals; Apple and Windows are free and built in |
| Meeting notes | Granola, Otter, Fireflies, Jamie, tl;dv | Mac meetings feature; Granola and Jamie record without a bot |
| Voice-note apps | AudioPen, Cleft, VoiceNotes | Notes window and AI actions on notes |
| Android built-in | Samsung and OnePlus voice input | What most Indian testers already have on their phone |

### Questions for each

1. **Features:** what does it do that we don't? Anything we dropped that they make work?
2. **Offline:** does it work in flight mode? Which parts stop?
3. **Hinglish:** does it output Roman script? How many words wrong on our script?
4. **Price in India:** free tier, monthly price in ₹, what the free tier caps.
5. **Privacy:** where does audio go? Is it kept? Is there an account?
6. **UX worth copying:** one or two patterns, with a screenshot.

### How to test

1. **Record the script once.** 15 fixed Hinglish sentences: names, numbers, English tech words, a question, a list, one noisy clip. Same voice, same phone.
2. **Hands-on** where free or a trial exists: play or speak the script, save the raw output, count wrong words.
3. **Docs** for features, offline and privacy claims. Note the page date.
4. **Reviews** (Play Store, Reddit, Product Hunt) for complaints. Treat vendor blogs as biased.
5. Mark every claim **tested**, **from docs**, or **unverified**.

**⚠ Remember:** never upload our recordings to a cloud tool unless they are the founder's own test script.
Never put recordings in git (the repo is public).

### Output

- **One comparison table:** rows = competitors; columns = offline, Roman Hinglish, words wrong on script, ₹/month, audio leaves device?, best pattern.
- **One adopt / test / skip line per idea**, each sent to an independent critic before it reaches the roadmap.
- Lives in this file. Old rows move to `docs/ROADMAP_ARCHIVE.md`.

### Order: first 5

| # | Who | Why first |
|---|---|---|
| 1 | Gboard (hands-on) | Answers founder request #168; free on most phones |
| 2 | Sarvam Edge | Biggest threat to the offline edge |
| 3 | Samsung / OnePlus voice input | What testers already use |
| 4 | Superwhisper | Closest Mac rival: offline, local models |
| 5 | Wispr Flow (refresh) | Already studied (WISPR_DEEPDIVE); check Hinglish since 2026 and India price |

### Cadence

- **Monthly, light (~1 hour):** check the first 5 for new releases and prices; re-run the script only if a big model update ships.
- **Quarterly:** go through the rest of the list.
- **Right away:** if a rival announces offline Roman Hinglish.

---

## Part 3. Desk research: Sarvam, Samsung/OnePlus, Superwhisper, Wispr Flow, Apple Dictation (18 Oct 2026)

**Verdict: no rival found gives offline, Roman-script Hinglish in every app today. indite's edge still holds on paper.
The two closest threats are Sarvam (it has an offline speech model, and a Mac dictation app called Kivi) and Wispr Flow
(Roman Hinglish, India price ₹320/month). Both send audio to the cloud today. None of this is tested by hand yet.**

How to read the labels:
- **docs** = from the vendor's own page (source number and date in brackets).
- **reviews** = from press, forums or competitor blogs (source given). Competitor blogs are biased.
- **unverified** = not confirmed by any source found; needs a hands-on test.
- ₹ figures for USD prices use about ₹85 = $1 and are rough.

**⚠ Remember:** this is desk research only. Nothing here was measured on our 15-sentence Hinglish script. The
"accuracy evidence" column is what each vendor claims, not what we measured.

---

### The comparison

| Competitor | Offline? | Roman Hinglish? | Accuracy evidence | ₹/month | Audio leaves device? | Best pattern to copy |
|---|---|---|---|---|---|---|
| **Sarvam Edge** (on-device model) | Yes, on-device (docs [1]) | Not stated (docs [1]) | "Competitive" WER, no numbers (docs [1]) | Not for sale to users; OEM deals only (docs [2]) | No, but cloud overflow when device is busy (docs [2]) | — (not a product yet) |
| **Sarvam Kivi** (Mac app) | Likely no: "powered by Saaras V4", a cloud model (reviews [6]) — unverified | Probably (Saaras has a "translit" mode, docs [3]); Kivi output unverified | None published | Free in alpha (reviews [5][7]) | Likely yes — unverified | Incognito toggle: paste without saving (reviews [8]) |
| **Sarvam Saaras API** | No, cloud only (docs [3]) | **Yes**, "translit" mode (docs [3]) | No WER published for v3/v4 (docs [3]) | ₹30 per audio hour (docs [4]) | Yes | Two output modes: Roman, or English-in-Latin + Hindi-in-Devanagari |
| **Samsung voice input** | Hindi offline pack: not found (reviews [10]) | No sign of it — unverified | One blog rates Hindi "Poor" (reviews [11]) | Free | Probably yes for Hindi — unverified | — |
| **OnePlus** | Uses Google voice typing (reviews [13], old) | Same as Gboard (Part 1) | None | Free | Same as Gboard | — |
| **Superwhisper** (Mac) | Yes, with local Whisper / Parakeet models (docs [14]) | No built-in Roman Hinglish found; Whisper writes Hindi in Devanagari — unverified | None for Hindi | Free tier; Pro $8.49 (~₹720) (docs [15]) | Only if you pick a cloud model (docs [14]) | Each stage (speech, AI clean-up) set local or cloud separately |
| **Wispr Flow** | No offline mode (reviews [20]) | **Yes**, "Hinglish" language, picked by hand (docs [17]) | Canto model tested on **English** only (docs [18]); Hinglish none | ₹320 (annual, India) (reviews [19]); free 2,000 words/week desktop, 1,000 mobile (docs [16]) | Yes, always | Floating "Flow Bubble" on Android (docs [18]) |
| **Apple Dictation** (Mac) | Hindi: **no**. Hindi is not on the on-device list (docs [22]) | No. Hindi output is Devanagari — unverified | None | Free | Yes for Hindi; not stored unless you opt in (docs [23]) | Blue underline on unsure words; click for alternatives (docs [21]) |

---

### 1. Sarvam

**In short: Sarvam is the biggest long-term threat. It has an offline speech model, a Roman-script output mode, and a
Mac dictation app. But today these are three separate things, and no one product combines them.**

Sarvam has three pieces. They are easy to confuse:

```
                         SARVAM
                           |
        +------------------+------------------+
        v                  v                  v
 +--------------+   +--------------+   +--------------+
 | Sarvam Edge  |   | Saaras API   |   | Kivi (Mac)   |
 | on-device    |   | cloud        |   | dictation    |
 +------+-------+   +------+-------+   +------+-------+
        |                  |                  |
   + offline          + Roman "translit"  + hold Fn, types anywhere
   - no app, OEMs     - cloud only        - likely cloud (Saaras V4)
   - flagship chip    - ₹30/hour          - free alpha, Mac only
```

| Question | Answer | Label |
|---|---|---|
| Features we lack | Kivi: "Hey Kivi" mode (Fn + Control) drafts or reformats text by voice; learns corrections; 22+ languages; Windows coming | reviews [5][7]; YourStory [9] (18 Aug 2026) |
| Features we lack | Saaras v4: keyterm prompting (up to 50 words), speaker separation in batch | docs [3] |
| Offline | **Edge**: 74M-parameter speech model, ~294 MB, runs fully on device, 10 Indian languages, auto language detection | docs [1] (14 Feb 2026) |
| Offline | Edge product page mentions an "India cloud fallback" when the device is at capacity | docs [2] (undated, © 2026) |
| Offline | Edge was benchmarked on a Snapdragon 8 Gen 3 (phones from ~₹40,000). No budget-phone numbers | docs [1]; reviews [12] (18 Feb 2026) |
| Offline | Kivi offline: not stated anywhere. Its launch video title says "Powered by Saaras V4" (a cloud model) | reviews [6]; **unverified** |
| Hinglish | Saaras "translit" mode gives Roman output, e.g. "Mujhe flight book karni hai." "codemix" mode keeps English in Latin and Hindi in Devanagari | docs [3] |
| Hinglish | Edge: Roman output not mentioned | docs [1] |
| Hinglish | Kivi: "hindi, english, or both in the same breath" (landing page, as quoted by search). Which script it writes: **unverified** | reviews [7] |
| Accuracy | Edge: "competitive" on the Vistaar benchmark; press says it beats Google Cloud on Hindi. No WER numbers published | docs [1]; reviews [12] |
| Accuracy | Saaras v3/v4: no WER on the model page | docs [3] |
| Price | Kivi: free in alpha | reviews [5][7] |
| Price | Saaras API: ₹30 per audio hour. Free credits: ₹100 (docs) or ₹1,000 (pricing page) — they conflict | docs [4] |
| Price | Edge: not sold to users; "contact us" OEM deals (Qualcomm, Bosch, Meta glasses, HP) | docs [2] |
| Privacy | Kivi: keeps a local history database; a "zero data retention" setting keeps only a few days; an incognito toggle pastes without saving | reviews [8] (third-party tool README) |
| Privacy | Kivi privacy policy effective 26 Jul 2026, by Axonwise Pvt Ltd (Sarvam). Could not open it (blocked) | reviews [7]; **unverified** |
| UX to copy | Kivi's incognito toggle (one tap: this dictation is not saved) | reviews [8] |
| UX to copy | Saaras's two Hinglish modes: all-Roman, or English-in-Latin + Hindi-in-Devanagari | docs [3] |

**Note:** heykivi.ai and its privacy page were blocked on this network. Kivi details come from search snippets and
third-party pages. The founder should open heykivi.ai himself.

---

### 2. Samsung and OnePlus voice input

**In short: no evidence that Samsung or OnePlus offer offline Hindi voice typing, or any Roman Hinglish voice output.
The evidence is thin. A hands-on test on a real Galaxy and OnePlus phone is the only way to settle it.**

- **Samsung Keyboard voice, Hindi:** for years users reported no Hindi voice input (forum posts 2019, 2021). Reviews [10].
- **Samsung offline Hindi pack:** a Sept 2025 forum user asked for one; Samsung gave a generic reply. Reviews [10].
- **Workaround on One UI 8 / 8.5:** one user says switching the keyboard to Hindi and tapping the mic "works very well most of the time." Reviews [10]. **Unverified.**
- **Quality:** one blog rates Samsung voice input "Poor" for Hindi vs "Good" for Google. Reviews [11] (vendor blog, biased).
- **Galaxy AI:** Hindi is in the 22-language list for Live Translate, Interpreter, Note Assist and Transcript Assist (as of Mar 2026). Docs [12a].
- **Galaxy AI network:** Transcript Assist transcription and summaries "require a network connection and Samsung Account login." Docs [12a].
- **Samsung Voice Recorder → Transcript Assist** is the closest Samsung feature to our Android "record" mode. It needs internet and an account. Docs [12a].
- **OnePlus:** an old (OxygenOS 10) guide says voice typing in the OnePlus keyboard runs on Google voice typing. Reviews [13]. Current OxygenOS behaviour: **unverified**.
- **Price:** free on both.
- **Privacy:** Samsung's AI needs a Samsung Account for transcription (docs [12a]). Where keyboard voice audio goes: **unverified**.

**Note:** Part 1 says Samsung phones do not ship Gboard by default. So Samsung voice input is what many Indian
testers actually see first. That makes the hands-on test important.

---

### 3. Superwhisper (Mac)

**In short: the closest Mac rival on privacy. It runs fully offline with local models. But it has no Hinglish model,
and Whisper writes Hindi in Devanagari, so Roman Hinglish would need an AI clean-up step.**

| Question | Answer | Label |
|---|---|---|
| Features we lack | File transcription, system audio, speaker separation, "context awareness", custom AI "modes" (e.g. Mail, Super) | docs [15] (undated) |
| Features we lack | One license covers Mac, Windows and phones | docs [15] |
| Offline | Speech-to-text and the AI clean-up step can each be set local or cloud. Fully local = "no audio or text ever leaves your machine" | docs [14] |
| Offline | Local engines: Whisper sizes, Parakeet. Cloud engines (e.g. Nova, Scribe) need internet | reviews [24] (tl;dv) |
| Hinglish | No Hinglish option found. With "Automatic" language, non-English speech can come out as English | docs [25] |
| Hinglish | Roman Hinglish would need a custom AI mode to rewrite the text. **Unverified**; never tested |  |
| Accuracy | No Hindi numbers found | — |
| Price | Free: unlimited dictation with local Whisper, 2 modes, no AI. Pro: $8.49/mo (~₹720), $84.99/yr, $249.99 lifetime. 3,000 free Pro words to start. 40% off for students. No India price shown | docs [15] |
| Privacy | "We never store your transcripts or audio" on their servers. Audio and transcripts are kept **on your Mac** in History | docs [14] |
| Privacy | Cloud providers are under zero-data-retention terms (they delete data right away) | reviews [24] |
| UX to copy | Separate local/cloud switch per stage, so a user can keep speech local and still use cloud AI | docs [14] |
| UX to copy | "Modes": one saved setup per task (e.g. email vs chat) | docs [15] |

---

### 4. Wispr Flow (what changed in 2026)

**In short: Wispr is now a serious India player. It has a Hinglish option, Android, an India price and a meeting
notetaker. It is still cloud-only, and it has published no Hinglish accuracy number.**

New since WISPR_DEEPDIVE:

1. **Android launched** (early access 23 Feb 2026), using a floating "Flow Bubble." Docs [18].
2. **India price:** ₹320/month on annual plans, from Dec 2025. Global Pro is $15 monthly or $12/month annual. Reviews [19] (TechCrunch via AI Chat Daily, 10 May 2026); docs [16].
3. **Hinglish model:** in beta "earlier in 2026." India growth went from ~60% to ~100% month on month after it. Reviews [19].
4. **Canto, their own speech model** (17 Sep 2026), now on for everyone. Lowest WER in their test of 9.8 hours of **English** recordings. Docs [18].
5. **Notetaker** (meetings, no bot joins the call), Mac and Windows only. Meeting transcription in 21 languages, Hindi included. Docs [16][18].
6. **Free plan** now 2,000 words/week on desktop, 1,000 on mobile. Docs [16].

| Question | Answer | Label |
|---|---|---|
| Features we lack | Android floating bubble; Notetaker with "ask questions across meetings"; send meeting notes to Claude/ChatGPT (MCP); Scratchpad notes window | docs [16][18] |
| Offline | No offline mode | reviews [20] |
| Hinglish | Must be picked by hand; "Writes Hindi in Latin letters and formats English normally." Not auto-detected. No auto-detect on Android | docs [17] |
| Accuracy | No Hinglish WER published. Press quotes "30% to under 10%" error for hard conditions, as a company claim | reviews [26] |
| Price | ₹320/month (annual, India). Free tier: 2,000 / 1,000 words a week | reviews [19]; docs [16] |
| Privacy | Audio always goes to their servers. "Privacy Mode" = zero data retention (nothing kept). Cloud Sync is a separate switch | reviews [20] (Wispr enterprise page and help centre, via search) |
| UX to copy | Floating bubble that recovers on its own if Android's battery manager kills it | docs [18] (2 Jul 2026 entry) |
| UX to copy | Hold-to-delete key that speeds up from letters to whole words after ~2 s | docs [18] (Jun 2026 entry) |

**Note:** our pricing-page fetch showed USD prices, not ₹. The ₹320 figure is from press, not the pricing page.

---

### 5. Apple Dictation (macOS)

**In short: free and built in, but Hindi is not offline. Hindi dictation sends audio to Apple. There is no Hinglish or
Roman Hindi option.**

| Question | Answer | Label |
|---|---|---|
| Features we lack | Type while dictating (Apple silicon); say "heart emoji"; say "new line"; auto punctuation; no length limit; stops after 30 s of silence | docs [21] (macOS 27 guide) |
| Offline | ~50 languages run on device after a model download. **Hindi is not one of them.** English (India) is | docs [22] |
| Hinglish | No "Hindi (Latin)" or Hinglish listed. Auto punctuation and emoji are not available for Hindi | docs [22] |
| Hinglish | Switch language mid-dictation with the Globe key. Mixing Hindi + English in one sentence: **unverified** | docs [21] |
| Accuracy | None published | — |
| Price | Free | — |
| Privacy | Server dictation is "not stored unless you opt in" to Improve Siri & Dictation. Requests use a random ID, not your Apple Account | docs [23] |
| UX to copy | Unsure words get a blue underline; click to pick another guess | docs [21] |
| UX to copy | Keyboard settings say plainly whether your dictation is processed on device | docs [21] |

---

### Quick lines: MacWhisper, Granola, Aqua Voice

- **MacWhisper:** local Whisper, offline, mainly for files not live dictation. About €59 one-time. Reviews [27] (competitor blog).
- **Granola:** meeting notes, no bot. Audio reportedly deleted after transcription. Business $14/user/month. Hindi: not found. Reviews [28].
- **Aqua Voice:** cloud-only dictation, no offline mode. $8/month; free tier 1,000 words total. Reviews [29] (competitor blog).

---

### Ideas for indite

**⚠ Remember:** every row is **unproven**. Each must go past indite's independent critic before it reaches the roadmap.
The call is a starting suggestion, not a decision.

| Idea | Seen at | User value | Offline? | Call | Why |
|---|---|---|---|---|---|
| Run the 15-sentence test on Samsung, OnePlus, Kivi, Wispr, Apple | All | Turns desk claims into numbers | Yes (our side) | **Test (do first)** | Every "unverified" above depends on it |
| "Don't save this one" toggle (incognito dictation) | Kivi | Privacy for one sensitive message | Yes | Test | Small; check it is not already covered by deleting from history |
| Tell the user plainly "this ran on your device" | Apple | Trust; our main edge made visible | Yes | Test | Cheap message; risk of clutter |
| Underline unsure words, click for other guesses | Apple | Faster fixes | Yes | Test | Needs word confidence; WISPR_DEEPDIVE found confidence useful for near-miss check |
| Bubble that restarts itself if Android kills it | Wispr | Floating mic stays alive | Yes | Test | Only if testers report the floating mic vanishing |
| Two Hinglish outputs: all-Roman, or English-Latin + Hindi-Devanagari | Saaras | Choice for Hindi-script readers | Yes | Skip for now | No tester has asked; doubles test work |
| Per-stage local/cloud switch | Superwhisper | Clear privacy control | Partly | Skip (mostly have it) | Speech is always local in indite; AI is already opt-in via the user's AI account |
| Hold-to-delete that speeds up to whole words | Wispr | Fast clean-up on phone | Yes | Skip | Normal keyboard already does this |
| Voice "reformat this" mode (Hey Kivi) | Kivi | Polished text | Needs AI | Skip (have it) | indite's AI actions on notes already cover it |
| Price anchor: rivals sit at ₹0 (Kivi alpha, Apple, Samsung) to ₹320 (Wispr) | Wispr, Kivi | Pricing decision input | — | Note only | Not a feature; for the pricing discussion |

---

### What the founder still needs to test by hand

1. **Samsung Galaxy (One UI 8):** Samsung Keyboard → Hindi → mic. Script? Flight mode? Words wrong on the 15 sentences.
2. **OnePlus (current OxygenOS):** which keyboard and voice engine ships by default; same test.
3. **Kivi on the Mac:** open heykivi.ai (it would not load during this research). Does it write Roman Hinglish? Does it work with Wi-Fi off? Read the privacy policy.
4. **Wispr Flow:** pick "Hinglish," run the script, count wrong words. Check the ₹320 price in the app from India.
5. **Apple Dictation:** Hindi, with a mixed Hindi + English sentence. Confirm it fails with Wi-Fi off.
6. **Superwhisper:** local Whisper with Hindi; then a custom mode that asks the AI to write Roman Hinglish. Count wrong words.

**⚠ Remember:** only use the founder's own test script on cloud tools (Kivi, Wispr, Apple Hindi). Never upload tester
recordings. Never put recordings in git.

---

### Sources (all read 18 Oct 2026)

1. Sarvam, "Announcing Sarvam Edge", https://www.sarvam.ai/blogs/sarvam-edge/ (14 Feb 2026; vendor blog)
2. Sarvam, Edge product page, https://www.sarvam.ai/products/edge (undated, © 2026)
3. Sarvam docs, Saaras models, https://docs.sarvam.ai/api/getting-started/models/saaras.md (undated; v4 current); output modes: https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/how-to/select-output-mode.md
4. Sarvam docs, pricing, https://docs.sarvam.ai/api/getting-started/pricing (undated); Sarvam pricing page https://www.sarvam.ai/api-pricing (undated; credits conflict)
5. NewsBytes, "Sarvam AI launches Kivi voice productivity app for Mac", https://www.newsbytesapp.com/news/science/sarvam-ai-launches-kivi-voice-productivity-app-for-mac/tldr (2026; page blocked, read via search snippet)
6. YouTube, "Introducing Kivi for Mac, Powered by Saaras V4", https://www.youtube.com/watch?v=2G2JZWcj-XY (date not shown)
7. Kivi landing page and privacy policy, https://heykivi.ai/ and https://heykivi.ai/privacy.html (policy effective 26 Jul 2026; blocked here, read via search snippets)
8. Kivi-Dash README (third-party), https://github.com/Shridhar600/Kivi-Dash (undated)
9. YourStory, "HP and Sarvam AI bring voice-first AI to PCs in India", https://yourstory.com/ai-story/hp-and-sarvam-ai-bring-voice-first-ai-to-pcs-in-india (18 Aug 2026)
10. Samsung Members forum threads: https://r2.community.samsung.com/t5/Tablets/Offline-language-pack/td-p/20549336 (Sep 2025), https://r2.community.samsung.com/t5/Galaxy-Note/Voice-input-support-not-available-in-samsung-keyboard-for-hindi/td-p/199549 (2019), https://r2.community.samsung.com/t5/Galaxy-A/Voice-input-languages-no-indian-Language-Hindi-Marathi-Telgu/td-p/8227365 (2021) (read via search snippets; pages blocked)
11. AI Voice Lab, "Samsung Speech to Text", https://aivoicelab.com/blog/how-to-use-samsung-speech-to-text-voice-typing (undated; vendor blog)
12. UC Strategies, "India's best offline AI only works on phones 80% of Indians can't afford", https://ucstrategies.com/news/indias-best-offline-ai-only-works-on-phones-80-of-indians-cant-afford/ (18 Feb 2026)
12a. Samsung, "Galaxy AI languages & usage guide", https://www.samsung.com/levant/support/mobile-devices/galaxy-ai-languages-usage-guide/ (lists "as of March 2026"; India page returned 404)
13. TechBone, OnePlus "Google voice typing", https://www.techbone.net/oneplus/smartphone/google-voice-typing (OxygenOS 10 era)
14. Superwhisper docs, security / account & data, https://superwhisper.com/docs/security (undated)
15. Superwhisper docs, plans, https://superwhisper.com/docs/billing/plans.md (undated)
16. Wispr Flow pricing page, https://wisprflow.ai/pricing (site "Last Published" 17 Oct 2026)
17. Wispr Flow help, "Use Flow with multiple languages", https://docs.wisprflow.ai/articles/3191899797-use-flow-with-multiple-languages (updated ~17 Oct 2026, relative date)
18. Wispr Flow "What's new" changelog, https://wisprflow.ai/whats-new (entries to 9 Oct 2026; Canto 17 Sep; Android 23 Feb)
19. AI Chat Daily, "Wispr Flow's India growth hits 100%...", https://www.aichatdaily.com/ai-business/wispr-flow-india-voice-ai-expansion (10 May 2026; summarises TechCrunch https://techcrunch.com/2026/05/09/voice-ai-in-india-is-hard-wispr-flow-is-betting-on-it-anyway/, which was blocked here)
20. Wispr enterprise privacy page https://wisprflow.ai/post/enterprise-privacy-and-security-overview and help "Understanding Privacy Mode and Cloud Sync" https://docs.wisprflow.ai/articles/4709791908-understanding-privacy-mode-and-cloud-sync (read via search snippets; fetch failed); "no offline mode" from third-party reviews in the same search (laxis.com, yaps.ai)
21. Apple, Mac User Guide, "Use Dictation", https://support.apple.com/guide/mac-help/use-dictation-mh40584/mac (macOS 27, © 2026)
22. Apple, macOS Feature Availability, https://www.apple.com/macos/feature-availability/ (current page)
23. Apple, "Siri, Dictation & Privacy", https://www.apple.com/legal/privacy/data/en/ask-siri-dictation/ and Apple Newsroom https://www.apple.com/newsroom/2025/01/our-longstanding-privacy-commitment-with-siri/ (Jan 2025) (read via search snippets; fetch failed)
24. tl;dv, "SuperWhisper review", https://tldv.io/blog/superwhisper-review/ (undated; competitor blog)
25. Superwhisper docs, language detection, https://superwhisper.com/docs/common-issues/language-detection (undated)
26. Reworked, "Wispr hits $2B valuation, launches Canto voice model", https://www.reworked.co/ai-platforms/wispr-hits-2b-valuation-launches-canto-voice-model/ (Aug 2026)
27. Voibe, "MacWhisper pricing 2026", https://www.getvoibe.com/resources/macwhisper-pricing/ (2026; competitor blog)
28. Granola, "Granola pricing", https://granola.ai/blog/granola-pricing-plans-features-roi and Anavem https://www.anavem.com/tools/granola (undated)
29. Spokenly, "Aqua Voice pricing", https://spokenly.app/blog/aqua-voice-pricing (undated; competitor blog)

---

## Sources (read 17 Oct 2026)

1. Google, "Use advanced voice typing features", support.google.com/gboard/answer/11197787 (undated, current page)
2. 9to5Google on Pixel "faster voice typing", ~85 MB all-neural on-device model, 9to5google.com/?p=266342 (2019)
3. JR Raphael, Computerworld, "Android voice typing", computerworld.com/article/4026831 (23 Jul 2025)
4. Google blog, "Gboard for Android gets new languages and tools" (Hinglish keyboard option), blog.google; Google India blog, "Type less, talk more in eight Indian languages" (Aug 2017)
5. Android Authority, "Gboard voice typing", androidauthority.com/gboard-voice-typing-3222912 (16 Jun 2023)
6. HackerNoon, "Testing Android's on-device speech recognition with Hindi-English code switching" (2 Oct 2026)
7. scriptio.in, "Tamil voice typing" (2026; vendor blog, Tamil not Hindi, an analogy only)
8. Google, "Type with your voice" (Docs), support.google.com/docs/answer/4492226 (current page)
9. Brave community forum and Mozilla wiki on the Web Speech API sending audio to Google (dates vary)
