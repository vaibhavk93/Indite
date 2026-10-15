# indite for Mac: what to build, and why

What the Mac app does today is in `mac/README.md`. This file holds the comparison with the Android app and with
Wispr Flow, and the critic-reviewed plan that came out of it. Update the plan's status column as things land.

Founder request (15 Oct): *"add all the capabilities we added in the android app in mac app as well + check
wisprflow's features and the user flow and UX flow and improve the app."*

---

## 0. Roadmap at a glance (15 Oct, 19:00) — the founder's three tables

### Done (built, committed, running)

| Area | What works |
|---|---|
| Dictation | Hold a key anywhere; hands-free (pick the key, 2 or 3 taps); Esc cancels; ⌃⌘V types the last one again; password boxes never typed into; long holds cut at quiet points; mic fallback + picker |
| Accuracy | Hinglish spelling (punctuation bug fixed), numbers → digits, junk from short taps dropped, Dictionary (word fixes). Clean set 19.9% → 14.4% words wrong |
| Pill | Liquid Glass, transparency slider (now in the right direction), two-tone border, writing animation, REC timer, shows over full-screen apps |
| Window | Dictations · Meetings · Files · To do · Dictionary · Settings (6 sections + finder) · Help; “…” menu on every note; Light / Dark / Like the Mac; drag strip; real full screen; never blank (reloads itself) |
| Notes | Stars, To do page (add, done), delete with Undo, filters |
| Files | Transcribed inside the app; Text and Subtitles export |
| Meetings | Mic (You) + the call's sound (Others), text at each pause, saved as it goes |
| Speakers | Who spoke: 59/60 turns on clear voices, 56/60 similar; rename |
| AI | 9 actions incl. Improve (original kept); from your Claude login or an API key (Anthropic / OpenAI / OpenRouter, in the Keychain); off by default for new users |
| Backup | All / starred / starred + to-do, with or without audio; restore adds only what is missing |
| Setup | First-run screen; Screen Recording asked once |
| Sharing | `mac/build_share.sh` → self-contained `indite-mac.zip` (624 MB), tested in a bare environment |

### Pending (needs doing or checking before it is "done")

| # | Item | Status | Who |
|---|---|---|---|
| P1 | Your boss tries the zip | Ready to send | You |
| P2 | Meeting recording with the call's sound, in a real call | **Permission NOT granted to indite** (log says False) — turn it on, then test | You, then me |
| P3 | Dropped ends of sentences | **Measured: mostly not real.** 48 of the 58 "dropped" words are one test sentence repeated 6 times (the model stops after "Bhej diya." when timestamps are off); most of the rest are faults in the long test file's timings and audio. A detect-and-retry fix recovers it (0 false triggers in 360 clips) but gains ~1 word and can add junk on broken audio. **Not built** - parked unless real dictations show drops | Me, if it shows up in real use |
| P4 | Settings / UI: what exactly still feels bad | Width and slider fixed; need your specifics | You |
| P5 | Real-use check: full screen, drag, hands-free over Terminal, ⌃⌘V | Fixes shipped, unconfirmed | You |
| P6 | Live clean-up while dictating (local model) | Needs a 30-dictation Hinglish test | Me |
| P7 | Signed + notarised build (no "right-click → Open") | Needs a $99/yr Apple Developer ID | You decide |
| P8 | Paytm: ownership, infosec review, AI data policy (your Claude login is a Paytm account) | Not started | You (HR/Legal) |
| P9 | Android: nothing from today's Mac work is on the phone yet | Not started | Later |
| P10 | Intel Macs | The build is Apple Silicon only | Later |

### Future (after this app is finished)

| Idea | What it would be | Must be true first |
|---|---|---|
| Personal assistant | Search your own notes, "what did I promise X", a daily brief, act on what you say ("Slack par Vaibhav ko message daalna", sent only after you confirm) | Fewer wrong words; notes kept long-term (done); speaker names (done); an approved AI route |
| Live AI clean-up | Wispr-style backtrack and filler removal while you dictate, original kept | P6 passes |
| Snippets and styles | Spoken shortcuts, tone per app | Asked for by real users |
| Phone ↔ Mac | The same notes on both | A sync design that keeps "nothing leaves your devices" |
| Windows | The same app on Windows | Mac stable; a Windows PC to test on |
| Other Indian languages | Beyond Hinglish | Tester demand |

---

## 1. Android → Mac, capability by capability (verified in code, 15 Oct)

★ = founder's personal build only. "Python" = reusable code already in the `indite/` package (the web/CLI app,
which is not the Android app, so reusing it keeps Android and Mac separate).

