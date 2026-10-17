# Speech test: final plan (critic-reviewed 17 Oct) - supersedes the draft below

**Verdict:** smaller than the draft. Fix notes on the Home page you already have, score in the terminal, and add a
small read-aloud page last. **Grow the Dictionary first** - without names to look for, the test proves nothing.

| Draft said | Critic found | Final |
|---|---|---|
| Part A (your own notes) alone answers the AI-review gate | Your Dictionary has 1 usable name and none of the 120 kept notes contain it: 0 flags, so it "passes" without testing anything | Gate needs ~20 names of 6+ letters, ≥2,000 words, ≥30 name mentions in ≥15 clips (estimates, unproven) |
| A new full page for part A | Home already plays a note and edits it with Undo | One action "This is exactly what I said" + a filter "kept audio, not checked (12/35)" |
| Send the dictation into the page while armed | Breaks dictating your own correction, a stale "armed" flag, a second output path | Typing stays normal; while armed the note is simply saved and tagged (≈3 lines) |
| Save only after one full listen | Can't be built: Play opens an outside app | Cut |
| Score screen, categories, history UI, export, variants tap | One person: terminal output is enough | Cut for now |
| Scorer starts its own engine | It would kill the app's engine (same port) | Use the running engine only, or refuse |
| Score with review.flags on confidence | The app uses review.on_text on the saved text | Score the live path: transcribe → tidy → on_text |
| Pre-fill "what I really said" | May bias the reference | Keep, but type 5 clips from scratch first and compare (5 min) |

**Build order:** 1 grow the Dictionary to ~20 names (you) · 2 `mac/speechset.py` scorer, terminal, live path (M) ·
3 Home: "This is what I said" + not-checked filter (S) · 4 first score of your own notes - real words-wrong number,
not yet the gate (S) · 5 small read-aloud page: one sentence at a time, Arm / Next / Skip, too-quiet check, ~25
sentences with 1-2 Dictionary names each (M) · 6 gate score (S).

**⚠ Remember:** speech-set text, sentences and results stay on the Mac and are never quoted in docs or commits.

---

# Speech test: building the real speech set (plan)

**Draft (superseded by the final plan above).** Written 17 Oct 2026. Roadmap: Mac next #1. Gates it unlocks: Mac next #3, #5, #6.

**Verdict: build it as a "Speech test" page in the Mac window. He reads each sentence with his normal dictation key,
so there is only one microphone and one engine. Do the 35 own dictations first: they need no recording at all.**

---

## 1. What we already have

| Thing | Where | Use here |
|---|---|---|
| 120 notes with kept audio (avg 19.6 s, 4,177 words) | `~/Library/Application Support/indite/audio/` | Enough for the 35 own dictations today |
| Scorer with Hinglish spelling and number rules | `bench_synth/score.py` (`normalize`, `align`, `edits`) | Reuse as is |
| Likely-mistake finder | `mac/review.py` `flags()` | Gate step 1 |
| Per-word confidence | `Engine.confidence` | Input to `flags()` |
| Terminal recorder with play / redo / pause | `mac/narrate.py` | Ideas only (see section 2) |
| Engine-vs-engine bench | `indite bench` (`clips/<group>/<name>.wav` + `.txt`) | Second-engine check via export |

**Note:** a note's stored `text` may be edited or Dictionary-fixed (`raw` is kept only when they differ). **Scoring must
re-transcribe the audio fresh**, never trust the stored text.

---

## 2. Where it lives

```
                       WHERE DOES THE SPEECH TEST LIVE?
                one person, ~1 day of use, then re-scored now and then
                                     |
         +---------------------------+---------------------------+
         v                           v                           v
 +----------------+      #=======================#      +------------------+
 | x Terminal     |      # * Page in Mac window  #      | Page + own       |
 | (narrate.py)   |      #   reads via hotkey    #      | recorder in page |
 +-------+--------+      #===========+===========#      +--------+---------+
         |                           |                           |
  + fastest to build          + one mic, one engine        + pause mid-sentence
  - editing a 35-word         + same path as real use      - a second recorder
    note in a terminal          (the thing we measure)       next to the Mic class:
  - second process loads      + edit boxes, diff colours     the stuck-CoreAudio
    a second 574 MB model     - needs a "send to test"       trap all over again
  - two mics open at once       switch on dictation       - more code

  * = recommended        # box = the pick        x = ruled out: bad for editing text
```

**How "read with the hotkey" works:** while the page is armed, the next finished dictation is not typed or saved as a
note. It goes to the current sentence instead. Everything else (mic choice, trimming, stuck-mic restart) is the normal
path.

