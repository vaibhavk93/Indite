# indite: detailed roadmap and Wispr Flow comparison (15 Oct 2026)

Researched and critic-reviewed. The one roadmap stays `ROADMAP.md`; this is the detail behind its new items. Built on `ROADMAP.md`, `docs/MAC_PLAN.md` (§0, §3, §6) and
`docs/FOUNDER_REQUESTS.md`, plus fresh research on Wispr Flow (sources and dates at the end).

**The short answer:** indite's next big gain is not a new Wispr feature. It is **fewer wrong words, measured on real
speech**, and getting the app into a second person's hands. The founder's "AI review" idea fits that goal well, *if*
it only suggests and never changes text by itself. Regional languages stay later: each one needs a new model.

**⚠ Remember:** every accuracy number in the repo comes from synthetic clips. The 53 real Mac dictations and the
real phone notes have never been scored, and the 53 can't be: their audio wasn't saved. Until they are, any claim that a feature "improves accuracy" is unproven.

---

## A. Simple roadmap

User types: **D** = daily dictation user · **M** = meeting user · **S** = student · **R** = regional-language user ·
**L** = low-end phone user.

### Now (this week and next)

| Feature | Build? | Why | Impact on users | Notes / risks |
|---|---|---|---|---|
| Back up the Android signing key | No (founder task, 5 min) | One copy only. If lost, no tester can ever update | All | Highest risk per minute of effort |
| Record ~50 fresh real dictations with audio saving on, then score them (plus ~20 real phone notes) | Yes | Every other accuracy decision depends on it; also the test set for AI review | D | ~1 day. The old 53 can't be scored: audio saving is off by default, only 2 audio files exist. Needs a hand-typed "what I really said" per clip |
| Test a real call with the meeting recorder | No (founder task) | Screen & System Audio Recording is granted (15 Oct night); one real call left (B22) | M | — |
| Founder's hand check of build 29 + Mac 🧪 items | No (founder task) | ~25 built features never used by a human | All | Keep. Unverified features outnumber gaps |
| ₹15k phone test | No (founder task) | Biggest unknown; tester plan sits behind it | L | Keep at top. If dictation > ~15 s, speed work comes first |
| Mac W1–W3: snippet example row, "Teach this word" in one click, "fixes made" on Insights | Improve existing | Cheapest proven accuracy path is word fixes | D | ~2 h. Already critic-reviewed (MAC_PLAN §6) |
| **AI review of a dictation, step 1: offline "near-miss" check** | Yes (gated) | Catches "in diet" when "indite" is in your Dictionary, with no AI and no internet | D, M, S | Works on Android public build too. Only suggests. Gate: ≤1 false alarm per 100 words on the real set |

### Next (after the checks above pass)

| Feature | Build? | Why | Impact on users | Notes / risks |
|---|---|---|---|---|
| **AI review, step 2: "Review with AI" on a note (Mac + Android personal)** | Yes | Finds context errors a word list can't (names, numbers, mixed words) | D, M, S | Gate: on the scored real set, ≥70% of suggestions are right. Text leaves the device |
| Accepted review fix → "Always fix?" → Dictionary | Improve existing | Android `Settings.addFix()` and Mac `store.add_fix` already exist; just wire them | D | Ask per fix; never auto-add |
| Review insights: most-fixed words, fixes per 100 words, fillers, wpm | Improve existing | Mac Insights page exists; wpm is there. The fix log behind the other numbers is new work | D, S | "Accuracy trend" is only a proxy (see C3). Wanting it is unproven. Android Insights: later |
| Mac W5: offline filler strip (umm, matlab, basically), raw kept | Yes (gated) | Free "light clean-up" with no AI | D | Gate: 30 real dictations, 0 real words removed |
| Mac W4: Dictionary primes the engine (`initial_prompt`) | Yes (gated) | Only item that makes names *heard* right | D, R | Gate: 0 dictionary words inserted where not spoken. Could invent a colleague's name |
| Indian formatting: ₹, lakh/crore, dates ("kal" kept as said) | Improve existing | Mac turns numbers into digits; Android doesn't. Lakh/crore is new work | D, R | Unproven: the Mac digits pass changed 0 of 53 real dictations. Port to Android only after real-speech evidence |
| Signed + notarised Mac build ($99/yr) | Yes (founder decides) | No second person can install it today | D, M | Every rebuild also resets permissions |
| Tester build (try-it, model download on first open, Play internal testing) | Keep | Already planned, critic-reviewed | All, L | Behind the ₹15k phone |
| Look-and-feel list (10 items) | Keep, lower priority | Polish; testers decide if it matters | All | Move after tester build, not before |
| Choose when transcripts are deleted | Keep | Founder request; privacy | All | Small |