| Android capability | On Mac? | Python has it? | Mac equivalent / note | Port (h) |
|---|---|---|---|---|
| **Dictation** | | | | |
| Voice keyboard, floating bubble, quick tile | yes, as hotkey + pill | — | Phone-only UI; the hotkey and pill are the Mac version | — |
| Type into the box you were in ★ | yes | — | Typed letter by letter, clipboard untouched | — |
| Hold to cancel | yes (Esc) | — | | — |
| Clipboard fallback, copy last | yes | — | | — |
| Each dictation saved as a note with audio | partial (text only, last 500) | — | | 3 |
| **Recording & notes** | | | | |
| Long recording, text after each pause, crash resume | no | partial (`core.cut_at_pauses`, `local`) | | 10 |
| Import / share an audio file | no | **yes** (`core.transcribe`, web upload) | Drop a file | 4 |
| Notes list: titles, rename, delete with Undo | partial (history) | partial (web job list) | | 8 |
| Play one paragraph | no | partial (web `/audio`) | | 2 |
| **Speakers**: guess count, confirm, label, fix, merge | no | no | Phone recipe (Silero + TitaNet + k-means) | 16 |
| **AI actions** (needs an AI route) | | | | |
| One "Do something with this" sheet, 10 actions | no | partial (`notes.py` via your own `claude`/`codex`) | Own Claude login works on the Mac without a key | 6 |
| Action items as rows (calendar, remind, share, done) | no | no | | 5 |
| Rewrite chips ("say this calmly") | no | no | | 3 |
| **Editing** | | | | |
| Edit a paragraph, undo/redo, back to original | no | yes (web editor) | | 3 |
| Retry one part | no | no | | 2 |
| Flags on likely-wrong text | partial ("nan" only) | **yes** (`guards.py`) | | 1 |
| Word fixes + "Always fix?" learning | partial (file, no learning) | no | Mac cannot see edits made in other apps | 2 |
| Hinglish spelling | yes | — | own copy in `mac/spelling.tsv` | — |
| **Reminders** on the alarm stream | no | no | Phone-only sound path; Mac would use notifications | 4 |
| **Export / backup**: SRT, backup zip + restore, export all | no | **yes** for SRT/VTT (`styles.py`) | | 1–4 |
| **Safety**: password / OTP box guard | **no — a real gap** | no | Mac types into password fields today | 1 |
| Privacy: no internet, no cloud backup | yes | — | | — |
| Theme | yes (follows the system) | — | | — |
| Stats | yes | — | | — |
| Onboarding "Try it now" | partial (Help page) | — | | 2 |

---

## 2. Wispr Flow on the Mac (researched 15 Oct, mostly from docs.wisprflow.ai)

**First run, in order:** sign in → microphone permission → Accessibility permission (each a card with Allow that
opens the right System Settings page; granted steps are skipped) → mic test with live bars → pick the shortcut and
push-to-talk or hands-free → languages → practice in a fake app window → data choice → the main window ("Flow Hub").
The floating bar stays hidden until setup is finished.

| Everyday action | Wispr default |
|---|---|
| Hold to talk | fn |
| Hands-free | double-tap fn within 0.5 s, or fn+Space, or click the bar; same again stops; 20-min cap, warning at 19 |
| Cancel | Esc, or X on the bar |
| Paste last / copy last | ⌘⌃V / ⌘⌃C |
| Feedback | a ping when recording starts; bar shows resting / recording / processing |
| Text in | pasted via the clipboard, which is then restored |

**Features:** dictionary with auto-learn from your edits; snippets (spoken trigger → up to 4,000 characters);
styles by app group (English only); cleanup level (None / Light / Medium — "High" removed after complaints);
backtrack ("scratch that", "actually"), spoken punctuation, lists; command mode (paid, experimental); "press enter";
scratchpad (⌥S floating notes); stats with streaks; ranked microphone list; settings split into General, System
(launch at login, bar, Dock), Account, Billing, Data & Privacy.

**What users complain about** (second-hand, some from competitors): the bar covered buttons like Gmail's Send (made
movable after 700+ survey replies); cleanup rewriting what was said; privacy (screenshots of the active window;
cloud only); added itself to login items; ~800 MB memory when idle.

**What indite already does better:** offline and private; Roman Hinglish as one language (Wispr picks one language
per dictation); typing without touching the clipboard; a pill that never takes focus or clicks.

Sources: docs.wisprflow.ai articles on setup, first dictation, hands-free, shortcuts, flow bar, dictionary, snippets,
styles, auto cleanup, smart formatting, command mode, multiple languages, scratchpad, usage stats, audio devices,
app navigation; digitaltrends.com, eesel.ai and spokenly.app reviews.