**⚠ Remember:** divert only when **the indite window is in front, on the Speech test page, and armed**. If he switches
to Slack and dictates, it must type into Slack as usual. Disarm after each take.

---

## 3. Prior art (all links read 17 Oct 2026)

| Tool | What it does | What we take |
|---|---|---|
| Mozilla Common Voice | One sentence on screen; record; skip a sentence you can't read; play back and re-record any clip before sending; 2 of 3 listeners must agree ([paper, 2019](https://arxiv.org/pdf/1912.06670v1), [QA plan](https://m.wiki.mozilla.org/QA/Common_voice)) | Big sentence, Skip, ▶, Redo one clip. Not the voting: one person |
| Label Studio "ASR with segments" | Audio player + an editable transcript box per region, required before submit ([template](https://labelstud.io/templates/automatic_speech_recognition_segments)) | Edit box per item; can't save empty |
| Apple Voice Memos | Pause/resume; "Replace" records over one part; keep old or overwrite ([Apple](https://support.apple.com/guide/voice-memos/vmac7e39c22e/mac)) | Redo replaces only that take |
| MUCS 2021 Hindi-English challenge (Apr 2021) | Scores "transliterated WER" too, so a word spelled another way is not an error ([arXiv 2104.00235](https://arxiv.org/pdf/2104.00235)) | Spelling-variant table |
| WER standardisation (Mar 2023) | Spelling variants and word splits make WER look worse than it is ([arXiv 2303.05046](https://arxiv.org/pdf/2303.05046)) | Show strict and normalised side by side |

**Words used:** *WER* (word error rate) = words wrong ÷ words said. *CER* = the same, counted in letters; it is
kinder to spelling variants.

---

## 4. The flow

```
 Speech test page
   |
   +-- [Mic check] -- mic name, 3 s level test, noise check
   |
   +-- A. Your own dictations (35) ----+
   |     queue of kept-audio notes     |
   |     ▶ play -> fix text -> Save    |
   |     or Skip-private -> next       |
   |                                   +--> refs.jsonl (saved after every item)
   +-- B. Read aloud (15) -------------+
   |     sentence -> hotkey -> result  |
   |     Keep / Redo / Edit / Skip     |
   |                                   |
   +-- [Pause] any time: nothing lost  |
   +-- [Score] ------------------------+--> results/<date>-<engine>.json
          re-run any time
```

### 4A. Own dictations (do this first)

1. Queue = notes with kept audio, newest first. Shows "12 of 35 done".
2. Press ▶ (or Space). The clip plays.
3. Below it: a text box **pre-filled with indite's fresh text**. He fixes only what is wrong.
4. **Save** turns on only after the clip has played once. Enter saves and opens the next.
5. **Skip - private** leaves the note out for good. **Skip - later** comes back at the end.

**⚠ Remember:** pre-filling saves typing but nudges him to accept indite's mistakes ("it looks right"). Mitigation:
Save needs one full listen. The size of this bias is **unproven**.

### 4B. Read aloud (15 sentences)

| Step | Screen shows | Keys |
|---|---|---|
| 1. Ready | Sentence in big text, "7 / 15", category tag (name, number, ₹, Hinglish) | Arm = A |
| 2. Speak | Normal pill; he holds/taps his dictation key and reads | His hotkey |
| 3. Result | indite's text under the sentence; wrong words red, missing struck through, extra in grey; "2 words wrong" | — |
| 4. Decide | **Keep** · **▶ Play** · **Redo** (replaces this take only) · **I said it differently** (edit box, starts as the sentence) · **Skip** | Enter, Space, R, E, S |

- **Pause:** Esc or the Pause button. Each take is written to disk the moment it lands, so closing the window, a call,
  or a restart loses at most the take in progress. The page reopens at the first sentence not done.
- **Stop:** "Finish now" scores whatever is done. Missing items are listed, not counted as zero.
- **No pause mid-sentence.** Sentences are 8-15 words; Redo is simpler and the dictation path has no pause. (narrate.py
  needed one for long paragraphs; this does not.)

**⚠ Remember:** the 15 sentences use his Dictionary names, which may include work names. **The sentence file stays in
Application Support, never in the repo** (public, and the no-employer rule).

---

## 5. Scoring screen

| Shows | How |
|---|---|
| Words wrong overall, normalised and strict, plus CER | `score.py` `normalize` + `align` |
| Same, split: own dictations vs read aloud | by `kind` |
| By category: names, numbers, ₹, Hinglish-heavy | per-sentence tag; numbers word-level (digits) |
| Engine alone vs engine + Dictionary fixes | run `store.apply_my_fixes` on the same text |
| **Gate step 1:** false flags per 100 words (needs ≤ 1); clips with ≥ 1 real catch (needs ≥ 10) | `review.flags(Engine.confidence(audio), dictionary)`; a flag is right if the reference has the suggested word there |
| Gate step 2 (≥ 70% right) | Placeholder until step 2 exists |
| Worst 5 items, each with ▶ | sorted by words wrong |
| History | one line per run: date, engine, Dictionary size, words wrong, flags/100 |

**Re-score** button: re-transcribes all items with the current engine and Dictionary. About 50 clips, roughly a minute.

**⚠ Remember:** about 1,400 words from one voice and one mic. **0.8 vs 1.2 false flags per 100 words is about 11 vs
17 flags: too close to call.** And it says how indite does for the founder, not for other users.

---

## 6. Data

```
~/Library/Application Support/indite/speechset/
  script.tsv          id, sentence, tag          (the 15 sentences; local only)
  refs.jsonl          one line per item
  read/S07.wav        read-aloud takes (16 kHz, same as dictation)
  results/2026-10-18-default.json
  variants.tsv        spelling pairs he marked "same word" (see 7)
```

`refs.jsonl` line: `{"id": "S07" | "note:<note id>", "kind": "read"|"own", "said": "...", "script": "...",
"tag": "rupee", "mic": "MacBook Pro Microphone", "peak": 0.41, "skip": null|"private"|"later", "at": "..."}`.

- Own dictations **point to** the note's audio; they are not copied. Delete the note and it drops out of the set
  ("3 items missing audio"). A copy would quietly keep a recording he deleted.
- **Export** writes the `indite bench` layout (`<name>.wav` + `<name>.txt`) to a folder he picks. It refuses any
  folder inside the repo.
- **Delete speech set** removes the folder. Notes are untouched.

**⚠ Remember:** recordings of a real person never go in git. The folder is outside the repo, and export refuses the
repo. `clips/` is already git-ignored.

---

## 7. Things he hasn't thought of

| Issue | What we do | Size |
|---|---|---|
| Mic check | Before starting: mic name, "say ek do teen", show level | S |
| Bluetooth mic | AirPods' mic is low-quality phone audio. Warn; store `mic` per take; split the score by mic | S |
| Too quiet / clipping | Peak < 0.05 = "too quiet, redo?" (narrate.py's rule); many samples at full scale = "too loud" | S |
| Background noise | Loud level before he speaks = "noisy room" note on the take | S |
| Spelling variants (hai/he, kya/kia) | Shared table in `score.py` `SPELL`. Plus a "same word, different spelling" tap on a red word, saved to `variants.tsv`. **The score lists every variant used**, so the number can't be quietly flattered | S |
| Picking only easy notes | Queue order is fixed (newest first); skips are counted and shown | S |
| Second engine | Export + `indite bench`; no second engine in the app | — |
| Score over time | History list (section 5) | S |
| Keyboard only | Every action has a key; shown on screen | S |
| Accessibility | Real buttons with labels; diff uses strike-through and colour, not colour alone | S |
| A call comes in | Pause, or just leave: every item is already saved | — |
| Stuck mic mid-session | Normal stuck-mic restart; page reopens on the same sentence | — |

---

## 8. Build plan

| # | Step | Size | Reuses | Check |
|---|---|---|---|---|
| 1 | `mac/speechset.py`: read refs, re-transcribe, score, gate step 1, history; also runs from the terminal (`score`) | M | `score.py`, `Engine`, `review.flags`, `apply_my_fixes` | `--selftest` with made-up refs: known WER, one true and one false flag |
| 2 | Page, part A: own-dictation queue, play, pre-filled edit, skip-private | M | window's `play` action, page and tab patterns in `app.html` | Bridge test: save writes one line, skip-private never scored |
| 3 | **First score:** 35 own dictations; gate step 1 measured | S | step 1 | — |
| 4 | Part B: 15 sentences, arm, divert, result + diff, Redo / Edit / Skip, quality checks | M | `finish()` path, `align` for the diff | Test: divert only when armed + front + on page |
| 5 | Score page and history | S | step 1 | — |
| 6 | Export / delete | S | `indite bench` layout | Test: export into repo refused |

**Order: 1 → 2 → 3 → 4 → 5 → 6.** Steps 1-3 alone answer the open question (gate step 1 on real dictations). Part B
adds the names, numbers and ₹ that his own notes may not have.

**Behind a setting:** show the page only with the founder's "Mark likely mistakes" setting on, like the review itself.

### Left out (add when asked)

- Pause mid-sentence; waveform; trimming audio by hand
- More than one speaker; other people checking his takes (Common Voice voting)
- Splitting a long note into lines to score separately
- A second engine inside the app
- Devanagari references
- Sync or upload of any kind

