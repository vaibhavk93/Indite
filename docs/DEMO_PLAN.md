# inditeflow: the demo video plan

One video, for the founder's own leadership. A credibility pitch, not a tutorial.
Research done 16 Oct 2026. Every source is dated. Anything that is marketing copy rather than evidence is labelled.

---

## 0. The verdict in one table

| Question | Answer | Confidence |
|---|---|---|
| How long? | **3:00–3:30.** Not 6–8 minutes | High — length data all points one way; 3:30 chosen over 2:30 because four products need room |
| How do you shorten it? | **Re-run `demo.py` with a shorter scene list. Do not edit video** | High — generation is automated here, cutting is not |
| What comes first? | **The hero moment at 0:00.** The problem is one clause spoken *over* the action | High — changed after the critic; see §13 |
| How many of the 22 scenes survive? | **8 beats.** 12 scenes cut, 2 merged | High |
| Whose voice narrates? | **The founder's, recorded.** Not macOS text-to-speech | High |
| Whose voice goes *into* the app? | **A real human, at least in the hero beat.** Today it is synthetic speech fed in place of the mic — the biggest credibility hole in the current demo | **High. This was missed in the first draft** |
| Burned-in captions? | **Only the spoken Hinglish, as a few cards.** Narration captions ship as a sidecar `.srt` | Medium |
| Split-screen / picture-in-picture edit? | **No.** The real window split already does it | High |
| On-screen latency stopwatch? | **No.** The uncut take is the proof; a number the app draws itself proves nothing | Medium — dropped after the critic |
| Show it failing? | **Yes — but a real, reproducible error, never a planted one** | Medium. Partly unresolved, see §13 |
| Live meeting recording on camera? | **No.** It is the one feature whose permission is still not granted (MAC_PLAN P2) | High |
| Where does the "known limits" list go? | **The covering email, not the video** | High |

**⚠ Remember:** three changes matter more than everything else.
1. **Halve the running time** — and do it by regenerating a shorter run, not by learning to edit video.
2. **Hero moment at second zero.**
3. **A real human voice** — narrating, and speaking into the app at least once. Today every sound in the demo is synthetic, in a video whose whole job is to prove the speech works.

---

## 1. Structure: what the evidence says

### The numbers, and which ones to trust

