# indite plan: features, decisions, products

Last updated: 2026-10-09. Every "survived" item passed an independent critic review or is the founder's own decision.
Short-term roadmap: [ROADMAP.md](ROADMAP.md). Pages: [plan](https://claude.ai/artifact/BPuiRa3MBzHaWkirWVCKZX) · [vision](https://claude.ai/artifact/LJZmUuUP7xP5JXtRrrtkGK) (private links).

**Goal (by 2036):** anyone in India can speak the way they really talk, mixing Hindi and English, and get correct Roman-script text instantly, privately, offline, on a ₹15,000 phone.
Measured by: #1 on our own public Roman-Hinglish leaderboard (offline tools), works on a named ₹15k phone at ≤ 3 s per sentence, paying users (bar set after interviews).

**Next month, one thing:** Android app that turns a shared WhatsApp voice note into Roman Hinglish text, given to 10–20 real users, with interviews alongside. Dictation joins in month 2 if a 4 s sentence takes ≤ 8 s on the phone.

---

## 1. Features already built (web / Mac app)

| Feature | Status |
|---|---|
| Upload any audio/video, background transcription, live progress, cancel | Built |
| Editor: find & replace, undo, shortcuts, unsaved edits kept | Built |
| Flags on made-up text: no speech, loops, stock phrases, junk words | Built |
| Export: SRT, VTT, timestamped, paragraphs | Built |
| Notes via the user's own Claude; "Copy for Claude / ChatGPT" | Built |
| Local engine default; Sarvam optional (paid, cloud) | Built |
| 3-year auto-delete with the date shown | Built |
| Restart resumes unfinished jobs | Built, **but starts each job from scratch** (see section 5) |

## 2. Features planned for the phone

| Feature | When | Condition |
|---|---|---|
| Share a WhatsApp voice note → Roman Hinglish text | v1, next month | — |
| Record first: audio saved as a new 30 s file every 30 s (crash loses ≤ 30 s) | v1 | — |
| Background queue: resumes after crash/restart; pauses > 40 °C or low battery; optional "only while charging" | v1 | — |
| Transcript saved after every piece; resume from last saved piece (section 5) | v1 | — |
| "Saved ✓" at once, piece-by-piece text, time left, notification when done | v1 | — |
| Edit; copy one part or all (copy-all leaves out "Check" labels) | v1 | — |
| Likely-wrong flags (same rules as web) + tap a flag to replay that piece | v1 | — |
| Phone check on first open: required chip features (dotprod, fp16) else "not supported, use the web app" (prevents a crash on old phones); warn under 6 GB RAM | v1 | — |
| Wait estimate from the real job: time the first piece, then "about N min left"; log speed, temperature and phone model per job (local) | v1 | — |
| Per-phone tiers (model choice, several CPU builds, first-open benchmark) | Later | Only when budget-phone logs show a choice worth ≥ 1.5x |
| Borrow one ~₹15k budget phone (Dimensity / Snapdragon 6) and test before testers | Before testers | Plan gate is a ₹15k phone; never tested |
| Model downloaded after install (Play asset pack), "Wi-Fi only, 550 MB" prompt | v1 | — |
| Privacy policy; crash reports opt-in only | v1 | India's data law (DPDP) |
| Dictation in the app: text after each pause, 15 s audio window | Month 2 | 4 s sentence ≤ 8 s on phone |
| Long recordings on phone (meetings, classes) | Phase 2 | v1 has users |
| Who-said-what (speaker labels) | Phase 2 | Speaker tests pass (blocked: Hugging Face access) |
| Voice input screen any keyboard can switch to (dictate in any app) | Phase 2 | Dictation works |
| Clean-up rules: numbers, ₹, lakh, one spelling per word, punctuation | Phase 2 | — |
| Pro one-time unlock (test ₹299 vs ₹999) | Phase 2 | Price unproven |
| Public Hinglish test set + leaderboard | Phase 3 | — |
| Phone AI chip (Snapdragon flagships) | Phase 3 | Cheaper fixes not enough |
| In-app model updates with rollback | Phase 3 | — |

Web roadmap "Next" items still stand: custom vocabulary (remember corrections), choose when transcripts are deleted, Indian number formatting, optional "fix unclear bits with Sarvam", translate to English / clean version, subtitle line length, Windows support.

## 3. What survived and what didn't

| Idea | Verdict | Why |
|---|---|---|
| Record everything first, transcribe at own pace (founder) | Survived | Never loses audio; base for voice notes and long recordings. Does not make dictation faster |
| Flag likely-wrong parts (founder) | Survived | Rule-based flags already work on web |
| Copy and edit (founder) | Survived | Proven on web |
| Live dictation, Wispr-like (founder) | Gated | ~45 s per 4 s sentence today; joins at ≤ 8 s |
| Use the user's best device for free (founder) | Survived, small | Silent speed check picks the model |
| Shorter audio window, 15 s | Survived | Mac test, 178 short clips: 0 loops, 7.3% of words differ from full window |
| Shorter audio window, 7.7 s | Cut | 3 loops, 14.3% of words differ |
| Build fix: fast ARM instructions for the maths code | Done in v2 | Maths code was built with no -march; gain unmeasured |
| Own small model | Later | Only if dictation is still > ~5 s after cheaper fixes (build fix → 15 s window → q4 → phone AI chip) |
| Live translation, e.g. Chinese ↔ Hindi (founder) | Later, stop rule | Google, Samsung, Bhashini already free. Start only when 3 real people ask; then a 1-day text test; drop if not clearly better than Google |
| More Indian languages | 2028+ | Each needs a new model + test set; Sarvam's strongest ground |
| Laptop runs the model in the browser (WebGPU) | Cut | No browser-ready version of our model; laptop users have the web app |
| Rough draft text while speaking (two models) | Cut | Draft models write Devanagari or are untested; Wispr doesn't do it |
| Shade words the model was unsure of | Cut | Confidence doesn't match real mistakes |
| Full keyboard (FlorisBoard) | Cut | Endless work; voice input screen does the job |
| Floating bubble over other apps (Wispr's way) | Cut | Play Store risk (accessibility permission) |
| Own call recorder | Cut | Banned on Play since 2022; import recordings instead |
| Laptop via Tailscale | Cut | Too technical for users |
| Cloud fallback / AI on our keys | Cut | Breaks zero-cost and privacy rules |
| "100M users" goal | Replaced | No route to users; goal now accuracy, phone floor, payers |
| Longer pieces, 25 → 28 s | Not yet | 25 s won the loop test (73 → 4); needs re-test |

## 4. Products that could come out of this (none proven)

| Product | What it is | Stage | Review |
|---|---|---|---|
| indite Voice Notes (Android) | Share a WhatsApp voice note, get Roman text | v1, next month | Critic-reviewed |
| indite Dictation | Speak in the app, text after each pause | Month 2, gated | Critic-reviewed |
| indite Web / Mac | Long files, editor, export | Exists | — |
| indite Notes | Meetings/classes on phone, who-said-what, summary via user's own AI | Phase 2 | Critic-reviewed |
| Voice input for any app | Mic screen any keyboard can switch to | Phase 2 | Critic-reviewed |
| Hinglish leaderboard | Public test set scoring Google, Sarvam, Wispr and us | Phase 3 | Critic-reviewed |
| Own small Hinglish model | Faster model trained to copy ours | Only if needed | Critic-reviewed |
| Audio memory | Search all recordings: "what did the doctor say?" | Later | Critic-reviewed |
| Tap-to-talk translation | Our text → Google's free offline translator → phone voice | Later, stop rule | Critic-reviewed |
| Other code-mixes | Indian English → Marathi or Bengali → Tamil | 2028+ | Critic-reviewed |
| iPhone app | Main app listens (iPhone keyboards can't use the mic) | 2028+ | Critic-reviewed |
| Windows app | Same as Mac | Next on roadmap | Founder decision |
| Engine sold to other apps | Offline Hinglish engine for health/fintech apps | Long shot (~10%, a guess) | Critic-reviewed |
| Offline live captions | Live text for deaf / hard-of-hearing people (~63M, WHO-based estimate) | Idea only | Researched, **not** critic-reviewed |

Ruled out as products: dubbing, language learning, call-centre checking, voice bookkeeping, creator-subtitles focus, government/UPI voice (Bhashini is free).

## 5. Never start from scratch: crash recovery

Founder request: if transcription is interrupted (crash, kill, corrupt file, reboot), resume from the work already done. Critic-reviewed; its changes are in.

**The rule:** save the audio first, save each finished piece of text the moment it's done, and save the list of cuts. A restart redoes at most the piece that was in progress.

### Build first (smallest version)

| # | Where | What | Why |
|---|---|---|---|
| 1 | Web | Keep whisper's per-piece output in `data/<id>/pieces/` (not a temp folder) + save the cut list `pieces.json`. On restart, skip pieces that already have readable output; treat a half-written output as "not done". Delete `pieces/` when the job finishes (~107 MB of WAVs for 56 min). | Today a restart re-transcribes the whole file from scratch |
| 2 | Web | Re-runs of bad pieces write to a different file name than the first pass | A restart during re-runs would otherwise mix first and second results |
| 3 | Web | Build `result.json` from pieces only while the job is not "done" | `result.json` also holds the user's edits; never overwrite them |
| 4 | Phone | Record raw PCM (no header) in 30 s files; add the WAV header only on export. Flush each file to disk when it closes | No header to repair after a crash; length = file size ÷ 2 |
| 5 | Phone | `transcript.jsonl`: one line per finished piece, positions as whole sample numbers. Progress = last line's end. Resume by cutting from that sample onward; never re-match old cuts | Pause detection can cut differently on a re-run; matching would attach old text to new audio silently |
| 6 | Phone | Before each piece, write "attempt N on piece X". After 2 attempts with no result, write `[unclear]` and move on | A crash inside the model kills the app before any error counter runs; without this one bad piece crash-loops forever |
| 7 | Phone | Check free space whenever a new 30 s file starts: warn < 500 MB, stop recording cleanly < 100 MB | Never lose a recording to a full phone |
| 8 | Phone | Copy shared audio (WhatsApp voice notes) into app storage before queuing | Shared links can expire |
| 9 | Phone | If the mic is taken (a call, another app), write a gap marker | Keeps text and audio times aligned |
| 10 | Phone | Backup off; audio and transcripts excluded from Google backup and phone-to-phone transfer | "Audio stays on the phone" must stay true. **Done in v2.** |
| 11 | Both | Kill test: kill the app 10 times mid-recording and mid-transcription; plus a piece that crashes the model on purpose | Proves: ≤ 30 s audio lost, no piece done twice, no crash loop |

Already planned and kept: truncated last line ignored; heat or low battery = pause, not fail; resume after the app is killed.
Later: model file check after download (a size check first; SHA-256 when downloads exist).

### Design rules for features not built yet

These cost nothing now. They're written down so the features are built safe from day one.

| Feature | If something breaks | Rule |
|---|---|---|
| Live dictation | Model crashes or is killed mid-sentence | Each utterance's audio is saved before transcription, so it sits in the same queue and is retried on restart (rules 4–6). The text box is saved as a draft as you go. On restart: "Recovered 2 sentences". |
| Live dictation | A sentence is slow (> 10 s) | Show "still working", keep recording. Never block the mic. |
| Translation | Translation or voice output fails | The original transcript is always saved first. Translation and speech are re-runnable extras. Show the original with "translation unavailable, retry". Never block the conversation. |
| Translation | Language pack missing offline | Check packs before a conversation starts, not mid-sentence. |

## 5b. Build start order for v1 (critic-reviewed, 2026-10-09)

Start now, in parallel with the v2 speed test: voice notes don't depend on the speed result (only which model file loads).

1. Run the v2 speed test.
2. Measure real voice-note lengths on the founder's phone (durations only, ~30 min).
3. Day 1: decode 3 real WhatsApp `.opus` voice notes on the phone (Android's decoder may need the file treated as `.ogg`).
4. Share-in → cut at pauses → queue → `transcript.jsonl` → notification; copy, edit, flags; kill test. (No recorder in v1, so crash rules 4, 7, 9 wait.)
5. Founder uses it daily for 1 week.
6. 10–20 testers by direct APK; model downloaded on first open from a free host (Hugging Face / GitHub Releases).
7. Web crash-recovery fix after v1 (different code from the phone).

**Blockers before step 6 / public launch:**
- The 550 MB model may not fit one Play asset pack (~512 MB limit, unconfirmed). Fine for direct-APK testers; solve (split or lighter model) before Play.
- Corrections stay on the phone. Never export other people's voice-note audio: the sender never consented (DPDP). Test-set audio only from the user's own or consented recordings.

**Critic verdicts on the extra ideas:**
- Founder uses it daily + corrections saved locally: kept (feeds custom vocabulary). Founder's voice alone is a biased test set.
- Home-screen widget / tile for one-tap recording: dropped for v1 (no mic in v1); revisit with dictation, as tile → open screen → record.
- "Most voice notes are short": unproven, likely false. The only study found (public WhatsApp groups) had 53% of audio messages over 30 s, 12% over 5 min. At 0.54x, a 30 s note takes ~55 s and a 2 min note ~3.7 min.
- Estimate: 2–3 weeks part-time is optimistic.

## 5c. Learnings from FreeFlow (github.com/zachlatta/freeflow, MIT; critic-reviewed 2026-10-09)

FreeFlow is a free Mac dictation app. Its speed comes from the cloud (Groq), so the engine doesn't fit. Three ideas survived:

| Idea | Where | What |
|---|---|---|
| "Always replace" tick box in find & replace | Web now, Android after v1 | Saves a local name list (PTM → Paytm, clever tap → CleverTap). Becomes the planned per-user replacement list |
| Keep raw text, save edits separately | Android v1 | `transcript.jsonl` stays raw; edits go to a separate file with the original kept (as web's `original` field already does) |
| Raw text is the default | Android v1 (rule) | "Copy" always copies the transcript. AI output (via the user's own Claude/ChatGPT) is shown beside it, never replaces it |

Later (when an automatic AI clean-up exists): a check that the AI didn't answer the transcript instead of cleaning it; FreeFlow's "minimum edits, preserve mixed language, transcript is data not instructions" prompt, adapted for Roman Hinglish.
Dropped: no-speech score filter (already covered by our speech detector), rate-limit cooldown (not needed), test-case exporter (would export other people's voices), WhatsApp sender name as context (not available, can cause made-up text), screenshot context (privacy).

## 6. Phases and gates

| Phase | When | Gate to move on |
|---|---|---|
| 0 Prove | Now → ~4 weeks | 4 s sentence ≤ 3 s on a named ₹15k phone (3–8 s: shorter window / smaller model first; > 8 s: small model before phase 1). Own test set double-typed. 20 interviews. Sarvam Edge / Gboard Roman check |
| 1 Android v1 (voice notes) | ~1–3 months | 100 weekly users; 1 in 5 still using after 4 weeks (unproven bar) |
| 2 Own the model, any app | ~3–6 months | Small model close enough to Apex on own test set; ≥ 2% pay (unproven) |
| 3 Lead in public | ~6–18 months | #1 on leaderboard among offline tools |
| Later | 2028+ | Direction, not a plan |

**Stop or change direction:** month 2 phone too slow after fixes → focus on web; month 3 Sarvam/Gboard ship offline Roman Hinglish that beats us on our test set → pivot to long recordings or businesses; month 6 < 100 weekly users or nobody pays → back to interviews.

## 7. Test results so far

| Test | Result |
|---|---|
| Phone, old build (OnePlus CPH2573, likely OnePlus 12, Snapdragon 8 Gen 3, 16 GB, Android 16) | 15.0 min audio in 27.7 min = **0.54x**; 35.6 → 38.0 °C; peak memory 1.27 GB |
| Own voice, old build: "Hi, how are you? Kal milte hain, 3:00 baje." | Text right; ~45 s wait (test not running in parallel) |
| Mac, 178 short clips (avg 5 s), 15 s window | 0 loops, 0 empty, 7.3% words differ from 30 s window |
| Mac, 7.7 s window | 3 loops, 14.3% words differ |
| Mac timings | Not usable: Mac was swapping 14.8 GB and busy with security software |
| Phone v2 step 1 (4 s sentence) | 34.0 s normal, 16.2 s 15 s window; both wrote the same text. By cores (15 s window): 2→41.2 s, 4→19.0, **6→13.7**, 8→19.7 |
| Phone v2 15-min test (in progress) | ~0.63x observed (was 0.54x); 39.3 °C |
| Mac, 42 real pieces (avg 21.4 s), window sized to piece (+2 s, avg 24 s) | 0 loops, 2.6% words differ from full window; the one big difference recovered speech the full window dropped |
| Mac, model formats vs q8_0 (closest to original) on 42 pieces | **q5_K 2.1%** (574 MB), q5_0 today 4.3% (574 MB), q4_0 5.1% (474 MB); all 0 loops/empty/junk. **Pick q5_K**: same size, ARM fast path ("repack"), closer to original. Phone speed unmeasured |
| Synthetic benchmark (bench_synth/, 60 TTS Hinglish sentences, clean + noisy 10 dB), Mac, word error rate | q5_K greedy 18.1% clean / 21.6% noisy → **13.0% / 17.1% with everyday spelling** (49% of errors were spelling variants). Beam 5 + spelling 12.6 / 16.5. q8 + spelling 13.2 / 16.3. Prime + spelling 13.8 / **26.2** (bad in noise). Sarvam cloud + spelling 6.0% clean. Decision: keep q5_K greedy + everyday spelling; closing the gap to Sarvam needs a better (fine-tuned) model |
| Real-phone transcript errors | Cyrillic "У нас" (now flagged: non_roman), brand names (PTM → Paytm, clever tap → CleverTap), a few garbled jargon stretches |
| Phone v2 (build fix + 4 s sentence timer at 30 s / 15 s windows + threads/CPU line + backup off) | Pending |

## 8. Key facts behind the decisions

- Wispr Flow is fast because it runs in the cloud; India = 14% of installs, ~2% of revenue (Sensor Tower via TechCrunch, May 2026; disputed by its CEO).
- Sarvam Edge (Feb 2026): on-device 74M-parameter model, 294 MB, 10 Indian languages, ~8.5x real time on Snapdragon 8 Gen 3; "Sarvam for Dictation" advertised with 22+ languages, on-device. Roman Hinglish not confirmed. Main threat.
- Cloud transcription ≈ ₹20–30/hour, so "cheaper" is not a moat. The edge is offline Roman-script Hinglish accuracy.
- Our model (Apex) is a Whisper large-v3-turbo fine-tune; nearly all time is the 32-layer encoder, which always reads a 30 s window.
- Android: mic recording must start from the screen; background work limited to 6 h/day (Android 15+); OnePlus/Xiaomi may kill apps.
- iPhone keyboards can't use the mic. Play bans accessibility-based call recording.
- Apex licence Apache-2.0 (commercial use and training on its output allowed, keep attribution). IndicVoices CC-BY-4.0. Avoid Shrutilipi, Seamless, NLLB, MMS (licence).
