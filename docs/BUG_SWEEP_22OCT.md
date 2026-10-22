# Bug sweep, 22 Oct 2026

Asked for: the pill, plus positive, negative, runtime and UI/UX testing across the whole Mac app, and a plan.
Everything below was run against the app actually running on this Mac, not read from the code.

---

## The pill: fixed, and confirmed from real use

| Check | Result |
|---|---|
| Every state change during the founder's own dictations | `on screen=True`, **`alpha=1.00`**, `level=25`, 116x30 at (662,96) |
| Draw loop | 17.9 - 20.0 ticks a second (asked for 20) |

It used to reach only alpha 0.40 after a six-second hold - on screen and invisible. It no longer fades in.
**Not a bug any more.** What remains is a design question, not a fault: at 116x30 points, 96 points above the
bottom, it is small and low. If it is still being missed, the answer is size or position, not visibility.

---

## What passed

| Area | Result |
|---|---|
| Module self-checks | 6 of 6 pass (`store`, `digits`, `ai`, `narrate`, `polish`, `indite_mac`) |
| Unit tests, run as documented | 4 of 5 pass |
| Negative input to word fixes | 7 of 7 safe: empty text, 200k characters, emoji and Devanagari, regex metacharacters, `\1` and `$0` in a replacement, blank-only input |
| All 8 window pages | Every one draws, **no JavaScript errors on any of them** |
| Engine | answers in 23 ms, 45 MB |
| App health | 27 MB, 16 threads, **0 threads stuck in CoreAudio**, no crash since this morning's boot |

A `\1` in a Dictionary replacement is worth calling out: it used to crash the app (`re.error: invalid group
reference 1`) and now comes through as literal text. That one is already fixed.

---

## Bugs found

| # | Bug | How bad | Evidence |
|---|---|---|---|
| **B1** | ✅ **FIXED 22 Oct.** `polish.speech_mask` crashed on empty or very short audio (`IndexError`) | **High for the demo.** One mis-pressed take under 20 ms makes `polish --all` die part-way, and the founder re-records blind | Reproduced: empty array and a 1-sample array both raise |
| **B2** | `tests/test_mac_handsfree.py` **cannot run** - it imports pytest, which is not installed and is in no dependency file | Medium. 1 of 5 test files is dead weight, and nobody would know | `ModuleNotFoundError: No module named 'pytest'` |
| **B3** | **There is no dependency file at all** - no `pyproject.toml`, no `requirements.txt` | Medium. The environment cannot be rebuilt on another machine, which blocks the Windows port and any second developer | `ls` finds neither |
| **B4** | **The app has crashed 4 times in a week and nothing reports it** | Medium. Found only by grepping a log nobody reads | 4 distinct `libc++abi: terminating` entries: a missing `bridge` attribute, an `UnboundLocalError` on `subprocess`, a duplicate Objective-C class, and the `re.error` above. Three look already fixed; none has reproduced today |
| **B5** | **Kept audio grows without limit** - 202 MB already, about **31 MB a day** | Medium, and rising. There is no cap and no cleanup | 194 files over 6.9 days |
| **B6** | ✅ **FIXED 22 Oct.** 7% of dictations silently went to the clipboard instead of being typed | Medium UX. The pill says "copied", but if it is missed the words are only on the clipboard | 8 of the last 120 dictations ended `copied` |
| **B7** | The log **never rotates** - 9,378 lines, 492 KB | Low, but it is the only record of a crash | - |
| **B8** | PortAudio prints warnings and errors even when the microphone works | Low. Noise that hides real faults | 10 AUHAL warnings, 5 "Invalid Property Value", 2 `-9986` |

---

## The plan

Ordered by what actually hurts, not by what is easy.

| # | Fix | Size | Why this order |
|---|---|---|---|
| 1 | **B1** - guard `speech_mask` and `tighten` against short or empty audio, and make `polish --all` skip a bad file with a message instead of dying | 20 min | It is the only one that can bite during the demo, which is the next thing happening |
| 2 | **B6** - when the words go to the clipboard, say so where it cannot be missed: the card already appears, so give it the word "copied - press Cmd V" | 30 min | Silent fallback is the kind of thing that makes someone think the app is broken |
| 3 | **B5** - a size cap on kept audio with the oldest deleted first, and the number shown in Settings | 1 h | 31 MB a day needs no decision to become a problem |
| 4 | **B3 + B2** - a `pyproject.toml` with the real dependencies, pytest among them, and one documented command that runs every test | 1 h | Blocks the Windows port and a second developer; also makes B4 findable |
| 5 | **B4** - write an uncaught exception to a crash file and show it once on the next start | 1 h | Four crashes in a week should not need a human grepping a log |
| 6 | **B7** - rotate the log at 5 MB, keep two | 20 min | Cheap, and protects the only crash record there is |
| 7 | **B8** - send PortAudio's own chatter to the log only, not to the user's output | 30 min | Last: it is noise, not breakage |

**Not in the plan on purpose:** the pill's size and position. It works; whether it should be bigger is the
founder's judgement, not a bug, and changing it the day before a recording is the wrong moment.

**Total: about 4.5 hours.** Items 1 and 2 are the ones worth doing before the demo.


---

## Fixed before the demo (22 Oct)

**B1 - polishing no longer dies on a bad take.** Two crashes, not one: `speech_mask` raised on anything shorter
than a 20 ms block, and `tighten` raised on an empty array - the second only showed up once the self-check
actually ran the short cases. A take that short is all speech or all nothing, so it is now kept whole. On top of
that, `--all` catches a failure per file, carries on, and says at the end which takes still have only their raw
version and the exact command to record them again. Proven with a deliberately broken run: a good file, an empty
one, a 4 ms one and another good one - both good files were tidied, both bad ones were named, and the run
finished.

**B6 - the clipboard fallback says so.** The explaining card existed but only appeared if "Show the words" was on,
and it is off by default - so in the one case where the words are *not* where the person is looking, nothing was
said. Smart mode falling back to the clipboard now opens the card for itself, whatever the setting, reading "No
text box here, so it is on the clipboard - paste with ⌘V." Choosing "copy" in Settings stays quiet, because that
was asked for. Checked on screen.