### Later (needs a trigger first)

| Feature | Build? | Why | Impact on users | Notes / risks |
|---|---|---|---|---|
| Regional name and place packs (offline word lists) | Yes, small (gated) | Names of Indian cities, common surnames, local brands | R | A pack has no "heard" side, so it only works through the step-1 near-miss check. Thousands of names = more false alarms. Gate on step 1's false-alarm rate |
| Whisper test (10 whispered clips) | Optional | Wispr claims it; nobody asked us | D | Needs fresh recordings. Unproven either way |
| Native-script output (Devanagari) as a switch | Improve existing | Already in "Later"; Mac AI can already translate to Hindi (Devanagari) | R | Offline needs a transliteration step; unproven quality |
| Other languages mixed with English (Marathi, Bengali, Tamil...) | Yes, one at a time | Real regional demand, but each needs its own model | R | Trigger: tester sign-ups. Sarvam Edge has 10 languages on-device already |
| Indian English accent tuning | Keep | Listed in ROADMAP "Later" | D, R | Unproven gain |
| Android Insights page | Yes, small | Mac has it; phone users are the main market | D, L | Only if testers open Mac Insights often |
| On-phone small AI for review (no internet) | Research | Would make AI review work in the public build | L, R | RAM on a cheap phone; Gemma test already listed |
| Topics in Insights (what you talk about most) | Yes, AI only | Fun, not needed | D, S | Needs AI on all notes: privacy + quota cost |
| Windows | Keep | Founder decision | D | Needs a Windows PC |
| iPhone | Keep parked | Trigger: 5+ tester asks | — | iOS blocks bubble and mic in keyboards |
| Web app speakers | Drop to "not doing" | The Mac app now has speakers natively | — | The web app is no longer the Mac path |
| Subtitle line-length setting | Drop | Nobody asked again; check the 56-min SRT if they do | — | — |

### Not doing (kept or newly added)

| Feature | Build? | Why |
|---|---|---|
| AI that auto-applies corrections | No | AI with only text can invent fixes. Every change must be the user's tap |
| AI clean-up on every dictation (Wispr Auto Cleanup) | No | 4–7× slower, spends the user's quota. Kept as after-the-fact "Improve" |
| Per-app styles, command mode, reading other apps' text | No | Already dropped in MAC_PLAN §6 (misfires, keylogger look) |
| Training the model on the user's voice | No | No trainer, no RAM on a phone |
| Sending corrections to a server to improve for everyone | No | Breaks privacy and the public-repo rules |
| Team dictionary, cloud sync, accounts | No | Breaks offline + no-account |

---

## B. indite vs Wispr Flow

Wispr facts checked on wisprflow.ai pages, Oct 2026. ✅ has · 🟡 partial · ❌ no.

