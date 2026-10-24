# inditeflow for Mac — test plan

Two parts. **Part A** is what Claude tested on its own (15 Oct). **Part B** is what needs you: a real key, a real
microphone, a real call, a real permission prompt, or your eyes. Mark each row ✅ / ❌ and add a note; a ❌ with
"what you saw" is enough for Claude to fix it.

**Before you start:** inditeflow running (🎙 in the menu bar), its window open, and a text box to type into — Notes or
TextEdit is fine.

---

## Part A — tested by Claude (no action needed)

| Area | How it was tested | Result |
|---|---|---|
| Hands-free, hold, tap, Esc, other key, 3 taps | `tests/test_mac_handsfree.py` (7 cases) | ✅ |
| Long holds cut at quiet points, no sound lost | `tests/test_mac_pieces.py`; 60 s hold 75% → 19% wrong | ✅ |
| Word fixes, notes store, stars, undo, clear keeps starred, backup/restore | `python mac/store.py` | ✅ |
| Numbers → digits, and words that must stay words | `python mac/digits.py` | ✅ |
| AI action-item parsing; AI answer through your Claude login (6.6 s) | `python mac/ai.py`, live call | ✅ |
| API key saved / read / removed in the Keychain | live | ✅ |
| Meeting cutting and echo rules; a 75 s simulated meeting | `python mac/meeting.py`, simulation | ✅ |
| Who spoke: 59/60 clear voices, 56/60 similar | `python mac/speakers.py` | ✅ |
| File transcription in the app (230 s → ~30–50 s), subtitles | live | ✅ |
| All 12 window pages open with no page errors | real-window snapshots | ✅ |
| Text card: multi-line, grows with the text | real snapshot | ✅ |
| Shareable build: own Python, engine, models; transcribes | bare-environment run | ✅ |
| Ask AI panel (15 Oct night): beside the list at ≥1180 px, note highlighted, Esc closes menu then panel, own Rewrite/Translate menus, long titles wrap clear of the time, no redraw jumps | real window: page tour + measured layout | ✅ |
| Every page and Settings section opens with no page errors; live AI summary (5 s); file → text in the app (4 s audio, 2 s) | real window + live calls | ✅ |
| Password guard | you, on a website login page | ✅ |

---

## Part B — needs you

**Founder's results so far (15 Oct):** B4/B5 ✅ · B14 ✅ · B14b ✅ · B22 open (later) · B12 → found the shortcuts dying after a
settings change, fixed (key listener restarted, mic work off the key handler).