---

## 3. Founder's requirements (15 Oct, evening) — the list that now drives the Mac app

**The founder overruled the earlier "drop" verdicts: every item below is wanted.** Section 4 (the first plan) is kept
for its technical catches. Status: ✅ done · 🧪 done, founder to check · 🔨 next · 📋 planned · 💬 answered.

| # | Requirement | Status | Notes |
|---|---|---|---|
| R1 | Pill more translucent, towards transparent | ✅ | Liquid Glass *Clear* style |
| R2 | Pill border, so it never merges with a same-coloured background | ✅ | Two-tone rim (dark outside, light inside) |
| R3 | Animation while it is writing | ✅ | Dots in a wave + an orange glint sweeping under the word |
| R4 | Drag the window (not in full screen) | 🧪 | Invisible strip along the top; double-click zooms |
| R5 | Full screen | 🧪 | Fixed: its own Space, no gaps (indite becomes a normal Dock app while the window is open) |
| R6 | Password guard | ✅ | Founder checked it on emergent.com: works |
| R7 | Hands-free: double-tap to lock | 🧪 | Tap to finish, Esc cancels, 15-min cap, red dot in the pill. 5 logic tests |
| R8 | Paste-last shortcut | 🧪 | ⌃⌘V types the last dictation again |
| R9 | Start sound | 🧪 | Tick on start, pop on stop; Settings → Sounds |
| R10 | Mic picker | 🧪 | Settings → Microphone; remembered by name |
| R11 | Transcribe files inside the app, not the web page | ✅ | PyAV + the loaded engine; 230 s in ~30-50 s; Text and Subtitles export |
| R12 | Notes that are kept, with stars | ✅ | Starred, to-do, file and meeting notes are never capped or cleared; delete has Undo |
| R13 | Mark things as action items, and a separate section to see them | ✅ | ○ mark on any note, To do page (open, then done); AI action items → To do in one click |
| R14 | Meeting recording | 🧪 | Mic (You) + system audio (Others) via ScreenCaptureKit, text at each pause, saved as it goes, both tracks kept. **Needs Screen & System Audio Recording permission** — untested with it granted |
| R15 | Speakers ("who spoke") | ✅ | 59/60 turns on clear voices, 56/60 similar; files: Who spoke?; meetings: Others split automatically; rename. Each turn starts 0.4 s early so its first word is not clipped |
| R16 | AI like the Android app | ✅ | ✨ on each note: 9 actions via your own `claude` login, asked once before text leaves the Mac |
| R17 | "Improve my wording", original and improved both kept | ✅ | After the fact (~6 s); live clean-up still needs the local-model test |
| R18 | Backup with options: starred or all, with or without audio | ✅ | Settings → Backup; restore adds only what is missing; optional per-dictation audio |
| R19 | First-run setup screen | ✅ | Accessibility, mic, key, try it; Help → Run setup again |
| R20 | Install on someone else's Mac (e.g. a boss) | 💬 not yet | Needs bundled Python + model, Developer ID ($99/yr), notarization |
| R21 | Can Paytm commercialise it? | 💬 | Licences allow it; ownership, infosec and DPDP questions are Paytm's to answer |
| R22 | Personal-assistant direction | 💬 later | Roadmap only, after the current apps are complete |
| R25 | Check the pill animation ("typing / typed in / writing" looked off) | ✅ | The orange line under "writing" crossed the g and jumped; the shadow blurred "✓ typed in"; states cut in abruptly. Now: dots on the baseline, orange tick, no shadow, each word fades in and settles (0.2 s). Checked frame by frame on light and dark |
| R26 | Is it capturing properly? | ✅ checked | Log of 15 Oct: 76 s → full text in 8.4 s, 58 s in 5.9 s, short ones ~1 s; password guard dropped 3. Misheard: "vishvash flow" (Wispr Flow), "Pace last" (paste last), "holder" (folder), "diary / Diairization" (diarization) — word fixes can take these |
| R27 | Keep this whole list and every answer in one document | ✅ | This file |
| R28 | Choose the hands-free key and the number of taps | 🧪 | Settings: same key or another; 2 or 3 taps |
| R29 | Pill even more transparent | 🧪 | Glass and drawing separated; Settings → Pill transparency slider (default 45%) |
| R30 | Find error patterns in real transcriptions and plan fixes | ✅ | ~⅓ of "19% wrong" was spelling or digits. Fixed: punctuation bug in the spelling list, numbers → digits, junk from short taps. Clean set 19.9% → 14.4%. Analysis: docs/research/mac_errors_2026-10-15.txt |
| R31 | Show or hide the place where the written words appear | ✅ | Settings → Look & sounds → Show text after dictating. Multi-line, grows with the text, stays 4–15 s |
| R33 | Text card: multi-line, dynamic height | ✅ | Was one line + "…" |
| R34 | Opening indite again should show it | ✅ | Window appears on every activation |
| R35 | Demo video with a voice-over | 💬 | Possible; see answer |
| R36 | Test cases for the founder, in a doc | ✅ | `docs/MAC_TEST_PLAN.md` |
| R37 | Who spoke runs by default | ✅ | Files ≥20 s and every meeting; switch in Settings → Writing |
| R38 | Full screen: top bar unusable; Close/Minimize dead after leaving | ✅ | App menus added; policy switch moved to app-level focus |
| R39 | Pill glass froze while scrolling; slider not useful | ✅ | Live glass + tint; 10 % steps, −/+, value shown, pill previews |
| R40 | Insights page like Wispr Flow | ✅ | Sidebar → Insights |
| R42 | Remove stats from Dictations | ✅ | Insights has them |
| R43 | Sidebar: drop “Ready · works offline”; Settings and Help at the bottom | ✅ | |
| R44 | A logo | ✅ | `mac/brand/logo.svg`, app icon |
| R45 | Shortcuts / pill dead after a settings change | ✅ | Listener switched off by macOS; now restarted and kept fast |
| R41 | A real run-time demo video with voice-over, made alone | ⏳ | Built and run twice: hotkeys, typing, hands-free, AI, file + speakers all worked live. **Blocked:** Screen & System Audio Recording is not granted to indite |
| R32 | Keep saving progress | rule | Commit after each feature; docs in the same session |
| R23 | Finish the Mac and Android apps before new directions | rule | |
| R24 | Think from first principles; do not just drop things | rule | |

