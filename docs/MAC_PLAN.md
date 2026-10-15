# indite for Mac: what to build, and why

What the Mac app does today is in `mac/README.md`. This file holds the comparison with the Android app and with
Wispr Flow, and the critic-reviewed plan that came out of it. Update the plan's status column as things land.

Founder request (15 Oct): *"add all the capabilities we added in the android app in mac app as well + check
wisprflow's features and the user flow and UX flow and improve the app."*

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
| R5 | Full screen "not working fine" | ❓ | Needs detail: the indite window in full screen, or the pill over another full-screen app? |
| R6 | Password guard | ✅ | Founder checked it on emergent.com: works |
| R7 | Hands-free: double-tap to lock | 🧪 | Tap to finish, Esc cancels, 15-min cap, red dot in the pill. 5 logic tests |
| R8 | Paste-last shortcut | 🧪 | ⌃⌘V types the last dictation again |
| R9 | Start sound | 🧪 | Tick on start, pop on stop; Settings → Sounds |
| R10 | Mic picker | 🧪 | Settings → Microphone; remembered by name |
| R11 | Transcribe files inside the app, not the web page | 🔨 | Possible without torch: decode with PyAV, then the Mac's own `pieces()` + engine |
| R12 | Notes that are kept, with stars | 🔨 | History becomes notes: kept until deleted, starred ones protected |
| R13 | Mark things as action items, and a separate section to see them | 🔨 | A "to do" mark on any note or line + a To do page with Done ticks (critic: keep it a mark, not a task manager) |
| R14 | Meeting recording | 📋 | Mic (you) + system audio (them) as two tracks; text after each pause; needs Screen Recording permission |
| R15 | Speakers ("who spoke") | 📋 | Two tracks give "me / them" for free; splitting "them" needs the phone's recipe (TitaNet: licence to verify) |
| R16 | AI like the Android app (notes, action items, summary, rewrite, translate) | 📋 | Through your own `claude` login; launcher must set PATH. ⚠ text leaves the Mac — check Paytm policy |
| R17 | "Improve my wording", original and improved both kept | 📋 | After the fact, a button per note; live clean-up only if a local model passes a 30-dictation Hinglish test |
| R18 | Backup with options: starred or all, with or without audio | 📋 | Plus restore |
| R19 | First-run setup screen | 📋 | Mic → Accessibility → mic test → key → try it (Wispr's order) |
| R20 | Install on someone else's Mac (e.g. a boss) | 💬 not yet | Needs bundled Python + model, Developer ID ($99/yr), notarization |
| R21 | Can Paytm commercialise it? | 💬 | Licences allow it; ownership, infosec and DPDP questions are Paytm's to answer |
| R22 | Personal-assistant direction | 💬 later | Roadmap only, after the current apps are complete |
| R23 | Finish the Mac and Android apps before new directions | rule | |
| R24 | Think from first principles; do not just drop things | rule | |

**Build order (phases):** 1 · notes with stars, to-do mark and page, files inside the app → 2 · meeting recording
(mic + system audio) → 3 · speakers → 4 · AI actions + improve-with-original → 5 · backup/restore + first-run
setup → 6 · a shareable, signed build.

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