| # | Test | What to do | What you should see | It failed if… |
|---|---|---|---|---|
| **Dictation** | | | | |
| B1 | Hold to talk | Click in Notes. Hold **Right ⌥**, say a sentence, let go | Pill with moving bars while you hold; “writing” with dots; the words appear in Notes in ~1 s; “✓ typed in” | Nothing typed, or the pill never appears |
| B2 | Short tap is ignored | Tap Right ⌥ quickly once | Nothing typed | Junk like “R.” appears |
| B3 | Esc cancels | Hold Right ⌥, speak, press **Esc**, let go | Pill says “cancelled”; nothing typed | Words get typed |
| B4 | Hands-free | Tap your hands-free key (**Right ⌘**, 3 times) quickly, let go, speak for 30 s, tap Right ⌘ once | Red dot in the pill while you speak hands-free; all 30 s typed after the last tap | Pill missing, or text cut short |
| B5 | Hands-free over full-screen Terminal | Make Terminal full screen, repeat B4 there | The pill shows over Terminal | Pill invisible over Terminal |
| B6 | Paste last | After any dictation, click elsewhere in Notes, press **⌃⌘V** | The last dictation is typed again | Nothing, or odd characters |
| B7 | No text box | Click the desktop, dictate | Pill says “✓ copied”; ⌘V pastes it | Words lost |
| B8 | Password box | Click a password field on any login page, dictate | Pill says “password box”; nothing typed, copied or saved | Anything typed |
| B9 | Text card | Settings → Look & sounds → **Show text after dictating** on; dictate 3–4 sentences | A glass card above the pill shows every line, no “…”; stays a few seconds | One line with “…”, or it vanishes too fast |
| B10 | Sounds | Settings → Look & sounds → Sounds on; dictate | A soft tick when listening starts, a pop when it ends | Silent, or the tick is in the text |
| B11 | Microphone picker | Turn your Bluetooth headset on; Settings → General → Microphone → pick it; dictate. Then turn it off and dictate again | Uses the headset; with it off, falls back to the MacBook mic and still works | An error, or no text |
| **The pill and the window** | | | | |
| B12 | Pill transparency | Settings → Look & sounds → use − / + (10 % steps); the pill shows each time. Then scroll a page under it | 100 % is clear glass, 0 % a solid tint; the background moves under the glass as you scroll | The background freezes, or no change |
| B13 | Drag the window | Grab the very top strip of the window (not full screen), drag | The window moves; double-click there zooms it | It does not move |
| B14 | Full screen | Click the green button; move the pointer to the top; then leave full screen | Its own Space; the top bar shows inditeflow / Edit / Window; after leaving, the red/yellow/green buttons work | Empty top bar, or grey dead buttons |
| B14b | Insights | Sidebar → Insights | Your words, speed, time saved, activity, apps, hours | Empty or wrong numbers |
| B15 | Reopen | Close the window (red button), then open inditeflow from Applications or Spotlight | The window comes back | Nothing appears |
| B16 | Appearance | Settings → Look & sounds → Light / Dark / Like the Mac | The whole window switches, sidebar included | Half light, half dark |
| **Notes** | | | | |
| B17 | Star, To do, delete, undo | On a dictation: “…” → Star; “…” → Add to To do; “…” → Delete, then **Undo** in the black message | Star shows; it appears on the To do page; delete then undo brings it back | Any of these do nothing |
| B18 | To do page | To do → type a task, press Return; tick it | It appears; ticking moves it to “Done” | Not added |
| B19 | Dictionary | Dictionary → add `ptm` → `Paytm`; dictate “ptm se pay karo” | Typed as “Paytm se pay karo” | Still “ptm” |
| B20 | Search | Dictations → ⌘F → type a word you said | Only matching dictations show | Nothing filters |
| **Files and meetings** | | | | |
| B21 | Transcribe a file | Files → Choose a file… → any voice note or call recording | Progress bar; then a note with the text; “…” → Save as subtitles works | Error banner, or stuck |
| B22 | Meeting, with headphones | Start a Zoom/Meet call with headphones; Meetings → **● Record**; talk 2 minutes; **■ Stop** | Lines marked **You** and the other person (**Person 1**…) appear while you talk; after stopping, the others are split by voice | Only “You” lines (then the Screen Recording permission did not take — quit and reopen inditeflow) |
| B23 | Meeting, without headphones | Same, on speakers | Their words appear once (as theirs), not twice | Duplicated lines |
| B24 | Rename a speaker | Click “Person 1” in a meeting, type a name, Return | The name changes on every line | It does not stick |
| B25 | Who spoke on a file | Transcribe a two-person recording (no click) | Lines labelled Speaker 1, 2… a little after the text appears | No labels on a clear two-person file |
| **AI** | | | | |
| B26 | AI on a note | Settings → AI on; on a dictation “…” → AI… → Improve the wording | “Claude is writing” then an **Improved** line under the note (click to open); your original unchanged | Error banner |
| B27 | Action items → To do | On a meeting: AI… → Action items → “Add all to To do” | Each task appears on the To do page | Nothing added |
| B28 | AI off | Settings → AI off | “…” menu shows “AI is off”; nothing is sent | AI still runs |
| B29 | API key (optional) | Settings → AI → Answers come from → OpenRouter (or OpenAI) → paste a key → Save; run B26 | Works through the key | “key was refused” (then the key is wrong) |
| **Backup and setup** | | | | |
| B30 | Backup and restore | Settings → Backup → Starred → Back up…; delete a starred note; Restore… the zip | The note comes back; nothing else changes | Duplicates, or not restored |
| B31 | Setup screen | Help → Run setup again | 4 steps with green ticks for permissions you have; the try-it box ticks when words arrive | Wrong ticks, or stuck |
| **The shared build** | | | | |
| B32 | Your boss's Mac | Unzip `inditeflow-mac.zip`, drag to Applications, **right-click → Open → Open** | Asks for Accessibility and Microphone; first start says it may take a minute; then dictation works | “damaged” message, blocked by company policy, or the engine never becomes ready |

---

## When something fails

Tell Claude the test number and what you saw. If it is about the window, Claude can take a picture of the real
window itself (it writes a tab name into `~/Library/Application Support/inditeflow/snapshot.request`); the log is
`~/Library/Logs/inditeflow-mac.log`.