### What is built and what is only planned (honest status, 15 Oct 18:00)

| Built and running | Built, needs a real-world check | Not built yet |
|---|---|---|
| Pill (glass, border, animation), password guard, notes with stars, To do, files in the app, AI on notes, improve-with-original, speakers, backup/restore, setup screen, accuracy fixes | Drag strip, full screen, hands-free key/taps, paste last, sounds, mic picker, meeting recording with the call's audio, show-the-words card | Shareable signed build (R20); live clean-up while dictating (needs the local-model test); personal assistant (later) |

**Build order:** phases 1–5 were built on 15 Oct (notes, files, meetings, speakers, AI, backup, setup). Next:
phase 6, a shareable signed build — and the real-world checks in the middle column above.

## 4. The first plan (critic-reviewed, 15 Oct)

**The critic's main point: "all Android features on the Mac" is the wrong goal.** Android is a notes app plus a
keyboard; the Mac app is a hold-to-talk tool. The web app (`indite serve`, `indite/web.py`) already does files,
long recordings, an editor with undo, SRT/VTT export and "Copy for Claude" — and it never reads `android/`. What
would make daily use better is fewer wrong words (still ~19%) and whatever the founder actually misses from Wispr.

| # | Item | Verdict | Status | Why / the catch |
|---|---|---|---|---|
| a | **Password-box guard** | Build now | ✅ built | Password boxes are `AXTextField` with subrole `AXSecureTextField`; checked in every output mode. Dropped, not copied, not saved. macOS "secure input" is *not* used as a signal: Terminal and password managers leave it on |
| m | **Fix a word from history** | Build now | ✅ built | Pencil on each row → "indite wrote / you meant". Shows how many past dictations hold the word, warns when it is a lot. Inline form, because WKWebView ignores `prompt()` |
| h | **Transcribe a file…** | Build now, as a link | ✅ built | Menu item and Home button start the web app on 127.0.0.1:8000 (its own process, ~2 s) and open it. Keeps torch out of the always-on app |
| e | Launch at login | No code | ✅ Help line | A LaunchAgent running Python would lose the Accessibility permission; Login Items → `indite.app` keeps it |
| b | Hands-free (double-tap to lock) | Ask the founder | ⏳ | Not asked for yet. A 10-min take means one big block of text ~70 s later. Reopening the mic on Bluetooth clips the first words |
| f | Start sound | Later | — | The pill already shows it; the beep would be recorded; late on Bluetooth |
| d | Microphone picker | Later | — | The fallback fixed the real crash. **Known bug if built:** device list read once at startup; `preferred` stores a position number that can change after a reconnect — store the name |
| i | AI actions (own `claude` login) | Ask the founder | ⏳ | Seconds per answer, uses the plan's quota. **A Finder-launched app has a bare PATH, so `claude` in `~/.local/bin` is not found** — the launcher must set PATH |
| c | "Type last again" shortcut | Drop | — | Copy last + history copy cover it; the keys would also reach the front app |
| g | First-run setup screen | Drop for now | — | One user, already set up. Build it when the app becomes shareable (Wispr's order: mic → Accessibility → mic test → shortcut → practice) |
| j | Meeting recording | Drop | — | Mic only (Zoom audio needs ScreenCaptureKit); the web app covers recordings |
| k | Speakers | Drop | — | ~16 h for a dictation tool; web app later if anywhere |
| l | Backup | Drop | — | History is one small file; recordings are deleted |

Not porting, by earlier decisions: bubble, keyboard, alarm stream, heat pause (phone-only); styles per app and
streaks (ROADMAP); press enter (misfires); command mode (no AI route); snippets (word fixes cover it); backtrack and
spoken punctuation (unproven with Hinglish).

**Open questions for the founder:** what do you actually miss from Wispr? Do you speak for over a minute at once?
Do you transcribe files on the Mac? Would you use rewrite/translate on short dictations, given the wait and quota?

---

## 5. Answers and opinions (15 Oct, critic-reviewed)

### Meeting recording: what Android does, what the Mac needs
Android records a long conversation, turns each piece into text at every pause (the text grows during the meeting),
saves it as a note with the audio, and can label each sentence with a speaker. On a Mac in an online call, the
other people come out of the headphones, not into the mic, so a mic-only recording hears only you.

| Option | Gain | Cost |
|---|---|---|
| Mic only | No new permission | With headphones, everyone else is lost |
| **★ Mic + system audio** (ScreenCaptureKit, or a Core Audio tap on macOS 14.2+) | Hears everyone; two tracks give "me / them" for free | Screen Recording permission; macOS 15 asks again monthly; without headphones, others are heard twice |
| BlackHole driver | Works on older macOS | Install a driver, volume keys stop working; GPL, cannot be bundled |

⚠ Tell people they are being recorded; check Paytm's rules on recording calls.

### To-do / action items section
Build it small: a "to do" mark on any note or line, a **To do** page listing them with a Done tick. No due dates or
reminders on the Mac (the roadmap rules out becoming a to-do app). Same field name as Android (`todo: open|done`) so
a backup can carry it, no shared code. Unproven: whether the list gets cleared or turns into clutter.

### Improve my wording, original kept
A button per note, after the fact: one AI call, the improved version saved beside the original, which is never
overwritten. Not live: the only AI route (your own `claude` login) takes seconds and uses plan quota. Wispr removed
its strongest clean-up after users said it rewrote their meaning; with ~19% words wrong, a polished version can hide
the errors, which is why the original stays. Live clean-up with a small model on the Mac (~1 s) is **unproven for
Roman Hinglish**: test on 30 real dictations first. ⚠ AI sends the text off the Mac — check Paytm policy if the
login or the content is Paytm's.

### Personal assistant (later, roadmap only)
Concretely: search your own notes, "what did I promise X?", a daily brief, and acting on what you say — e.g. "Slack
par Vaibhav ko message daalna ki woh ho gaya kya" (founder's example, 15 Oct: draft the message, improve it, send it
after you confirm). First must be true: fewer wrong words (a brief on 19% errors cannot be trusted), notes kept
long-term (phase 1), speaker names (phase 3), an approved AI route. Cheapest first step: offline search across notes.
Cost to weigh: it means keeping everything you say.

### Can someone else (a boss) install it? Not yet
It runs Python and the model from this folder. Needed: Python bundled into the app (py2app or PyInstaller), the
574 MB model inside or downloaded on first run, an Apple Developer ID ($99/yr), every library signed and the app
notarized. Without it macOS blocks the app. ⚠ A Paytm-managed Mac may block an app with keyboard, mic and screen
permissions (it looks like a keylogger): expect an infosec review.

### Can Paytm commercialise it? (not legal advice)
Licences allow it: the Hinglish model (Apache 2.0), whisper.cpp (MIT), most libraries MIT/BSD; pynput is LGPL (fine
unmodified, ship its licence); **TitaNet (speakers) has no licence noted in the repo — verify** (NVIDIA models are
usually CC-BY-4.0, credit needed). The bigger questions are Paytm's: who owns a side project built by an employee
(contracts often give the employer work related to its business or made on its equipment/accounts); the public repo
with no LICENSE; DPDP notice and consent if AI features send personal data out; an infosec review. Ask Paytm
HR/Legal first.