| Feature | indite | Wispr Flow | AI-like thing to build (or not), and why |
|---|---|---|---|
| Works offline | ✅ | ❌ cloud only | Our edge. Keep |
| Hinglish | ✅ Roman, one language | ✅ since May 2026 (India launch, TechCrunch 9 May) | Our edge is now smaller. Win on accuracy + offline, not "has Hinglish" |
| Android | ✅ keyboard + bubble | ✅ bubble only (Feb 2026), Android 13+ | — |
| iPhone / Windows | ❌ / ❌ | ✅ / ✅ | Parked with triggers |
| Other languages | ❌ | ✅ 100+, language picker | Later; each costs a model |
| Personal Dictionary | ✅ Mac + Android word fixes | ✅ starred words, usage ranking | — |
| Auto-learn words from your corrections | 🟡 Android after 2 edits; Mac by pencil only | ✅ auto-adds when you fix a spelling | **Build:** review → accept → "Always fix?" |
| Snippets | 🟡 word fixes do it, hidden | ✅ rich text | W1: show the example row |
| Uses surrounding text to spell names | ❌ by design | ✅ "context awareness" | **Build the safe version:** AI review on the note, user accepts each fix |
| Backtrack ("scratch that") | 🟡 Improve does it, after | ✅ live | Not live. Unproven for Hinglish |
| Auto clean-up / filler removal | 🟡 AI "Clean it up", after | ✅ 4 levels, undo; over-aggressive fixes in Jul 2026 | W5 offline filler strip, raw kept |
| Styles / tone per app | 🟡 13 rewrite styles (tone, where it goes, purpose), by hand | ✅ English, desktop only | No per-app. Keep by hand |
| Command Mode / Transforms | 🟡 "Ask anything" on a note | ✅ voice edits on selected text (paid) | No: misheard command, no undo |
| Whisper (quiet speech) | ❓ never tested | ✅ claimed | Optional test later (10 whispered clips). Unproven either way |
| Meeting notes | ✅ Mac meetings, Android recording, AI notes | ✅ Notetaker (Mac Aug, Windows Sep 2026) | Ours is offline. Fix the Mac permission first |
| Speaker names | ✅ both | ✅ per news coverage (unverified on wisprflow.ai) | — |
| Insights / stats | 🟡 Mac only | ✅ | Add review numbers (C3) |
| Notes reachable from Claude/ChatGPT (MCP) | ❌ | ✅ Notetaker | Later, Mac only; unasked |
| Password / banking guard | ✅ password boxes | ✅ banking-app pause (Android) | — |
| Speech model | 🟡 open third-party Hinglish model (Oriserve), runs locally | ✅ own model "Canto" (Sep 2026), cloud | Theirs is in-house and cloud; ours is borrowed but private |
| Team dictionary, admin, SSO | ❌ | ✅ Pro / Growth | No: different company |
| Price | Free | Free: 2,000 words/week desktop, 1,000 mobile. Pro ₹400/mo, or ₹320/mo yearly; students 50% off; UPI | Free + offline is the pitch to students |

---

## C. Detail for each "Yes" item

### C1. AI review of a dictation (the founder's idea 1)

**What it does.** You open a note and tap **Review**. indite lists likely mistakes: *"heard: in diet → maybe:
indite (your Dictionary)"*. Each has **Fix** / **Ignore** and a ▶ to hear that bit. Fixing changes the note (the
original is kept) and asks **"Always fix in diet → indite?"**. Yes adds it to word fixes, so next time it is fixed
by itself.

```
                   REVIEW A NOTE
                        |
        +---------------+----------------+
        v                                v
 #=====================#        +---------------------+
 # * Step 1: offline   #        | Step 2: with AI     |
 #   (no internet)     #        |  (user's own AI)    |
 #=========+===========#        +----------+----------+
           |                               |
  + works on every build           + catches names, numbers, mixed words
  + free, instant, private         + uses the meaning of the sentence
  - only finds near-misses of      - text leaves the device
    Dictionary words + flags       - can invent fixes; seconds per note
  - can't spot new names           - Mac + Android personal build only
  * = recommended first     # box = build first
```

| | Step 1: offline near-miss | Step 2: AI review |
|---|---|---|
| How | Join 1–3 note words, compare with Dictionary targets by spelling distance ("in diet" → "indiet" is 2 letters from "indite"). Only targets ≥5 letters; skip common words. Plus existing flags (Android only: loops, "nan", stock phrases; Mac deletes "nan" silently) | Prompt with the note + Dictionary; reply as a list `heard | suggest | why | sure?`. A per-item version of the Mac "Improve" / "Clean it up" actions, which already fix context but all at once |
| Where | Mac + Android (both builds) | Mac (Claude login or API key); Android personal (OpenRouter / Mac route) |
| Effort | S–M (~1 day, unproven: Roman Hinglish spelling varies a lot, tuning may take longer) | M (~2–3 days incl. the test) |
| Privacy cost | None | The note's text goes to the AI the user picked. Audio never leaves |
| Depends on | Dictionary existing (done) | Scored real set (Now); AI route (done on Mac) |

