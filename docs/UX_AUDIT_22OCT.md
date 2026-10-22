# UI, UX and capability audit — 22 Oct 2026

Measured on the founder's own Mac from 354 real notes, not from the code or from opinion.

---

## 1. Capabilities: what is actually on

| Capability | State | Note |
|---|---|---|
| Dictation (hold Right ⌥) | on | 330 dictations |
| Hands-free (Right ⌘ ×2) | on | |
| Typing into other apps | on | "smart" - types when it finds a text box, copies when it does not |
| Text card after dictating | on | and now forces itself on for a clipboard fallback |
| AI actions | on | own Claude login · **20 notes have an AI answer, out of 354** |
| Mark likely mistakes (step 1) | on | |
| Review with AI (step 2) | on | |
| Speech test page | on | **178 notes waiting to be checked** |
| Keep recordings | on | 215 MB, now capped at 500 MB |
| Swear masking | on | raw word still stored |
| Who spoke, automatically | on | 11 meetings, 13 files |

**Everything that can be on, is on.** Nothing is broken-but-enabled, and nothing useful is switched off.

---

## 2. The one number that matters: the wait is not what we claim

The demo script says "about a second". That is the **median**, and it is true. It is not the experience.

| What the founder sees | Measured over 330 real dictations |
|---|---|
| Median wait | **1.7 s** |
| 9 times in 10, under | **7.9 s** |
| 1 in 5 dictations | **over 5 seconds** (60 of 330) |
| 24 dictations | over 10 seconds |
| Worst | **25.9 s** |

And the cause is plain:

| You spoke for | How many | Median wait |
|---|---|---|
| under 5 s | 59 | 0.8 s |
| 5-10 s | 83 | 0.9 s |
| 10-20 s | 65 | 1.6 s |
| **20 s or more** | **123** | **3.9 s** |

**123 of 330 dictations are 20 seconds or longer** - that is how this founder actually works, thinking out loud.
And those are exactly the ones that make him wait, with a pill that says "writing" and nothing else. The app is
tuned for the sentence and used for the paragraph.

---

## 3. What I would change, in order

### A. Show progress on a long dictation (the biggest win)
Today the pill says "writing" whether the wait is 0.8 s or 25 s. A long hold is split into pieces and transcribed
one at a time, so **the app already knows how far along it is** and says nothing. Show it: "writing 2 of 5", or fill
the pill left to right. No new engine work, no risk to accuracy - it turns an unexplained 20-second wait into a
visible one. **~2 h.**

### B. Type each piece as it is ready, instead of all at once at the end
The pieces finish one at a time. Typing each as it lands would put the first words on screen in about a second
instead of after twenty. **Needs care** - the founder may have moved the cursor by then - so it belongs behind a
setting, and after A. **~4 h, gated on A being in use for a week.**

### C. The text card is the right place for the slow case
It already appears, already holds for 6 seconds, already keeps itself up while the pointer is on it, and now
explains a clipboard fallback. The missing piece is the same as A: while the words are still coming, it could show
what is done so far rather than waiting to show everything.

### D. Small UI faults worth fixing while nearby
| What | Where |
|---|---|
| "1 words" | the Dictations list, when a note is one word |
| "To check · 178" sits next to All / Starred / With AI as if it were a filter of the same kind | it is a task queue, not a view |
| 20 AI answers against 354 notes | the AI actions are a tab away; the card now has buttons, which should help - worth re-measuring in a week |

---

## 4. What I would not change

- **The pill's size and position.** It works, it is confirmed at full opacity, and the founder has a recording to
  make. Changing it now is the wrong moment.
- **The Insights page.** It is honest, it is using real data, and the numbers are the ones that matter.
- **The clipboard fallback rate.** Measured per app: Terminal 0%, Claude 8%, Chrome 7%. It is small, and now it
  explains itself. Not worth engineering further.
