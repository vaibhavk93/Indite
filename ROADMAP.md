# indite roadmap

Last updated: 2026-10-09. Every item here passed an independent critic review, or is the founder's own decision.

## Done

- Free local engine: whisper.cpp + Oriserve Hindi2Hinglish-Apex, 5-bit (547 MB, ~0.75 GB RAM, ~2.3x real time on an 8 GB M1)
- Sarvam engine (paid, Roman output), working behind company HTTPS inspection
- Reads any audio/video incl. MPEG; skips damaged spots instead of failing
- Guards that flag (never delete) invented text: no speech, loops, stock phrases, "nan" junk
- Output styles: SRT, VTT, timestamped, paragraphs
- `bench`: scores engines against hand-typed clips
- Web app: upload, background jobs, live progress bar + peek, plain errors, cancel, editor, export, 3-year cleanup with the deletion date shown
- Editor for long files: pinned player and buttons, find & replace with undo, shortcuts, unsaved edits kept in the browser
- `notes` via the user's own Claude login; "Copy for Claude / ChatGPT"
- Local engine is the default; privacy notice matches the chosen engine

## Now (approved)

1. **Accuracy:** done. Tested 12 variants on 13 min of problem audio. Winner: cut audio at pauses into <=25 s pieces and re-run only bad pieces (loops 73 -> 4, 35% faster). Built as `local`; Prime model with the same method built as `local-best` (0 loops, ~2x slower, 2 GB). Dropped: q8 model (more stray words), stricter thresholds and vocabulary prompt (no gain). `-mc 0` alone: -22% loops. Full 56-min file: 24.7 -> 11.6 min, loop words 468 -> 7, stray words 1,385 -> 835, "nan" 3 -> 0 (`local-best`: 19.6 min, 3 loop words). Blind-typed clips still needed to prove accuracy.
2. **Speaker test 1:** done, partly. Normal word times are unreliable (up to 21% of words move >0.5 s when only silence is added). DTW word times are steady (all within 0.06 s) but not yet proven correct, and ~30% slower. Settled inside test 2.
3. **Speaker test 2:** blocked: Hugging Face access for the token's account not granted yet. pyannote community-1 on the 56-min file (speed, memory), then the busiest 5 minutes (~30+ speaker changes) hand-labelled. Score 3 ways: whole pieces / normal word times / DTW word times; also with hand labels as the speakers, and only words within 2 s of a speaker change. Check whether DTW is always early or late. Target: wrong speaker < ~15% (unproven bar).
4. **Android, offline on the phone** (founder decision 2026-10-09: no Mac needed). Step 1: a test APK (whisper.cpp's Android example + the Apex model, audio cut at pauses) that shows the text and the speed. Same 15-min test on the Mac: 2.2 min with GPU, 7.2 min CPU-only; phones mostly run on CPU, so expect slower. Bar (unproven): 15 min of audio in <= 15 min without overheating; also test one mid-range phone. Pass -> build the real app; fail -> phone waits for hosting. A phone-browser route (Mac does the work, over Tailscale) was the critic's cheaper option, kept as a fallback.
   - Test APK source: `android/` (whisper.cpp's Android example; model and test audio copied into `app/src/main/assets/` at build time, never committed). Measures time, speed, battery temperature, peak memory.
   - Still to check for 1-hour files: heat slowdown, battery used, a foreground service (Android background job with a notification) so a long job isn't killed.
   - If the phone is too slow, in this order: whisper.cpp GPU options (Vulkan/OpenCL) or a more compressed model, then the Qualcomm NPU (weeks of work; only Whisper Tiny/Small are published for it).
   - OnePlus/OPPO research (2026-10-09): they don't disclose their speech model; OPPO's recording summaries use cloud Gemini; Hindi support unconfirmed. Dropped: Android's built-in recognizer (Hindi comes out in Devanagari, short clips only, crashed on a OnePlus 9R) and ML Kit GenAI speech (alpha, Pixel-only advanced mode). Later: phone summaries via Android "share" to the user's own Claude/ChatGPT app first; Gemini Nano (only some phones, Hindi unconfirmed) after that.

## Next

- **Speaker labels** + rename (route depends on the speaker tests; Sarvam's paid labels are the fallback)
- **Windows support** (founder decision: after the speaker tests). Python setup script for both systems, whisper.cpp Windows build (CUDA / Vulkan / CPU), stored test clip instead of macOS `say`. Speed on Windows is unmeasured and needs a real Windows PC to test.
- Engine choice from `bench` on real clips (3–5 files per user group, plus a fixed hand-checked test set)
- **Choose when each transcript is deleted** (founder request): a per-transcript setting, e.g. 30 days / 1 year / 3 years / never
- Custom vocabulary (names, brands)
- Indian formatting (₹, lakh, dates, numbers)
- Optional "fix unclear bits with Sarvam" switch for the local engine (off by default; ~₹0.40 per file; those bits leave the Mac)
- Translate to English and a "clean" version without Hindi fillers: extra choices on Copy for Claude / `notes`
- Subtitle line-length setting (check the 56-min SRT first)

## Competitors noted

- Truecaller AI call recording: Hindi/English transcripts, ₹75/month (calls only, not interviews; price reference).

## Later

Hosting, Google login, payments (Razorpay / UPI), installable web app, DOCX export, batch upload,
Devanagari output, subtitle burn-in, autosave to server, "Sign in with ChatGPT".

## Not doing (for now)

Deepgram, Gemini login, "Sign in with Claude" (not allowed), noise cleanup before transcription (hurts accuracy),
uncertain-word highlighting, search across transcripts, in-browser recording, YouTube import, meeting bot,
live transcription, collaboration, editing audio by editing text.
