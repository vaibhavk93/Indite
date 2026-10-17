# Competitors: Google voice typing, and a plan for the rest

Written 17 Oct 2026. Desk research only: **nothing here was tested by hand, and no critic has reviewed any idea yet.**
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