**Guards against invented fixes (must ship with step 2):**
1. Drop any suggestion whose "heard" text isn't in the note word for word.
2. Never apply anything without a tap. No "Fix all" in v1.
3. Max ~10 suggestions per note; skip it if the AI is unsure.
4. Show ▶ for that bit of audio when audio is kept. **On the Mac, audio saving is off by default, so most notes
   have none.** Android notes keep audio. Without audio the user can only judge by memory.
5. The original text is always kept.

**⚠ Remember:** the AI reads only text, not audio. It *guesses* what was meant from the sentence. It can catch
"in diet" in a sentence about the app. It can't tell "Rahul" from "Rohit" if both fit. Treat it as a spell-check for
meaning, not a second transcriber.

**How we'd know it worked.** On the scored real set: % of suggestions that are right (target ≥70%, else don't ship
step 2), and % of real errors it catches. In use: accept rate per suggestion, and whether "fixes per 100 words"
falls over weeks. All unproven today.

### C2. Accepted fixes feed the Dictionary
Wire the review's **Fix** button to Android `Settings.addFix()` and Mac `store.add_fix`. (Not `Settings.learn()`: it
only suggests after the same edit twice and needs an exact match.) Ask "Always fix?" every time; skip very common words ("the", "hai"), which could break other sentences. Effort **S**. Measure: how many
saved fixes trigger again later (Mac W3 count).

### C3. Insights from reviews (idea 2)

| Number | Offline? | Honest? |
|---|---|---|
| Most-fixed words (top 10) | ✅ from a fix log (new work: no log exists yet) | Yes |
| Fixes per 100 words, by week | ✅ | **Proxy only.** Falls if accuracy improves *or* if you stop fixing |
| Filler words per dictation (umm, matlab, basically) | ✅ word list | Yes, roughly |
| Speaking speed (wpm) | ✅ already on Mac | Yes |
| Topics you talk about | ❌ needs AI on every note | Later; costs quota and privacy |
| True accuracy % | ❌ needs what you *really* said | Only from the scored test set, not daily use |

Effort **S** on Mac (page exists), **M** on Android (no page yet). Measure: does the founder open it twice a week
after the first week? Unproven that users care.

### C4. Offline filler strip (Mac W5)
Fixed list removed in `tidy()`; raw text stored beside it; switch in Settings, off by default. Effort **S**. Gate:
30 real dictations, ≥1 filler removed on ≥10, 0 real words removed. "matlab" is also a real word ("what it means"),
so it may need to stay out of the list.

### C5. Dictionary primes the engine (Mac W4)
Feed Dictionary words to whisper's `initial_prompt`. Effort **S** to build, **M** to test. Gate: words-wrong falls
on the 360-clip bench **and** 0 dictionary words appear in clips that don't contain them. Highest gain, highest risk.

### C6. Indian formatting
Offline rules: "do sau rupaye" → "₹200", "paanch lakh" → "5 lakh" (not "500000"), dates as said. Lakh/crore and ₹
are new work in `mac/digits.py` (it has none today). Effort **S–M**. Measure: on the scored set, number errors before
vs after. **Unproven:** the digits pass changed 0 of the 53 real dictations. Port to Android only once real speech
shows number errors. ("ek baar" is already safe: "ek" only converts next to a counting word.)

### C7. Regional personalisation (idea 3)

| Piece | Offline? | Effort | Honest status |
|---|---|---|---|
| Name/place packs (city names, surnames, local brands) | ✅ | S | Work only through the step-1 near-miss check; more names = more false alarms. Gate on step 1's rate. Risky if fed to the engine (W4) |
| Numbers/dates in Indian style | ✅ | S–M | See C6 |
| Output script switch: Roman / Devanagari | ✅ via transliteration | M | Quality for code-mixed words unproven |
| WhatsApp-first: share-in exists; "WhatsApp Hinglish" rewrite exists; date titles for WhatsApp notes planned | ✅ | S | Mostly built |
| Low-end phone: smaller install, speed on ₹15k phone | ✅ | M–L | The ₹15k test decides. 681 MB install is a real blocker |
| Marathi / Bengali / Tamil + English | ✅ but new model each | L each | Needs a Roman-output model per language; may not exist. Unproven demand |
| Regional accents of Hinglish | ✅ (model tuning) | L | Needs recorded data; unproven |