| Number | Source | Date | Trust |
|---|---|---|---|
| Videos under 1 min hold **52%** of the viewer; 1–5 min "over 50%"; data from 13M+ Wistia-hosted videos | [Wistia, optimal video length](https://wistia.com/learn/marketing/optimal-video-length) | accessed 16 Oct 2026 | **Medium.** Big sample, but Wistia never publishes the date range or the breakdown |
| Under 1 min **50%** engagement, 1–3 min **46%**, 3–5 min **45%**; 13M videos / 79M hours | [Chief Marketer on Wistia State of Video](https://www.chiefmarketer.com/wistia-state-of-video-report-engagement-down-content-under-promoted/) | 2025 report | **Medium.** Same dataset, second-hand |
| Engagement lost in the opening of a video: **4.9%** for a 1–2 min video, **17.3%** for a 5–10 min video | [Wistia, audience retention](https://wistia.com/learn/marketing/understanding-audience-retention) | published 3 Jan 2020 | **Medium-low.** Sample size and year not disclosed. Direction is believable; the decimals are not |
| Viewers get "about halfway" through videos on product pages | Wistia, same page | 2026 | **Medium.** This is the one that matters: the point must land in the first half |
| "**30%** of viewers drop off in the first 30 seconds" | demosmith.ai blog | 2026 | **Fluff.** No study, no sample, no method. Do not quote it |
| "Product demos of 2–4 minutes get a **78%** completion rate" | vendor blogs (rimodreamlabs, ngram) | 2026 | **Fluff.** No method published |

**What is solid:** shorter is better, and the opening loses people fastest in long videos. **What is not solid:** any specific percentage.

### The shape the good demos use

Consistent across the guidance (all marketing-blog grade, no academic backing, so treat as craft convention not proof):

1. **Problem first, product second.** State the situation the viewer already recognises in the first ~10 seconds; the product arrives as the resolution.
2. **Hero moment early.** Find the one moment where the viewer "gets it", and put it in the first 10–30 seconds.
3. **Two or three features that map back to the stated problem.** Not a feature tour.
4. **One specific close.**

Sources: [getsmartcue](https://www.getsmartcue.com/blog/how-to-create-a-demo-video-for-software) (2026), [demopolish, the 90-second rule](https://demopolish.com/blog/saas-demo-video-best-practices/) (2026), [screenkite](https://www.screenkite.com/blog/how-to-make-a-product-demo-video) (2026).

### Narrated walkthrough vs silent capture with captions

| Use | When |
|---|---|
| **Narrated walkthrough** (what inditeflow's demo is) | When the *why* needs saying and the viewer will watch with sound. Right for a leadership pitch |
| **Silent capture + captions** | Social feeds, autoplay, and anywhere sound is off. Also the safe fallback if the narration voice is weak |

For this audience — people who will open it once, at a desk or on a phone — **narrated, with captions on for the Hinglish and the key labels.**

---

## 2. Length: 6–8 minutes is too long

| Audience | Target | Why |
|---|---|---|
| Leadership deciding "does this deserve attention" | **3:00–3:30** | They need the claim, the proof, and the ask. 2:30 was the first draft; it rushes four distinct products (dictation, files, speakers, AI) and the breadth is itself part of the pitch |
| Product launch / public page | 60–90 s | Engagement data; nobody watches a launch video twice |
| Anyone who says yes and wants the detail | A separate 6–8 min walkthrough | Keep the current 22-scene cut *as that file*. Do not delete it |

Craft guidance converges on 1–3 minutes for corporate and explainer video, with engagement falling off sharply after 2 minutes ([motioncue](https://motioncue.com/impact-of-video-length/), [idearocket](https://idearocketanimation.com/17591-best-video-length/), both 2026 — again marketing-grade).

**The lazy win:** the existing 6–8 minute run is not wasted. It becomes the "long version" for whoever asks. The short version is the one that gets sent.

**⚠ Remember — how to shorten it.** `mac/demo.py` generates; `mac/demo_make.py` only lays the narration audio over the raw recording. **There is no trim, no cut, no overlay, no zoom in the pipeline.** So "cut the video" would be the most expensive item on this whole plan. The cheap path is the opposite: **re-run `demo.py` with a shorter scene list in `show()`**, and get a short video out of the machine that already works. Treat every "add an overlay" idea in this document against that same test — if it needs a compositing step that does not exist, it needs to be worth building one for.

---

## 3. Narration: the credibility cost of a synthetic voice

### The evidence

| Finding | Source | Date | Trust |
|---|---|---|---|
| People are **more than twice as likely to trust a human voice (55%) than AI-generated content (23%)** | Audacy Innovation Tracker, via [realvotalent](https://www.realvotalent.com/ai-voice-sentiment) | 2025 | **Medium.** Broadcast-industry survey, reported second-hand |
| In a blind listen, people **could not reliably tell** AI from a professional voice actor. Told it was human, **48%** viewed the clip more favourably; told it was AI, **20%** turned less favourable | vendor blind test, via [voicejungle](https://www.voicejungle.com/human-vs-ai-voiceover/why-ai-voices-still-sound-off/) | 2026 | **Low-medium.** Vendor-run, method not published |
| Listeners matched a voice clone to its human original ~**80%** of the time, but correctly spotted a recording as AI only ~**60%** of the time | Barrington et al., 200+ speakers | 2025 | **High.** Peer-reviewed-grade |
| Once a voice is *recognised* as synthetic, approval collapses (reported correlation **-0.802**), 20 models / 10,000 listeners | [readingminds.ai](https://www.readingminds.ai/blog/why-people-dont-trust-bad-ai-voices) | 2026 | **Low.** Vendor study, self-serving |
| Prosody — tone, pitch, rhythm — drives judgements of warmth, credibility and competence, and those drive acceptance of the technology | [Phonetica, perceptions of OpenAI TTS](https://doi.org/10.1515/phon-2025-0065) | 2025 | **High.** Peer-reviewed |

**The honest reading:** the penalty is not for sounding synthetic. It is for being **noticed** as synthetic. macOS `say` voices at `-r 175` get noticed in the first sentence.

**⚠ Remember:** there is a second, worse problem that no study covers. This is a video about a *speech* product. If the narrator is obviously a robot, the viewer's first unconscious conclusion is "the speech here is fake" — exactly the suspicion the video exists to kill. **Recommendation: the founder records the narration himself, on a phone, in a quiet room.** The script is already written and timed; only the recording changes. The TTS version stays as the fallback if his voice is not available.

### The hole that matters more: the voice going *into* the app

`speak_into_inditeflow()` feeds a macOS voice (Tara) into inditeflow in place of the microphone. That is excellent engineering for a repeatable automated run. **It is a serious problem for a credibility video.**

- The video never shows inditeflow working on a **human** voice. That is the first question anyone will ask.
- Synthetic speech is clean, evenly paced and has no room noise. It is the easiest possible input. A viewer who knows that discounts the accuracy on screen entirely.
- Combined with a TTS narrator, **every sound in the video is machine-made**, in a pitch about whether a speech product works.

| Option | Verdict |
|---|---|
| Keep synthetic input throughout | **No.** It quietly voids the whole demo |
| Real human voice in **every** beat | Ideal, but it breaks the automated re-run and makes each take unrepeatable |
| **Real human voice in the hero beat; synthetic for the repeatable rest, and say so** | **Yes.** One honest line — "the rest of this was driven by a script so it can be re-run; this first one is me" — costs 4 seconds and buys the whole video |

### If TTS is kept anyway, these practices help

- **One sentence per line, under 20 words.** Already true of most `SCRIPT_N` lines.
- **Real punctuation.** Full stops and commas are what the engine turns into breaths. `[[slnc 350]]` is already used for the lead-in; use it between clauses too.
- **~150 words per minute**, roughly 65–70 words per 30 seconds. `demo.py` currently runs `-r 175`, which is fast for an unfamiliar accent. Drop to 150–160.
- **No abbreviations, no symbols, no bracketed asides.** Write "Control Command V", not "⌃⌘V" — `SCRIPT_N` already does this. Keep it.
- **Never let the narrator say a number the screen contradicts.**

Sources: [WellSaid](https://www.wellsaid.io/resources/blog/voiceover-scripts-best-practices), [Narakeet on pauses](https://www.narakeet.com/docs/how-to/add-pauses-to-text-to-speech-voiceovers.html), [voicebros 150 WPM guide](https://voicebros.com/en/blog/voice-over-script-writing) — all 2026, craft guidance.

---

## 4. How voice products actually demo themselves

Checked 16 Oct 2026, on the vendors' own pages.

| Product | What is first on screen | Failures shown? | How they solve "you can't hear typing" |
|---|---|---|---|
| **Wispr Flow** — "Don't type, *just speak.*" | A **before/after**: raw speech with "Umm" and "the the" on one side, clean text on the other | **Yes — as the input.** The mess is the problem they fix, not a defect | Two text panels and a **wpm counter: keyboard 45 vs Flow 220**. The proof is the diff, not the motion |
| **Superwhisper** — "Just speak. Write faster." | No hero video. A download button and a "Watch my demo" link. Then: "Select an app, press ⌥ + space and start dictating" | No | Punts to a separate video, and invites you to **do it yourself** |
| **Otter** — "Meeting AI that turns talk into action" | Meeting capture video, then a named customer quote | No | Scrolling live transcript with speaker labels — the transcript *is* the motion |
| **MacWhisper** | Static screenshots on a Gumroad page | No | Doesn't try. Sells on the model list and the price |
| **Dragon** (Nuance/Microsoft) | Enterprise accuracy and compliance claims, clinician testimonials | No | Testimonial, not demo |

### The four lessons that transfer

1. **Nobody shows failures as defects.** Wispr shows mess *as the input*, fixed on screen. That is the only honest-looking way to show an error without looking broken. Copy that exact move.
2. **The proof is a side-by-side, not an animation.** Raw on the left, result on the right.
3. **Numbers on screen beat adjectives.** Wispr puts "45 wpm / 220 wpm" on the page. inditeflow's equivalent: **seconds from key release to text on screen**, and **Hinglish words right**.
4. **Everyone leads with the same hero:** key down → speak → text appears in a real app. Nobody leads with settings, history or exports. The current `SCRIPT_N` already leads correctly (`N[0]`, `N[1]`, `N[2]`). Keep that and cut almost everything after it.

Competitor latency, useful for the on-screen comparison: Wispr Flow is reported at **under 700 ms p99** by its model host Baseten, with users describing **1–2 seconds** in real use ([spokenly review](https://spokenly.app/blog/wispr-flow-review), 2026 — vendor-adjacent, treat as indicative). inditeflow's `N[2]` already claims "about a second". **Put a real timer on it and let the viewer check.**

---

## 5. Credibility devices for an internal leadership pitch

This audience is not buying. They are deciding whether to believe the thing works. What earns that:

| Device | Why it works | Cost here |
|---|---|---|
| **No cut during the critical action** | "If a process takes three seconds to load in real life, show it taking three seconds — it builds trust." The moment a demo feels staged, "the investor mentally discounts everything that follows" ([dev.to, what investors look for in a live demo](https://dev.to/adamvibe/what-investors-look-for-in-a-live-demo-and-why-most-fail-p6a), 2026) | Free. `demo.py` already records continuously and never cuts |
| ~~An on-screen stopwatch over the latency moment~~ | **Dropped.** A latency number drawn by the product being demoed proves nothing to a sceptic, needs an overlay pipeline that does not exist, and invites an argument about milliseconds that this audience is not having. The uncut take is the proof. If a number is wanted, let an **independent** clock be visible on screen, not one inditeflow drew | Dropped |
| **Raw output before any clean-up** | Matches product rule **R3** ("raw text is the default") — the video proves the rule | Free. It is what the app does |
| **Wi-Fi visibly off in the menu bar** | The whole pitch is "nothing leaves the Mac". One glance at a crossed-out Wi-Fi icon says it better than a sentence | Nearly free: turn Wi-Fi off before recording, and let the menu bar show. **Do not crop the menu bar out** |
| **A real, recognisable fintech sentence** | A generic sentence looks cherry-picked. A sentence a colleague would actually say does not | Free: rewrite `SCRIPT_S` lines |
| **One visible error, fixed on camera** | See §4 lesson 1 | New work: a scripted wrong word plus a Dictionary fix |
| **Same machine, one take, timestamp visible** | Hard to fake, costs nothing | Free |

**⚠ Remember what this audience is actually weighing.** It is not milliseconds. It is **does my data leave the laptop**. A large Indian fintech cares about that more than about speed. **The Wi-Fi-off shot, held, in an uncut take, is the most valuable ten seconds available — and it is free.** Build that before anything with a timer in it.

**What destroys credibility:** jump cuts mid-action, a speed-up during a wait, text appearing with no visible key press, a transcript that is suspiciously perfect in a language the audience knows is hard, and a machine voice dictating into a speech product.

**⚠ Note — one honest disclosure to make.** `demo.py`'s `stage()` pre-answers the "AI sees your meeting/file" warning with `pref:ai_ok_meetings=true` so the modal cannot stop the take. That is a reasonable staging choice, but it means the video silently skips a consent step. Either show the warning once on camera, or say in the narration that it was accepted up front. **Do not leave it unmentioned if the video is going to leadership at a regulated company.**

---

## 6. Parallel / "in-panel" showing

The founder asked to show features running in parallel. The research says be careful.

```
            SHOWING TWO THINGS AT ONCE
          what the viewer's attention can take
                        |
     +------------------+------------------+
     v                  v                  v
+-------------+  #===================#  +-----------------+
| Composited  |  # * REAL WINDOW     #  | Picture-in-     |
| split-screen|  #   SPLIT (today)   #  | picture overlay |
+------+------+  #=========+=========#  +--------+--------+
       |                   |                     |
  + true compare      + already built        + good for a face
  + two equal panels  + it IS the product    + one clear main shot
  - new editing work  + nothing to fake      - second focus point
  - two focal points  - only two panels fit  - no face in this demo
  x ruled out: nothing here is a true A-vs-B comparison

  * = recommended      # box = the pick      x prefix = ruled out
```

**The finding that decides it:** Mayer's redundancy and split-attention work — people learn **worse** from graphics + narration + on-screen text than from graphics + narration alone, because reading and listening to the same words forces the viewer to reconcile two streams ([Mayer's principles](https://www.devlinpeck.com/content/mayers-principles-of-multimedia-learning), 2026; [re-examination in Educational Psychology](https://www.tandfonline.com/doi/full/10.1080/01443410.2026.2678483), 2026 — peer-reviewed). A four-panel "look at everything at once" montage is exactly the failure mode.

Craft guidance agrees: use split-screen only when **both panels are equally important and you are comparing**; use picture-in-picture when one layer is primary and the other supports it ([fiveable, PiP and split-screen](https://fiveable.me/tv-studio-production/unit-5/picture-in-picture-split-screen/study-guide/37ri3dpmLd87Buoz), 2026).

**So: no new compositing.** `stage()` already puts TextEdit on the left half and inditeflow on the right half of the real screen. That is one genuine split, it is the product's actual behaviour, and it is free.

### Layout and text size — the part that actually breaks on a projector

| Thing | Rule | Source |
|---|---|---|
| Recording resolution | 1080p minimum; 720p makes UI text fuzzy | [one-rec](https://one-rec.com/blog/how-to-make-screen-recordings-look-professional), 2026 |
| On-screen labels at 1080p | **36–48 px** | [legibility.info, rules for text in videos](https://legibility.info/rules-for-text-in-videos) |
| Captions at 1080p | **≥ 24 px**, high contrast, no condensed fonts | same |
| Titles at 1080p | 80–120 px | same |
| App font size while recording | Bump 2–4 points above comfortable; what reads on a 27" monitor is tiny in a shared video | [Medium, demo recording guidelines](https://medium.com/@alsargent/video-demo-recording-guidelines-2139f592c91c) |
| Contrast for text on colour | ≥ 4.5:1 | same |

**⚠ Remember for this pipeline:** `demo.py` records the **whole screen** at the Mac's native (Retina) size, and `demo_make.py` writes it out at that size minus one pixel for evenness. **There is no downscale and no zoom.** When that is squashed into a 1080p frame on someone's phone, inditeflow's note text and the pill labels will be small. Two fixes, in order of laziness:

1. **Record a smaller logical display** (Displays → Scaled → a lower resolution) before the take. Zero code.
2. If that is not enough, zoom the two moments that matter — the typed text and the speaker labels — in the final encode.

### Keystroke overlay — the answer to "you can't see the key being held"

The viewer cannot hear the Option key. Every screencast convention says put it on screen: KeyCastr (free, open source, Mac) overlays key presses, and the standard advice is to **show only modifier chords, not every character** ([screencharm](https://screencharm.com/blog/show-keystrokes-on-screen), [screenify](https://www.screenify.studio/blog/2026-04-20-show-keyboard-shortcuts-recording), both 2026).

That is important here: if KeyCastr showed every character, it would *also* show the characters inditeflow types, which would look like the app is typing them — accidentally honest, but confusing. **Modifier-only filtering is required, not optional.**

---

## 7. Captions

**Verdict: yes, but not a word-for-word transcript of the narration.**

| Evidence | Source | Date |
|---|---|---|
| More than **100 empirical studies** find captioning improves comprehension of, attention to, and memory for video | Gernsbacher, *Video Captions Benefit Everyone* | 2015, peer-reviewed |
| Captions significantly help second-language listening (**g = 0.99**) and vocabulary (**g = 0.87**) | Montero Perez et al., meta-analysis | 2013, peer-reviewed |
| Closed captions **+3%** on test scores; interactive transcripts **+8%** | San Francisco State study, via [3Play Media](https://www.3playmedia.com/blog/studies-find-captions-improve-engagement/) | reported 2026 |
| But: graphics + narration + **verbatim** on-screen text is *worse* than graphics + narration (redundancy principle) | Mayer; [Educational Psychology 2026](https://www.tandfonline.com/doi/full/10.1080/01443410.2026.2678483) | peer-reviewed |

**How to square the two:** caption only what the narration does **not** say.

| Layer | Decision |
|---|---|
| The spoken **Hinglish** | **Burn in**, as a handful of cards. The audience reads Roman-script Hindi faster than it parses a recording of it, and this is the content the narrator never repeats |
| Short labels — `Right Option held`, `Speaker 2`, `Wi-Fi off` | **Burn in**, 3–6 words, if and only if the same `ffmpeg` pass is already being added |
| The narration itself | **Sidecar `.srt`**, toggleable. Burning it in duplicates the voice word-for-word, which the redundancy evidence says makes comprehension worse |

**Caveat on the cheap build.** `demo.py` writes `timeline.json` with every clip's start time, and `render()` already measures durations — so an `.srt` for the *TTS* narration is arithmetic on data that exists. **But the moment the founder records his own narration, those timings are wrong**, and the sidecar has to be timed by hand or re-derived. Burning the Hinglish cards needs one new `ffmpeg -vf subtitles=` pass in `demo_make.py`. Budget it as real work, not free.

---

## 8. The recommended beat sheet

Total target **3:20**. "Exists" = `mac/demo.py` does it today. Beats 1 and 2 are merged at the open — the hero starts immediately and the problem is spoken over it.

| # | Beat | Time | On screen | Narration / audio | Build state |
|---|---|---|---|---|---|
| 1 | **Hero, with the problem over it** | 0:00–0:25 | TextEdit empty, left half. Menu bar in frame with **Wi-Fi off**. Hold Right Option → the pill listens → Hinglish typed in. **Unbroken take. Real human voice.** Keystroke overlay shows the held modifier | Founder voice; the problem is one clause spoken over the action (full text in §11) | **Exists** (`speak_into_inditeflow`) but **must be re-shot with a human speaking**. **New:** KeyCastr (modifier-only), Wi-Fi off, recorded narration |
| 2 | **The claim, proved by the screen** | 0:25–0:45 | Same shot. Hold on the Wi-Fi-off menu bar for 2–3 seconds. Point at `chaar baje → 4` | One line, tied to what is visible | **New:** 1 narration line |
| 3 | **A long, real thought, hands free** | 0:45–1:20 | Three taps of Right Command, the long fintech sentence typed in one go | `N[3]`, `N[4]`, rewritten `SCRIPT_S[1]` | **Exists** (`hands_free=True`). **New:** rewrite the sentence into one a colleague would really dictate |
| 4 | **Honest accuracy** | 1:20–1:45 | Whatever the engine actually produced, left on screen. Dictionary page: add the company name it got wrong, say it again, it is right | New narration, with the real number | **Mostly exists** (`js:go('dict')`). See §10 risk 1 — the error must be a **real, reproducible** one, not planted |
| 5 | **A recording, and who said what** | 1:45–2:20 | Drop the call file in; transcript appears with speaker labels; rename a speaker | `N[11]`, `N[12]` | **Exists** (`js:go('files')`, `file:`). Live meeting **cut** — see §9 |
| 6 | **Your own AI, your own account** | 2:20–2:50 | Open one note, Improve, original stays beside the new version. Narration covers the wait | `N[8]` trimmed, `N[9]` | **Exists** (`ai:improve`, 9 s wait) |
| 7 | **What it is** | 2:50–3:05 | inditeflow window, clean, still offline | `N[22]` | **Exists** |
| 8 | **The ask** | 3:05–3:20 | Hold on a still frame | One sentence: what is needed next | **New:** the ask line |

### New work, as a list

1. **A shorter `show()` in `demo.py`** — the 8 beats, nothing else. This is the whole "edit", and it is a list change.
2. **Record the founder's narration.** `demo_make.py` lays WAVs from `timeline.json`, so this is a file substitution plus re-timing.
3. **A human voice in beat 1**, replacing the synthetic mic feed for that beat only.
4. KeyCastr, **modifier keys only**, running during the take.
5. Wi-Fi off, Do Not Disturb on, menu bar left in frame, a smaller logical display resolution.
6. Rewrite `SCRIPT_S[1]` into a sentence a colleague would really dictate.
7. Hinglish caption cards via one `ffmpeg -vf subtitles=` pass; narration `.srt` as a sidecar.

**Dropped from the first draft after the critic:** the stopwatch overlay, and any planted error.

Everything else is already running.

---

## 9. What to cut, and why

| Cut | Was | Why |
|---|---|---|
| Escape cancels | `N[5]` | A safety detail. Nobody decides on a cancel key |
| Control-Command-V types it again | `N[6]` | Power-user convenience. Long version only |
| "Every dictation is saved here" | `N[7]` | Implied by beat 7 |
| The nine AI actions listed out | half of `N[8]` | Feature list. Keep **one** action, shown working |
| "Improve keeps your original" | `N[9]` | Fold into beat 7's picture — the two panels say it |
| The gold edge | `N[10]` | A UI affordance. Invisible value to leadership |
| **Live meeting recording** | `N[13]`, `N[14]`, the meeting block | **The permission is still not granted and it is untested in a real call (MAC_PLAN P2).** Highest-risk thing in the video, and beat 6 already proves speaker separation. Say it in one sentence instead of showing it |
| To-do | `N[15]` | A list feature. Every app has one |
| Dictionary as a *tour stop* | `N[16]` | Promoted into beat 5, where it earns its place by fixing a visible error |
| Insights | `N[17]` | Self-reported time saved, from the product being pitched. Leadership will discount it, and it invites the wrong argument |
| The pill transparency slider | `N[18]` + the 30/70/100/60 loop | Pure decoration. The most cuttable 10 seconds in the video |
| AI is off by default | `N[19]` | Right policy, wrong medium. One line in the email that carries the video |
| Help page | `N[20]` | Documentation |
| Subtitles / Text export | (in the long cut) | Nobody evaluates a product on its export formats |

**12 scenes cut, 2 merged.** 22 → 8 beats.

**⚠ Remember:** none of this is deleted from `demo.py`. The long run stays as the detailed walkthrough for whoever asks for it. Only the sent version is short.

---

## 10. The three moments where this could look bad

### Risk 1 — a wrong word appears on screen, unplanned

The clean-set error rate is **14.4% of words wrong** (MAC_PLAN §0). On a 20-word sentence that is roughly 3 words. **An error is not a risk; it is the expected case.**

| Handling | Verdict |
|---|---|
| Retake until it is perfect | **No.** Perfect Hinglish on a 14.4% engine reads as staged, and this audience speaks Hinglish |
| Hide it with a cut | **No.** Cuts during a critical action are the single clearest staging tell |
| Invent an error and plant it | **No.** A sceptic gets nothing from a staged failure, and if anyone works out it was planted it costs more trust than the error would have |
| **Use a real, reproducible error** — a company or product name the engine genuinely gets wrong every time — and fix it with the Dictionary on camera | **Yes.** Not staged: it is a real defect, merely a *chosen* one. This is Wispr Flow's move — the mess is the input, fixed on screen |
| Say the number out loud | **Yes.** One line: roughly one word in seven needs a touch-up today, and the Dictionary closes the gap on the words that matter — names |
| Re-roll a take because a genuine error appeared | **No.** Leave it. Then an unplanned error reads as more of the same, not as a collapse |

**The rule:** pick a defect that is real and repeatable. Never write one in.

### Risk 2 — a long silence while AI answers

`demo.py` waits **9 seconds** on `ai:improve`. On a 170-second video that is 5% of the running time staring at a spinner.

| Handling | Verdict |
|---|---|
| Cut it out | **No.** It is the clearest "this was edited" signal, and it would hide a real property of the product |
| Speed it up | **No.** Same problem, plus the mouse moves at a visibly wrong speed |
| **Narrate across it** | **Yes.** `demo.py` already does exactly this: `say(N[8])` runs during the wait. Make the line long enough to cover it, and make it say something worth hearing |
| Show progress | **Yes.** A visible working state means the wait reads as work, not as a hang |

Precedent: the guidance is explicit — if a step takes three seconds in real life, let it take three seconds on camera.

**⚠ Note — where the limits list goes.** Narrating your own failure modes *inside* a 3-minute credibility pitch undercuts it and eats the runtime you just bought. Beat 4 shows **one** honest number and one fix. **Everything else — the 14.4% figure, the untested meeting permission, Intel Macs, the unsigned build — goes in the covering email or a closing "known limits" still, not the voice-over.** In writing it reads as rigour; spoken over a demo it reads as apology.

### Risk 3 — a macOS permission dialog, or any modal

Two live hazards: the system permission prompts (Accessibility, Microphone, Screen Recording) and inditeflow's own AI-sees-your-file warning, which `stage()` currently pre-answers off camera.

| Handling | Verdict |
|---|---|
| Grant everything before recording | **Yes, for the system prompts.** They are first-run noise, not product behaviour |
| Silently pre-answer the AI consent warning | **Risky.** It is a privacy consent, to a leadership audience at a regulated company. Either show it once, or say in narration that it was accepted up front |
| **Show the first-run permission screen for 3 seconds, on purpose** | **Worth considering.** For an offline-privacy product, a visible, finite permission list is evidence, not friction |

**⚠ Note:** one more hazard specific to this runner — `demo.py` hides every other app and restores them at the end. If a Slack or Mail notification banner lands mid-take, retake. Turn on Do Not Disturb before recording. It is one toggle and it has ended more demo takes than any bug.

---

## 11. The opening 30 seconds, as narration

Same plain spoken style as the existing `SCRIPT_N` lines. Short sentences. No jargon. Read at about 150 words per minute. **The action starts before the narration does** — the first thing the viewer sees is a key being held, not a slide.

> **[0:00 — TextEdit empty, Wi-Fi off in the menu bar. The key goes down immediately.]**
>
> "This is me talking to my Mac, in Hinglish, the way I actually think."
>
> **[0:04 — a real human voice, speaking the work sentence into the app]**
>
> *(spoken into the app, in Hinglish: the real work sentence)*
>
> **[0:14 — the text lands in TextEdit, in one unbroken shot]**
>
> "I held one key, and the words were typed straight into the app I was already in. About a second. Chaar baje came out as four, in digits."
>
> **[0:22 — the shot holds on the menu bar]**
>
> "And look at the Wi-Fi. It is off. Nothing left this Mac. No account, no cloud, and no bill per recording."
>
> **[0:30 — into beat 3]**
>
> "That is the whole idea. Here is what else it does."

Word count: ~85 spoken words across 30 seconds, which with the dictation audio in the middle leaves room for the pauses.

**Why it is built this way:**

| Line | Job |
|---|---|
| Nothing before the key goes down | The hero moment is at second zero. The first draft spent 12 seconds explaining that typing Hinglish is slow — to an audience that lives it |
| "the way I actually think" | The problem, as one clause, *over* the action instead of before it |
| The dictation itself, in a human voice | The proof. A machine voice here would void it (§3) |
| "About a second… four, in digits" | A number, said while the viewer can still check it against what just happened |
| "look at the Wi-Fi. It is off." | The differentiator, proved by something visible rather than claimed. For a fintech audience this is the single most valuable sentence in the video |
| "Here is what else it does." | Hands over without a list |

## 12. Sources

All accessed 16 Oct 2026. Grade: **P** = peer-reviewed or academic, **I** = industry dataset, **C** = craft/marketing guidance, **V** = vendor's own page or vendor-run study.

| Grade | Source |
|---|---|
| P | Gernsbacher, *Video Captions Benefit Everyone* (2015) |
| P | Montero Perez et al., captioned video meta-analysis (2013) — L2 listening g=0.99, vocabulary g=0.87 |
| P | Mayer's multimedia principles; [redundancy re-examined, Educational Psychology (2026)](https://www.tandfonline.com/doi/full/10.1080/01443410.2026.2678483) |
| P | [Perceptions of OpenAI text-to-speech, *Phonetica* (2025)](https://doi.org/10.1515/phon-2025-0065) |
| P | Barrington et al. (2025), voice clones, 200+ speakers |
| I | [Wistia, optimal video length](https://wistia.com/learn/marketing/optimal-video-length) — 13M+ videos; date range undisclosed |
| I | [Wistia, audience retention](https://wistia.com/learn/marketing/understanding-audience-retention) — published 3 Jan 2020, sample undisclosed |
| I | [Chief Marketer on Wistia State of Video (2025)](https://www.chiefmarketer.com/wistia-state-of-video-report-engagement-down-content-under-promoted/) |
| I | Audacy Innovation Tracker, human voice 55% vs AI 23% (reported second-hand) |
| C | [dev.to, what investors look for in a live demo (2026)](https://dev.to/adamvibe/what-investors-look-for-in-a-live-demo-and-why-most-fail-p6a) |
| C | [legibility.info, rules for text in videos](https://legibility.info/rules-for-text-in-videos) |
| C | [Medium, video demo recording guidelines](https://medium.com/@alsargent/video-demo-recording-guidelines-2139f592c91c) |
| C | [fiveable, picture-in-picture and split-screen](https://fiveable.me/tv-studio-production/unit-5/picture-in-picture-split-screen/study-guide/37ri3dpmLd87Buoz) |
| C | [screencharm](https://screencharm.com/blog/show-keystrokes-on-screen), [screenify](https://www.screenify.studio/blog/2026-04-20-show-keyboard-shortcuts-recording) — keystroke overlays |
| C | [demopolish 90-second rule](https://demopolish.com/blog/saas-demo-video-best-practices/), [getsmartcue](https://www.getsmartcue.com/blog/how-to-create-a-demo-video-for-software), [screenkite](https://www.screenkite.com/blog/how-to-make-a-product-demo-video) |
| C | [WellSaid](https://www.wellsaid.io/resources/blog/voiceover-scripts-best-practices), [Narakeet](https://www.narakeet.com/docs/how-to/add-pauses-to-text-to-speech-voiceovers.html), [voicebros](https://voicebros.com/en/blog/voice-over-script-writing) — TTS script craft |
| V | [wisprflow.ai](https://wisprflow.ai/), [superwhisper.com](https://superwhisper.com/), [otter.ai](https://otter.ai/) — hero sections, checked 16 Oct 2026 |
| V | [readingminds.ai, 10,000 listeners](https://www.readingminds.ai/blog/why-people-dont-trust-bad-ai-voices), [voicejungle blind test](https://www.voicejungle.com/human-vs-ai-voiceover/why-ai-voices-still-sound-off/) — vendor-run, treat as indicative |
| V | [spokenly, Wispr Flow review (2026)](https://spokenly.app/blog/wispr-flow-review) — Wispr latency <700 ms p99 (Baseten), 1–2 s in practice |

**Unverified claims deliberately excluded:** "30% drop off in the first 30 seconds", "78% completion for 2–4 minute demos", and every "X% more conversions with video" figure found during this research. None publish a method.

---

## 13. What the critic said

House rule: every recommendation goes past an independent critic before it is recommended. A fresh critic was given all eight of the first draft's recommendations and asked to break them. Verdict: **2 kept, 3 changed, 3 dropped.**

| First draft said | Critic's objection | What changed |
|---|---|---|
| Cut to 2:30, kill 12 scenes | The breadth *is* part of the claim — one person shipped 22 things. And **there is no cutting pipeline**, so "cut the video" is the most expensive item on the list | **Changed.** 3:00–3:30, and shortened by **re-running `demo.py` with a shorter `show()`**, not by editing |
| Problem first, hero at 0:25 | Leadership at an Indian fintech already agrees that Hinglish typing is painful. Spending the only attention budget on the thing they agree with reads like an ad | **Changed.** Hero at 0:00, problem as one clause over the action |
| Keep macOS TTS narration | Worst of the eight. A credibility pitch where **every sound is synthetic** — and the bigger hole: synthetic mic input means the video never shows the app working on a human voice | **Dropped.** Founder records the narration; a real human speaks into the app in beat 1. Added as §3 |
| Burned-in captions from `timeline.json` | Half of it was patching the TTS problem. Re-recorded narration invalidates the timings, and burning captions needs compositing that does not exist | **Changed.** Hinglish cards burned in; narration as a sidecar `.srt`; timing cost flagged |
| On-screen latency stopwatch | A number the demoed product draws itself proves nothing, and invites a millisecond argument. Latency is not what a fintech exec is weighing — **whether data leaves the laptop** is | **Dropped.** Replaced by the uncut take plus the Wi-Fi-off shot |
| No picture-in-picture | Kept. One caveat: a 50/50 split on a 1280-wide playback makes both UIs unreadable | **Kept**, with the font-size and logical-resolution fix in §6 |
| Plant a wrong word, fix it with the Dictionary | Still staged, so it buys nothing from a sceptic and costs real trust if spotted. In a 3-minute exec video the wrong word is what gets quoted back | **Changed, not fully resolved.** Use a **real, reproducible** error (a name the engine genuinely fails on) and never re-roll a genuine one. The critic would rather show no error at all |
| State the risk list | In the video it undercuts the pitch and eats runtime | **Kept, relocated.** The limits list goes in the covering email, not the voice-over |

**Still unresolved:** whether to show an error at all (§10 risk 1). The research says showing mess-as-input builds trust; the critic says any error in a 3-minute exec video becomes the quote. **The judgement call is the founder's**, and it is the one open decision in this plan.
