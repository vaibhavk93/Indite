# End-to-end audit, 24 Oct 2026

Founder asked (24 Oct): test everything end to end (run time, positive cases, negative cases, other use cases), write the
audit down, fix what it finds, then commit. This is that audit. It covers everything built or changed on 24 Oct:
search / filter / sort / group on every list, Find in one transcript, Delete choices, How many to keep, the card, AI cost,
model and effort, rupees, the Dictionary, saving, and the founder's own bug reports from that day.

**Method.** (1) Read the code and the design rules (`docs/DESIGN.md`). (2) Ran the real `mac/ui/app.html` in headless
Chrome against made-up notes: 13 UI scenarios, about 83 checks (`tests/test_lists_ui.py`). (3) Ran the real Python in the
hidden test copy (own data, nothing on the founder's screen): save, the three delete choices with Undo, a review decision,
a walk through every screen. (4) Measured 25,800 made-up notes (25,000 dictations + 800 meetings, 33 MB) and the
founder's real notes (read-only, counts only). (5) Looked at light, dark and narrow-window renders.

**Result.** 39 findings (36-39 from the founder's live checks, 24 Oct evening), all fixed (39 awaiting a live check); 61 automated tests + 131 real-app end-to-end checks pass; 0 JavaScript or Python errors
across every screen. **Second pass (same day, after the founder found two bugs the first pass missed):** the first tests
checked what the page's data said, not what the screen showed. They now check real visibility (computed display and size)
and invariants that must hold for any state (see section 7).

---

## 1. Findings and fixes

Severity: **H** loses or hides data, or blocks use · **M** wrong result or a confusing screen · **L** polish.

| # | Sev | Area | What was wrong | Found by | Fix | Test |
|---|---|---|---|---|---|---|
| 1 | H | Saving | Dictations spoken while indite's own window was in front, no box focused, were never saved (3 lost) | Founder | Always save; the page tells Python when a box has the cursor (typing vs clipboard only) | live-checked by founder |
| 2 | H | Saving | New dictation recordings were deleted the moment they were saved (starred audio filled the 500 MB cap) | Founder | The cap counts only audio that can be dropped | `store.py` check |
| 3 | H | History | The app keeps only the newest **500** plain dictations: 2-3 years of history could not exist | Scale audit | Setting "How many to keep": 500 / 5,000 / Everything, asks before deleting | UI test, `store.py` |
| 4 | H | History | A crash could leave the last line of the history file without its newline; the next saved note would be glued onto it and lost | Negative case | `add()` writes a newline first when needed | `store.py` check |
| 5 | M | Speed | Saving one dictation rewrote the whole file (465 ms at 25,800 notes) | Scale audit | Append one line (0 ms) | `store.py` check |
| 6 | M | Speed | Notes were re-parsed on every read (175 ms) | Scale audit | Parsed-rows cache (8 ms) | `store.py` check |
| 7 | M | Speed | Every update checked the disk once per note for its recording (408 ms at 25,000) | Scale audit | One directory listing (48 ms) | measured |
| 8 | M | Speed | "Longest first" re-counted words in every comparison (673 ms) | Scale audit | Measure once per row (133 ms) | measured |
| 9 | H | Search | Curly quotes (“like this”, from dictation and macOS) returned **nothing** | Founder ("search with quotes/codes") | Curly and single quotes count as quotes | `test_search_words_quotes_codes_and_symbols` |
| 10 | M | Search | Accents were not matched (`cafe` missed `Café`) | Negative case | Capitals and Latin accents ignored; Hindi letters untouched | same |
| 11 | M | Search | "Best match" ignored how many times a word appears | Sort test | Counts every mention (title most) | `test_search_best_match…` |
| 12 | M | Lists | A saved filter that no longer exists (an app you stopped using) made the list **blank** | Negative case | Ignored, never a blank list | `test_filters_when_app_review…` |
| 13 | L | Lists | The When menu said "Any time" while a time filter was still on | Review | Shows the real choice | same |
| 14 | M | Lists | Date groups with Title A–Z / Longest / Shortest gave a confusing order | Sort test | Date headings only when sorted by date; picking Group by date switches to Newest | `test_sort_group_and_windowing` |
| 15 | M | Meetings | A meeting that matched a search showed its first 6 lines, so you could not see why | Review | Shows the matching lines | `test_meetings_files_todo_dictionary` |
| 16 | M | Settings | "How many to keep" listed **Everything** first (numeric keys reorder in JavaScript) | Settings test | Keys keep their order | `test_how_many_to_keep…` |
| 17 | M | Design | Filters and sort used system dropdowns, off-theme (`DESIGN.md`: own `popup()` menus) | Founder | Own menus, chip-like buttons, filled when active | `test_toolbar_uses_our_menus…`, renders |
| 18 | M | Design | "How many to keep" used a dropdown plus an inline warning, off-theme | Founder | `.seg` + `.banner` | same |
| 19 | H | Delete | Deleting a note never asked whether to delete the words, the recording or both | Founder | "Delete what?" with three choices, each with Undo; recordings go to a trash folder first | `test_delete_asks…`, test copy |
| 20 | M | Review | No way to find notes by Fix / Always fix / Not a mistake | Founder | Mistake review menu; each decision is kept on the note | `test_filters_when_app_review…`, test copy |
| 21 | L | Dictionary | A fix that only changes capitals (jira → Jira) was refused as "the same word" | Founder test | Allowed; applies the exact capitals | `store.py` check |
| 22 | H | AI | AI review with an API key was broken since the cost change (`_api` returns two values) | Code read | Fixed | import + selftest |
| 23 | M | Search | Searching inside one long meeting transcript was not possible | Founder | Find box in Listen: lit lines, marks, ↑ ↓ / Return | `test_find_inside_one_long_transcript` |
| 24 | L | Docs | The quote rule was not discoverable | Review | Search hint tooltip + Help "Find things" | Help text |
| 25 | H | Lists | **A number on a button or menu did not match the list** ("Terminal · 318" showed 6 notes): counts ignored the other filters that were on, and an empty list did not say why | Founder | Faceted counts (each number is what you get by choosing it with every other filter as it is now); empty options dimmed; "n of total · Copied · Claude  Clear" names every filter; "No note is all of these: …" | `test_every_number_on_every_button_and_menu_matches_the_list` (260 notes, 46 states, every option); same check on the founder's real notes: 61 states, 0 mismatches |
| 26 | H | Settings | **The "keep N" warning came back every time** you switched Settings section: it was a row, and the Settings page un-hides every row on switching | Founder | The warning exists only while a choice is waiting, is dropped when you leave the section or page, and never was a hidden row | `test_keep_limit_question_is_asked_once_and_never_comes_back` |
| 27 | M | Settings | The waiting warning showed no title and its Delete button was a black pill in red text | Screenshot | Title says how many would go; button matches the other danger buttons | screenshot |
| 28 | M | Lists | A damaged saved view (wrong types, unknown values) **crashed the page** | Negative case | Every saved choice is checked and falls back to the default | `test_a_choice_survives_the_round_trip_through_python`, e2e |
| 29 | H | Dictation | **Two seconds of silence became a saved note reading "KKK"** (the engine invents words for silence; the junk filter only looked at sounds under 1 s) | End-to-end run | Silence is never sent to the engine; one repeated letter is never a note at any length | selftest, e2e section 1 |
| 30 | M | Lists | "Clear" was cut off when the filter description was long | Screenshot | The description shortens; Clear always shows | screenshot |
| 31 | L | Lists | A pressed button looked almost like an unpressed one | Review | Stronger pressed state | screenshot |
| 32 | M | Settings | A note's words-only delete and other states showed no on-screen proof in tests | Review | Tests now check computed visibility everywhere | `test_the_right_things_are_visible…` |
| 33 | L | Tests | My test page broke when a note contained `</script>` (a test-only problem; the app passes data differently) | Hostile-data test | Escaped in the harness | `test_hostile_notes…` |
| 34 | L | AI | An AI action the app does not have raised an error (and would have shown the consent dialog first) | Real-app run, section 11 | Unknown actions are ignored before anything is asked | e2e section 11 |
| 35 | M | AI | **"Action items → To do" created nothing, silently, when the AI answered with a plain list instead of the table the prompt asks for** | Real-app run, section 11 | Plain bullet and numbered lists work too; prose and "none" create nothing | `mac/ai.py` check, e2e section 11 |

| 36 | H | Backup | **Restore said "everything is already here" after a delete**: it skipped any note whose id existed, and Delete → words only (or recording only) leaves the note behind, empty | Founder, live | Restore refills a note that lost its words, and a recording that is missing; a note deleted completely comes back as before. A second restore still changes nothing | `store.py` self-check, `tests/e2e_keep_restore.py` |
| 37 | H | Keep limit | **"Delete them" did not delete**: it saved the setting, and the old dictations were cut at the next dictation, so 519 stayed 519 | Founder, live | The limit applies at once, with the recordings of the dropped notes; banner text says so | self-check, `tests/e2e_keep_restore.py` (519 → 500 on the real page) |
| 38 | M | Backup | Restoring old plain dictations while the limit is lower said "Restored N" and the limit dropped them again | Found while fixing 36 | Counted honestly: "N older dictations not kept: over your keep limit" | self-check, e2e |
| 39 | H | Esc | **Esc did not cancel a dictation in two live tests** and the log showed no Esc at all (the key listener never saw it). Likely cause: an app with secure keyboard entry hides ordinary keys from listeners but not modifiers (the talk key is a modifier). Not proven | Founder, live | The paint tick also asks macOS whether Esc is held (10 times a second while listening) and logs `Esc: dictation cancelled (seen by the ...)` | `tests/test_mac_handsfree.py`; **live check pending** |

Also fixed earlier on 24 Oct from the founder's own reports (verified): the To do items not showing (saved as `True`, the
page lists `"open"`), AI cost showing 0 (the Claude login's usage was discarded), the card pickers hidden instead of
disabled, the AI-buttons switch layout, the model setting being ignored for the Claude login.

---

## 2. Positive cases checked

- **Search:** all words in any order; "phrase" in straight, curly, single and « » quotes; codes (`JIRA-123`, `#77`,
  `example.com`, `₹4,500`); symbols (`a+b`, `(x)`, `[y]`, `\path`, `.*`, `?`, `$5`, `^`, `<b>`, `&`); Hindi; capitals;
  accents; extra spaces; a 300-character query; Esc clears; matches marked; the sort follows the search.
- **Filters:** Starred, With AI, To do, Copied, To check; When (today, 7 and 30 days, month, last month, year, a named
  month or year); App; Mistake review (suggestions, Fix, Always fix, Not a mistake); combinations; Clear.
- **Sort and group:** newest, oldest, longest, shortest, Title A–Z, Best match; group by date (Today, Yesterday, weekday,
  month with year), by app (largest first), none; the sort inside groups.
- **Pages:** Dictations, Meetings (speaker-line search, star filter, title and length sort), Files, To do (Open / Done,
  search), Dictionary (search, 4 sorts, letter headings, empty state).
- **Windowing:** 100 rows, "Show more", the window restarts when the view changes.
- **Find in a transcript:** lines lit, count, next / previous, phrase, speaker name, no match, clear.
- **Delete:** all three choices and Undo in the real Python (recording moves to trash and back; words cleared and
  restored; note and recording together), then purge.
- **Settings:** How many to keep (applies at once when it fits; asks first when it would delete; disabled when saving is
  off); Model and Effort for each provider; Dollars / Rupees with and without a rate.

## 3. Negative and edge cases checked

Empty and whitespace-only queries; lone quotes; HTML in a note (shown as text, never as markup); regex characters; very long
queries; no matches (message and Clear button); stale saved filters; a note with no recording (deleted at once); a
transcribed file (its original is never touched); words already deleted (no second "words only"); a history file with a torn
last line; choosing a smaller keep limit than you have (asks, "Keep them" sends nothing); saving turned off; AI off; an
unknown model; Rupees chosen with no rate typed (stays in dollars, never a guessed rate).

## 4. Run time

Made-up history of 25,800 notes (25,000 dictations + 800 meetings), headless Chrome:

| Action | Before | After |
|---|---|---|
| Page receives the notes and draws | 163 ms | 144 ms |
| First draw of Dictations | n/a (all rows) | 133 ms |
| Search two words | 46 ms | 55 ms |
| A filter or a menu choice | ~80 ms | 78-99 ms |
| Sort longest first | 673 ms | 139 ms |
| Meetings page | 162 ms | 152 ms |
| Python: save a dictation | 465 ms | 0 ms |
| Python: read the notes again | 175 ms | 8 ms |
| Python: recording check for 25,000 notes | 408 ms | 48 ms |

The founder's real notes (about 500): every page loads and filters without errors.

## 5. Known limits (not bugs, not built)

- **The page is sent every note on each update.** At 25,800 notes that is 33 MB, about 250 ms, mostly meeting segments.
  Fine to roughly 10,000 dictations. Beyond that: leave meeting segments out of the update, or page on the Python side.
- **Review decisions made before 24 Oct are not on any note** (the log never said which note), so the Fix / Always fix /
  Not a mistake menu counts only decisions from 24 Oct on.
- The default keep limit is still **500** (a privacy choice). Until the founder chooses Everything, search can only reach
  the newest 500 plain dictations.
- The Models API refresh needs an Anthropic API key (none on this Mac): parsing is tested, a live call is not. Codex is not
  installed here and is not built.
- The card's hover / pressed tint needs a real mouse (tested on a card that is built but never shown).
- Not checked: the Android app (nothing changed there today).

## 6b. Coverage map: what is tested, how, and what cannot be

Founder (24 Oct): "have you tested every feature, all the cases?" Honest answer after the third pass:

| Area | How it is tested | Cases |
|---|---|---|
| Lists: search, filters, When / App / Mistake review, sort, group, windowing, scrolling | headless Chrome on the real page (`test_lists_ui.py`, `test_e2e_screen.py`) and the founder's real notes | words, quotes (straight, curly, single, « »), codes, symbols, accents, Hindi, empty, very long, HTML, no match, stale saved choices, junk saved choices, every number vs the list for 46 states and every option, 25,800 notes |
| Toolbar menus, Find in a transcript, keyboard shortcuts (⌘F, Esc, ⌘, Return) | same | open / close / pick, keyboard, no match, speaker names, phrase |
| Delete (note + recording / recording only / words only) and Undo | page (popup) and the real app (files moved to the trash and back, purge) | with and without a recording, a transcribed file, bad ids, unknown mode, undo with nothing |
| Settings: every switch, the choices, keep limit, rupees, model and effort | page and the real app (prefs.json) | each switch on and back, a bad rate, 0, 2-decimal rounding, damaged keep limit, the warning (drawn only while waiting, gone after leaving) |
| Dictation through the real engine (a recording, silence, a 0.15 s blip, Don't save) | the real app, hidden copy | saved, not saved, switches itself off |
| Row actions, Dictionary, review decisions, combine, to-dos, edit and Undo | the real app | 10 valid and invalid Dictionary entries, bad ids, blank to-do |
| Ask AI (Improve, Summary, remove, Undo, Action items → To do, cost chips in $ and ₹, month total) | the real app with real Claude calls (haiku) | unknown action, unknown note, plain-list answers |
| The card after a dictation (To do, AI button working → answer, Ask AI) | the real app (`card:N`), what it would have shown is read from the log | |
| Files: transcribe, timed lines, edit a line, Undo, Listen, seek, missing and corrupt files | the real app | empty edit, nonexistent line |
| Speech-test marking and the scorer | the real app + `speechset.py --selftest` | |
| Insights numbers | page, against counts worked out by hand | empty history |
| Hostile data (script tags, emoji, right-to-left, 6,000-character words, missing fields) | page | nothing runs, nothing breaks, still searchable |
| Every page opens; click every button on every page; dark theme | page | |
| History file: cap, cache, torn last line, append | `mac/store.py` self-check and the real app | |
| Speed at 25,800 notes (25,000 dictations + 800 meetings, 33 MB) | headless Chrome + Python | every interaction 73-261 ms; the "numbers match the list" check also passes at that size |

**Cannot be tested here (needs hardware or macOS windows), so not claimed:** holding the talk key and the live microphone; the
pill and the card on screen (glass, position, the hover and pressed tints need a real mouse); typing into other apps and the
clipboard fallback; hiding the pill from screen sharing; the "Record this call?" card; live meeting recording (microphone +
system sound); macOS permission dialogs; the Save / Open panels for Backup, Restore and Export; the "Clear dictations"
confirmation; the AI consent dialog (bypassed with `ai_ok`); the Anthropic Models API live refresh (no API key here; parsing
is tested against the docs' example); Codex (not installed); the Android app (nothing changed there today).

## 6a. Second pass: what the first one missed, and why

The founder reported (1) menu numbers that did not match the list and (2) a warning that kept coming back. Both passed the
first tests because those tests read `element.hidden` and the data behind the screen, never what is actually drawn. The
rule now: **a feature is not tested until its test looks at computed visibility, and its numbers are compared with the
rows on screen.** New checks (`tests/test_e2e_screen.py`): every chip and menu number equals the list you get by choosing
it, for many combined states, on invented notes and on the founder's real ones; rows on screen equal the count; the toolbar,
menus and banners are visible exactly when they should be; a choice survives Python's round trip; hostile notes (script
tags, emoji, right-to-left text, 6,000-character words, missing fields) render as text and stay searchable; every page
opens; clicking every button on every page never breaks it; cost chips in dollars and rupees; dark theme.
`tests/e2e_testcopy.py` drives the real app (real Python + real page) in the hidden test copy: 131 checks in 16 sections,
covering dictation (a real wav, silence, a 0.15 s blip, Don't save), star / to-do / edit with bad ids, the Dictionary (10
valid and invalid entries), review decisions, the three delete choices and Undo, combine, preferences (including damaged
ones), the keep limit, a torn history file, every page, real AI calls (Improve, Summary, remove and Undo, Action items,
cost chips, wrong model names), the card's buttons, file transcription, line edits and Undo, Listen and seeking, speech-test
marking, every Settings switch, and the founder's real history compared with an independent count.

## 6. Re-run

```
.venv/bin/python -m pytest tests -q                 # 61 tests, about 2 min (needs Chrome for the UI scenarios)
.venv/bin/python tests/e2e_testcopy.py              # 131 checks against the real app in the hidden copy, about 13 min (real AI calls, a few tenths of a cent)
.venv/bin/python mac/store.py                       # history cap, cache, append, delete choices, Dictionary rules
.venv/bin/python mac/indite_mac.py --selftest       # the app's own checks
```
For the real Python path use the hidden copy: `python mac/testcopy.py start`, drive it with `js` / `eval` / `cmd`, `stop`.