Measure: tester sign-up answers ("which language do you mix with English?"); only start a language when 5+ ask.

### C8. Critic review of this draft (fresh, independent agent)

| Main objection | What changed |
|---|---|
| The 53 real dictations can't be scored: audio saving is off by default, only 2 audio files | "Now" item is now: record ~50 fresh with audio on, then score (~1 day) |
| Wrong function: `Settings.learn()` is a twice-seen counter | C2 now uses `Settings.addFix()` / `store.add_fix` |
| Near-miss check: feasible, but noisy on Roman Hinglish | Added ≥5-letter rule, common-word skip, false-alarm gate; effort marked unproven |
| ▶ audio guard mostly missing on Mac | Said so in guard 4 |
| Digits pass changed 0/53 real dictations; no lakh/crore | C6 marked unproven, lakh/crore = new work |
| Name packs have no "heard" side | Routed through step 1, gated |
| Whisper test unasked | Moved to Later, optional |
| Wispr table overreach ("own model", unsourced claims, student price) | Fixed or marked unverified |

**Still unresolved:** whether step 1's false-alarm rate can get under 1 per 100 words. Nobody knows until it runs on
real notes.

---

## D. Things the founder should know

**Risks**
- **AI review can invent fixes.** It reads text only. A confident wrong "fix" is worse than the original mistake.
  The guards in C1 are not optional.
- **Feeding names to the engine (W4) can put names into notes where nobody said them.** Gate before shipping.
- **⚠ The real-speech test set must be recorded fresh** (Mac audio saving is off by default). It gates AI review,
  formatting and every accuracy claim.
- **Wispr now does Hinglish, Android, and student pricing (₹160/mo on the yearly plan, 50% off).** "Has Hinglish" is no longer our
  edge. Offline, private, free and accurate-on-real-speech are.
- **Sarvam Edge** (on-device, 10 Indian languages, with phone makers) is the bigger threat to the offline edge.
- **The ₹15k phone and the 681 MB install** decide whether low-end users can use indite at all.

**Costs**
- AI review uses the user's own Claude quota or API key. A long meeting note may be a few thousand words per review.
- The $99/yr Apple fee is needed before anyone else can install the Mac app cleanly.
- Each new regional language = a new model (hundreds of MB), its own test set, its own spelling list.

**Legal / privacy (not legal advice)**
- AI review sends note text out of the device. Ask once, clearly, per AI route (Mac already asks). Under India's
  DPDP rules, other people's words in a meeting note are their personal data too.
- The public Android build has no internet. AI review step 2 can't exist there, by design. Only step 1 can.
- Free OpenRouter models may train on what is sent; warn before review on personal builds.
- The public repo still has **no LICENSE** file. Name packs must come from openly licensed lists.

**What is unproven**
- That AI review's suggestions are right often enough (no test yet).
- That users want Insights beyond a first look.
- That fixes-per-100-words tracks real accuracy.
- That any regional language model exists in Roman output at usable quality.
- That whisper mode matters to anyone.
- That real-speech accuracy is near the synthetic 13–14% (it could be much worse).

---

### Sources (checked 15 Oct 2026)
- wisprflow.ai/pricing — tiers, word limits (Free 2,000/week desktop, 1,000 mobile; Pro $12–15; Growth; Enterprise)
- wisprflow.ai/india — Hinglish, ₹400 / ₹320 per month, 50% student discount, UPI, Android 13+
- wisprflow.ai/features — Styles (English, desktop), Whisper, Snippets, Dictionary auto-add, Backtrack, 100+ languages
- wisprflow.ai/whats-new — Android dictionary + context (31 Mar 2026), Insights + 4-level cleanup (24 Apr), Transforms
  (1 May), cleanup over-aggressiveness fix (9 Jul), Notetaker Mac (5 Aug), Windows (15 Sep), Canto model (17 Sep)
- roadmap.wisprflow.ai changelog — Android launch, 23 Feb 2026
- TechCrunch, 9 May 2026 — Wispr India launch with Hinglish; TechCrunch, 5 Aug 2026 — Notetaker terms change
- docs.wisprflow.ai — Command Mode article exists (details from secondary sources; treat as weaker)
