# Work log

Newest first. One entry per session: date, who, what changed, what's untested, next step. See `docs/HANDOFF.md`.

---

## 24 Oct 2026 · Critic rule narrowed, model default changed

- **Founder's live checks, 24 Oct evening (3 bugs, fixed; restarted):** (1) **Esc did not cancel a dictation**, and the log showed no Esc event in two tests. Silence, hands-free, card effects and Backup/Restore with identical data passed. I could not prove why (I may not press keys on the founder's Mac); the likely cause is secure keyboard entry in the frontmost app, which hides ordinary keys but not modifiers. Fix: while listening, the paint tick also asks macOS (`CGEventSourceKeyState`) whether Esc is held, 10 times a second, and logs which path saw it (`cancel_listening`, `esc_down` in `mac/indite_mac.py`). **Not proven live.** (2) **Restore said "already here" after deleting an older transcript** (RCA: Delete → words only/recording only leaves an empty note; restore skipped existing ids). `store.restore_zip` now refills a note's words and missing recordings, brings back fully deleted notes, and reports notes the keep limit drops (`restore_zip.over_limit`; message in `InditeApp.restore`). (3) **"How many to keep": Delete them did not delete** (RCA: it only saved the setting; trimming waited for the next dictation). `store.set_pref("history_cap")` now calls `store.apply_cap()` (drops the oldest plain dictations and their recordings at once); banner text changed. Tests: `store.py` self-check, `tests/test_mac_handsfree.py` (Esc check), new `tests/e2e_keep_restore.py` (real page, 519 → 500, restore cases; 17 checks), 62 pytest pass. Answered: Google Meet in a browser records fine by hand; the automatic call card skips browsers on purpose.
- **Bug fixed: new dictation recordings were deleted the moment they were saved** (found while starting the real speech set, Mac next #1). Starred meetings and to-dos hold 891 MB of protected audio; the cap is 500 MB; `store.trim_audio` counted the protected files toward the cap, so it was over the limit for good and trimmed every new, unprotected clip straight away. Only 5 of 442 notes had audio. Now the cap counts only audio that can be dropped (`mac/store.py`); starred audio is still never dropped. Self-check extended: `.venv/bin/python mac/store.py` → `ok`. **Proven live:** after the restart the 4 newest notes all kept their audio. Earlier read-throughs had no audio and cannot be scored.
- **Dictations are now always saved, wherever they are spoken** (founder's decision, 24 Oct, after 3 dictations were lost inside indite and the first fix did not hold live: macOS answers "a box is focused" when unsure, so the words were typed into nothing and not saved). The save-skip is gone (only "Don't save the next dictation" skips). For indite's own window the page now tells Python whether a text box has the cursor (`box` message, `Bridge.handle` in `mac/window.py`, `focusin` in `mac/ui/app.html`, `self.in_box`), and that only decides typing vs clipboard. With no box focused: saved + clipboard + card with its buttons. The card has no buttons only when a note is not saved (that was the second symptom: the card had none for the lost dictation). Tested in the hidden copy: page→Python box message (true/false with a faked active element), card buttons `True` / `"todo"`. **Not proven live:** a real click into a box (the hidden window can't take focus). Self-checks `ok`.
- **Founder's check, 24 Oct (fixed, needs a restart):** (1) the two to-dos did not show on the To do page: I had saved `todo=True`, the page lists only `"open"`; both are now `"open"`. (2) AI cost stayed 0: the founder's AI runs through the Claude login, and `indite/notes.py` threw away the CLI's JSON usage. `notes.last_usage()` now returns the CLI's own model, tokens and `total_cost_usd` (list price) and `ai.run` passes it on; new answers carry a cost chip and count in Insights → AI → "This month". Old answers stay "no cost reported". Test: `tests/test_cli_usage.py`; one real call returned `claude-opus-5-5`, 819 in / 24 out, $0.007. Chip tooltip says "list price; your Claude plan may not charge this". (3) Settings: the card's AI-button rows are indented under "Show text after dictating" and **disabled with a reason instead of hidden** (rendered in headless Chrome in three states). **Found, not changed:** the Claude-login path runs on the CLI's default model (Opus 5.5 here), ignoring the AI-model setting; the 7-tenths-of-a-cent price of a one-line rewrite is why this matters while usage limits bite.
- **Third pass: the founder found two bugs the audit missed** (24 Oct, "you haven't tested it end to end, you just created it"): (1) "Terminal · 318" showed 6 notes: menu and chip counts ignored the other filters that were on, and an empty list did not say why → faceted counts, dimmed empty options, "n of total · filters · Clear", "No note is all of these: …". (2) The keep-limit warning came back whenever Settings sections were switched: it was an `.item` row and `sgo()` un-hides every `.item` → drawn only while a choice waits, dropped on leaving. Cause of the miss: tests read `element.hidden` and data, not what is drawn. New rule and tests in `tests/test_e2e_screen.py` (computed visibility, an invariant over many filter states, round trip, hostile data, click-everything, dark theme, Insights numbers, scroll loading, keyboard shortcuts) and `tests/e2e_testcopy.py` (131 checks on the real app, including Ask AI, the card, files, Listen, every Settings switch and the founder's real history). They also found: a damaged saved view crashed the page (fixed), 2 s of silence became a saved note "KKK" (silence is never sent to the engine now; one repeated letter is never a note), "Clear" cut off, pressed state too faint. Fourth step (founder: "have you tested every case?"): an honest coverage map was written (`docs/AUDIT_24OCT.md` §6b) and the gaps were run: Ask AI end to end, the card's buttons, file transcription, line edits, Listen, speech-test marking, every Settings switch, real history vs an independent count, Insights numbers, scroll loading, shortcuts, speed at 25,800 notes after the new counts. Found and fixed: unknown AI action raised an error; Action items → To do silently created nothing for a plain-list answer. Write-up: `docs/AUDIT_24OCT.md` (35 findings).
- **Audit + second pass on the lists** (founder, 24 Oct: filter/sort UI off-theme, "How many to keep" UI wrong, search inside one transcript, test everything, search "with codes" not working, Delete should ask text / recording / both, filter by Fix / Always fix / Not a mistake). Full write-up: **`docs/AUDIT_24OCT.md`** (24 findings, all fixed; 45 tests; 0 JS / Python errors across every screen). Highlights: filter menus are now our own `popup()` menus (chip-like buttons, filled when active) instead of system dropdowns; "How many to keep" is a `.seg` + `.banner`; search treats curly quotes as quotes (the likely "codes" bug: dictation and macOS produce curly quotes, which returned nothing), ignores Latin accents, ranks by mentions; saved filters that no longer exist are ignored (they blanked the list); date headings only when sorted by date; Find in one transcript (Listen); Delete asks what to delete, with Undo (`store.stash_audio` / `delete_text` / `replace`, trash purged at start); Mistake review menu with `reviewed` kept on each note (decisions before 24 Oct are not recorded per note); capital-only Dictionary fixes allowed; torn-last-line guard on append; one directory listing instead of a disk check per note. Tests: `tests/test_lists_ui.py` (13 UI scenarios, headless Chrome), `tests/test_store_checks.py`.
- **Search, filter, sort and group on every list, built for years of use** (founder, 24 Oct: "imagine 2-3 years of recordings"). **Audit first:** only Dictations had search + 4 filters, Meetings/Files had search, To do and Dictionary had nothing, and nothing could be sorted. **Scale facts measured (made-up 25,800 notes = 25,000 dictations + 800 meetings, 33 MB):** `store.add` rewrote the whole file (465 ms), `history()` re-parsed every call (175 ms), the page receives all notes on every update (33 MB, ~250 ms), and `store.CAP = 500` deletes old plain dictations, so 2-3 years could not exist. **Built:** (page, `mac/ui/app.html`) one toolbar on Dictations, Meetings, Files, To do, Dictionary: filter chips, When (any month/year present), App, Group (date / app / none), Sort, "n of total" + Clear; multi-word AND search with "quoted phrases", marks, Best match while searching; smart date headings (Today, Yesterday, weekday, Earlier this month, "September 2026"); 100 rows at a time with Show more + scroll loading; letter headings in a long Dictionary; "Nothing matches" with a Clear button; filter/group/sort remembered per page (`views` pref). (Python, `mac/store.py`) parsed-rows cache (175 -> 8 ms), `add()` appends one line (465 -> 0 ms), pref `history_cap` (500 default / 5,000 / everything, 0) with Settings -> Privacy -> "How many to keep", which asks before deleting (the founder is at 475 of 500, so old dictations start going within days at the default). Help page has a "Find things" section; `docs/DESIGN.md` has the pattern. **Measured after:** 25,800 notes: first draw 137 ms, search 44 ms, filters 90 ms, sort 133 ms (was 673 ms), every page 150-330 ms, no JS errors; also run against the founder's real 517 notes, no errors. **Still the limit:** the page is sent every note on each update (33 MB, mostly meetings, ~250 ms at 25,800 notes), fine to roughly 10,000 dictations; beyond that move meeting segments out of the update or page on the Python side. Tests: `tests/test_lists_ui.py` (headless Chrome, made-up notes), store self-check (cap and cache).
- **Model + effort discovery, and cost in rupees** (founder, 24 Oct). `mac/models.py`: the lists of models and effort levels to offer. **Live** from Anthropic's Models API (`GET /v1/models`, each model with its supported effort levels; needs an API key) and OpenAI (`/v1/models`, ids only), cached in `models.json`; **built-in** table (copied from Anthropic's effort docs, 24 Oct 2026) for the Claude login, which has no listing call, and as the fallback. Settings → AI → Model now builds its options from this catalog (named versions such as "Opus 5.5 · claude-opus-5-5", plus haiku/sonnet/opus "latest" aliases and "account default"), with a "Refresh list" link, and a new **Effort** row listing only the levels the chosen model supports (disabled with a reason for OpenAI/OpenRouter, or a model with no effort setting). Effort goes to the Claude CLI as `--effort` (validated) and to the Anthropic API as `output_config.effort` (only a level the model is known to accept). Real CLI test, same rewrite on Haiku: low 25 output tokens, 4.0 s; max 501 tokens, 6.6 s. **Not tested live:** the Models API refresh (founder has no Anthropic key on this Mac; parsing is tested against the docs' example), OpenAI listing, Codex (not installed here, not built). New setting **Show AI cost in Dollars / Rupees** with a typed **rupees-per-dollar** rate (`cost_currency`, `usd_inr`; no rate is looked up or guessed, so Rupees without a rate keeps showing dollars); used by the cost chip and Insights. **Bug fixed on the way:** `ai.review` broke for API-key providers since the cost change (`_api` returns two values). Checked in headless Chrome across provider/model/currency cases, no console errors; `tests/test_models.py`, `tests/test_cli_usage.py`.
- **Model choice for the Claude login** (founder, 24 Oct: "a user should be able to select the model"). Settings → AI → Model now shows for the Claude login too (it was hidden): Claude's default for your account / haiku / sonnet / opus, or a custom id. Own pref `claude_model` (the API providers keep `ai_model`, so switching provider never sends a wrong id); `InditeApp.ai_model()` picks the right one; `notes._claude(model=...)` adds `--model`, and a typed name that is not `[A-Za-z0-9._-]` is refused so it can never become a CLI flag (`tests/test_cli_usage.py`). API list gained Sonnet 5.5 and Opus 5.5. **Measured, same one-line rewrite:** default (Opus 5.5) $0.00705 vs haiku $0.000177 at list price, ~40x less, 4.1 s vs 5.0 s. Quality on Hinglish rewrites at Haiku is **unproven**. The default stays "your account's".
- **Card buttons now react** (founder, 24 Oct): hover tint (ink 9 %), pressed tint (20 %), shown only while a click would count; while an AI action runs the card line pulses with cycling dots until the answer or failure (`button_look`, `_paint_buttons`, `_pulse` in `mac/overlay.py`; rules in `docs/DESIGN.md` §4). Tested headless on a card that was built but never shown: hover 0.09 only when clickable and over the button, 0 elsewhere; pulse cycles dots and fades 0.55-1.0, back to 1.0 on answer. **Not seen on a real screen; the pressed tint needs a real mouse-down.** Needs a restart.
- **New setting "AI buttons on the card"** (`card_ai`, on by default; Settings → Look & sounds, beside "Show text after dictating" and "Card buttons"): off keeps the card but shows only To do. `card_mode()` in `mac/indite_mac.py` with a self-check. Tested in the hidden copy (`buttons: True` vs `"todo"`; the two pickers hide when it is off).
- **Two to-dos added** for the founder (Wash clothes; Interview-prep agent). Voice commands ("make it formal", "add to to-do") do not exist: parked 18 Oct on the roadmap (revisit at ~30 real to-dos).
- **Speech set started:** read 20 sentences (names from the Dictionary); first read by eye: about 4 in 10 name mentions right, and the same sentence read twice gave different results (so one reading is a noisy measure). The Dictionary entries for the new spellings are deliberately NOT added until the baseline is scored. Next: founder reads sentences 4-20 one per note, fixes each to what was said, marks "This is exactly what I said", then `python mac/speechset.py score`.
- **Critic rule narrowed** (founder: critics used tokens without helping). Now only for features, app behaviour, security/privacy/data, or hard-to-undo changes. Skip for settings, tool/model choices, lookups, small fixes. A quick test beats a critic. Changed in `~/.claude/CLAUDE.md`, `CLAUDE.md`, `AGENTS.md`, `docs/HANDOFF.md`.
- **AI cost table fixed** (`mac/cost.py`): added the 5.5 models and corrected old prices against Anthropic's pricing page. Haiku 5.5 (the default) had been shown ~10x too high. OpenAI rows not re-checked. Self-check `.venv/bin/python mac/cost.py` → `ok`. Needs an app restart to take effect.
- **Model default** (founder near usage limits): global Sonnet 5.5 + high effort; Opus 5.5 + medium kept for hard work via `/model opus`. The AI flags tasks that need Opus. No code changed.

## 23 Oct 2026 (afternoon) · Mac: pill hidden from screen capture, multi-select → Ask AI combined

**Next step:** restart indite (`open -n -g dist/indite.app` — check the log first for ~2 min of quiet, per the rule) to pick up the new overlay.py and app.html. Then: start a Zoom/Loom/QuickTime screen recording, hold the hotkey, confirm the REC pill is NOT in the recording. And: open indite, kebab on any dictation → "Select (combine with others)" → tick 2–10 more → bottom bar → "Ask AI combined".

**Pill hidden from screen share (founder, 23 Oct).** `self.panel.setSharingType_(0)` on both the Pill ([mac/overlay.py:239](mac/overlay.py:239)) and the Card ([mac/overlay.py:390](mac/overlay.py:390)). macOS's `NSWindowSharingNone` (= 0) excludes a window from every system-mediated capture: ScreenCaptureKit (what Zoom, Meet, Teams, Loom use), QuickTime screen recording, and ⌘⇧3 screenshots. The pill is a dictator's HUD, not something viewers should see floating over the slide as "REC 02:59". Not tested in a live share yet — one-liner change, standard macOS API, low risk.

**Multi-select → Ask AI combined on Mac** (founder, 23 Oct, same shape as the Android build from this morning).
- **`store.combine(ids)`** at [mac/store.py:220](mac/store.py:220). Builds a new row with `kind: "combined"`, `sources: [ids]`, `sourceLabels: [name · date]`, and `text` = each source's full text under a `— Clip N: title · date —` header. Snapshot by design: deleting a source leaves it intact. `kind != "dictation"` so `keep()` protects it from the plain-dictation CAP. **Self-check in `mac/store.py` extended**: 2 dictations → combine → combined row has the expected headers, sources list, labels; `combine([one_id])` returns None; `combine([valid, invalid])` returns None; `clear()` keeps the combined row and only removes the plain dictations. All green: `.venv/bin/python mac/store.py` → `ok`.
- **New message action `"combine"`** in [mac/window.py:407](mac/window.py:407): calls `store.combine(ids)`, pushes new state, then `openDrawer(new_id)` on the web side so the Ask AI drawer opens on the new combined note straight away.
- **Dictations tab UI** in [mac/ui/app.html](mac/ui/app.html):
  - `let sel = new Set()` holds the selection ids.
  - Kebab menu first item (non-media only): `Select (combine with others)`.
  - Rows show a hollow circle (`.selmark`) in the time column when `sel.size > 0`; filled circle with tick when picked; row gets `.picked` class (brand-tinted background + 1.5 px brand border).
  - While selecting, clicking anywhere on a row (not on a button) toggles it in / out. Cap: 10, with a toast.
  - **Fixed bottom bar** `#selbar` (`.selbar`): `N selected · about W words · [Cancel] [Ask AI combined]`. Over 8,000 words the word count turns red with a one-line warning. The styles live beside `.row.sel` so dark/light inherit the same tokens the rest of the page uses.
  - `drawList` filter widened to include `kind === "combined"` so combined notes appear naturally in the Dictations tab. A combined row shows an `i-spark`-titled line with the title.
- **Verified in the hidden test copy** (never touched the founder's screen): seeded `sel` with 2 real ids, called `draw()`, read back: bottom bar visible with `"2 selected · about 12 words / Cancel / Ask AI combined"`; 2 rows have `.picked`; 2 filled marks + 9 hollow marks against 11 total rows; "Ask AI combined" button posts exactly `{"action":"combine","ids":[...]}` to Python; "Select (combine with others)" is the first item in the kebab menu. Testcopy stopped afterwards.

**Rules I kept:**
- Founder's live app was never touched. All verification ran in `python mac/testcopy.py` (own data folder, own engine on 8712, no mic/pill/card/menu icon). Testcopy stopped before I came off the keys.
- Pill was NOT tested on-screen (would need to open a share; founder's call).
- Not rebuilt (`build_app.sh` resets Accessibility and Screen Recording). The founder restarts his copy with `open -n -g dist/indite.app` after checking the log is quiet.

**Untested:**
- Pill-hide in a real screen share. One-line change, standard API, but needs a live Zoom/Loom/QuickTime run.
- `combine` end-to-end on a real indite instance (the self-check covers logic; the message handler is simple).
- Combined row interaction with Ask AI drawer not visually confirmed — but openDrawer takes any id and reads from S.history, which now carries `kind: "combined"` as a dictation-visible row.

**Open:**
- A combined note whose sources are later deleted shows "— Clip N: Dictation N · ..." headers with intact text, but a nice-to-have is a line "1 of 3 clips is gone" on the row. Not built — unproven whether anyone will care.
- Combined-of-combined is allowed (store.combine admits `kind` in dictation/combined/file/meeting). Whether that reads sensibly for the AI is open.
- Version not bumped.

---

## 23 Oct 2026 · Android: multi-select → Ask AI combined, paste-fail reason in log

**Next step:** build 30 on the phone, long-press a note → "Select (combine with others)" → pick 2–10 → bottom bar → "Ask AI combined"; try to reproduce the "typed to clipboard" bug and read the A/B/C/D1/D2/E line in `adb logcat -s indite`.

**(B) Clipboard-fallback diagnosis in the paste path.** [AutoPaste.kt:45](android/app/src/personal/java/com/whispercppdemo/overlay/AutoPaste.kt:45) now logs *which* of five conditions dropped the paste: A no focused box at bubble tap, B target node could not be refreshed (view rebuilt), C focus moved away during the recording, D1 target no longer editable, D2 target now looks sensitive, E app refused `ACTION_PASTE`. The behaviour is unchanged — a `false` still falls back to clipboard — but the next time it happens the log will say why, and the real fix can target the real cause. The old boolean guard had hidden five distinct bugs behind one return value.

**(A) Multi-select transcripts → one combined Ask AI note.** Founder request (23 Oct): "I speak multiple short recordings for the same idea and later can't recall it all at once; I want to summarise or email across them in one go."

Shape, after a critic pass (section below):
- **Snapshot into a NEW standalone note** (`Note.sources`, `Note.sourceLabels` in [Notes.kt](android/app/src/main/java/com/whispercppdemo/notes/Notes.kt)). The full transcript of each source is COPIED into the combined note's own `transcript.jsonl`, one piece per source, each prefixed with `— Clip N: name · date —`. Deleting any source leaves the combined note intact.
- **Entry:** long-press a note → the dropdown menu's first row is now `Select (combine with others)`. Normal long-press/menu behaviour is unchanged — one new row only.
- **Selection mode:** TopAppBar flips to `N selected / Cancel`; row shows a tick or a hollow circle; swipes are disabled while selecting; tap toggles. Row border/background colour marks selected.
- **Bottom bar:** `N selected · about W words · [Ask AI combined]`. Soft-warns in red above 8,000 words. Cap: 10.
- **Ask AI combined** calls `Notes.combine(sources)` which validates (2–10, done, non-empty), creates a new folder with the usual `meta.json` (now carrying `sources: [ids]` and `sourceLabels: [name · date]`), empty `cuts.json`, and `transcript.jsonl` with the headers; opens the new note. The existing AI drawer (Summary, Action items, Email, Make it formal, Ask anything…) then runs on the whole concatenated text as if it were one dictation.
- **Row chip:** combined notes show a `Combined` chip and `N clips · DD MMM` instead of a duration.
- **Backup/restore** rides along unchanged: `meta.json` is copied whole, so `sources`/`sourceLabels` survive without a `fmt` bump (optional fields; older readers ignore them).

**Critic pass before building** (full table in the chat thread). The real risk is a stale snapshot — if a user edits a source clip after combining, the combined note won't reflect that edit. Accepted and surfaced: the chip reads "Combined" and the title names the clip count and date. A "live" link (re-generate on source edit) is deliberately **not** built — unproven, and the simple snapshot answers the founder's actual ask. "Partial transcript selection" and bulk delete/export are also deliberately out.

**Untested:**
- Not run on the founder's phone yet (no build 30). Logic compiles clean under `:app:compilePersonalReleaseKotlin` and `:app:compilePublicReleaseKotlin`; unit tests pass.
- `Notes.combine` has no unit test (file-IO heavy, mostly header plumbing); the `require` on input validity is the only logic that can fail quietly.
- Paste-fail reason: not yet seen in the wild; the next real occurrence should surface the code.

**Open:**
- Deletion of a source clip is silent today — a future UX pass could show "1 of N clips is gone" on the combined row. Unproven: not blocking.
- Combined-of-combined (selecting two combined notes + one dictation) works; whether it reads sensibly for the AI is open.
- Version not bumped. Founder to decide when to cut build 30.

---

## 2026-10-18 (00:00-01:30) · Claude Code (Opus 5.5) · Portable app, bug sweep, UI review, critic-passed changes

- Portable app for other Macs (`mac/build_portable.sh`, `mac/portable_check.py`): the old app needed this project
  folder, macOS 26 and an old engine folder - that is why the boss's M2 "did nothing". Now 822 MB / 630 MB zip,
  macOS 14+, any Apple Silicon, start-up failures shown as a message, READ ME FIRST + Help inside. Tested hidden.
- ⚠ The disk filled up during the first build (1 GB free); build now refuses with < 4 GB and keeps no second copy.
- Calls: the call's sound capture died 7 s into a 13-min headphone call; it now reconnects. Listen: engine "nan"
  answers retried / estimated. Meetings log and show the mic in use.
- End-to-end test (agent, test copy): 17 bugs; all high/medium and most low fixed (crash on any window error,
  masked text saved over real words, meeting audio missing from backups, orphan recordings, ...).
- UI review (agent, 41 screens): items 1-23 done; critic on items 24-37: 13 built (some smaller), 2 dropped.
- Open: Who spoke failed once in the test copy ("GetElementType is not implemented"), not reproduced; lock added.

## 2026-10-17 (22:35-23:05) · Claude Code (Opus 5.5) · Rest of the Mac roadmap, copy review

- Built and tested (unit tests, self-checks, headless Chrome renders, the new hidden test copy): card buttons in
  Settings; meeting clock + Both tracks; word-time healing; paused dictations keep the lit word; test copy;
  Record this call?; own hidden words; setup step 5; line speaker fix + join with Undo; speech-test tools.
- Bugs found and fixed: card-button reload code had landed inside start-up (would not apply until restart);
  word times saved as all-zero when the engine was busy; word times kept after a fix changed the word count;
  a test leaked a fake thread maker into later tests; "Nothing to join" wording.
- Mistakes of mine, fixed: a plain `open` reached the test copy (founder's indite down ~30 s; now `open -n -g`);
  running the bundled Python wrote .pyc files into the app and broke its signature (warning shown once; removed,
  signature valid, app restarted). Both are in HANDOFF.
- Copy: independent agent reviewed every UI string; 12 must-fixes and most should/nice items applied. 17 tests pass.
- Answered: Wispr cleanup levels without AI (None yes, filler words yes, grammar/clarity/polish need a model).

## 2026-10-17 (22:30) · Claude Code (Opus 5.5) · Listen view restyled to indite's own look (#283)

- Listen panel now matches the note list: gutter, `.who` speaker colours, 14 px text, hairline rows, icon actions on
  hover, a grey player strip with SVG play/pause and a thin orange-fill slider. Playing line = `--well` (no orange box
  or bar); spoken word = `--accent-soft`. Hint text was centred by a CSS clash: fixed. New pattern in `docs/DESIGN.md`.
- Off-screen check: headless Chrome render of `app.html` with made-up notes (light + dark, dictation + meeting), no
  page errors. Live page reloaded in the background via `js:location.reload()` (no restart, no focus).
- Test fix: `test_mac_handsfree.py` replaced `threading.Thread` for the whole run, so 2 later tests failed when the
  files ran together. Now restored after each test. 13 pass (`uv run --with pytest pytest tests/test_mac_*.py`).

## 2026-10-17 (15:00-17:15) · Claude Code (Opus 5.5) · Card, clipboard, Insights, Mark likely mistakes, one roadmap

**Next step:** Mac next #4 (fixes count), #5 (engine-hint test), #7 (edit + undo); founder's 30-min checks (Mac next #2).

- Card: Ask AI + the two most-used AI actions + To do; copy icon tried and removed at the founder's call; answers wrap.
- Clipboard: typed words also copied; every AI answer copied (tested end to end in TextEdit: dictation, card
  Rewrite · Formal, Ask AI Summary).
- Insights: a rebuild was rolled back on founder feedback; the original page grouped into 4 sections + 4 KPIs.
- Copy: one icon on notes and answers; meeting copy/export use renamed speakers (bug).
- Mark likely mistakes built and tested end to end ("crasin" → Fix → "Crocin"). Found on the way: confidence comes
  in word pieces (merged now), and the second listen can differ from the typed text (flags now come from the text).
- ROADMAP.md rewritten as one file (Mac / Android, done / next / later / parked); 10 Oct sections archived; an audit
  of all requests, commits and chat logs added 11 missing items and 8 founder decisions.

---

## 2026-10-17 (14:40) · Claude Code (Opus 5.5) · Text card AI buttons; crash fix; context-safe fixes planned

**Next step:** founder dictates, hovers the card, clicks Make it a prompt - confirms the click-through works.

- Crash fixed: `window.py` add_fix refusal called `self.bridge.js` inside Bridge (from `3c9ba16`); now `self.js`.
- Text card (`overlay.Preview`): 3 buttons, clicks only while hovered (`_track`), `working()` / `answer()` states;
  `App.card_action`; `_ai` sends the answer back to the card and the clipboard. Snapshot: `preview:+text`.
- `tests/test_mac_handsfree.py` was failing since `9b0c4a8` (no `preview` on the fake app); fixed.
- Critic on the founder's "same word, different context" worry -> ROADMAP Mac #7 and Android #4.

---

## 2026-10-16 (10:20) · Claude Code (Opus 5.5) · Two roadmaps, personalisation plan, recordings reachable

**Next step:** founder: demo decisions (length) and the real speech set; Android item 1 (key or Tailscale).

- Recordings: saved but unreachable. Added Play / Show in Finder to the note menu (`store.audio_files`, window
  actions `play`/`reveal`). Crashed the app once on the way (a local `import subprocess` later in the same handler
  shadowed the module import); fixed, pyflakes clean, Show in Finder tested.
- ROADMAP.md forward sections rewritten as two roadmaps + limits table + personalisation (critic-reviewed).
- Another session (founder's other account) commits in the same folder (81f8487, narrate.py only). Commit this work
  soon so it is not swept into someone else's commit.

---

## 2026-10-16 (09:50) · Claude Code (Opus 5.5) · Swear masking fixed; roadmap re-prioritised

**Next step:** founder confirms the demo decisions and length; the real speech set starts (ROADMAP Now 1-2).

- Swear masking: removed from `tidy()` (the saved text); `App.out()` masks typed/copied/previewed/exported text;
  `store.masked()` masks the window's copy of notes. Check added to `mac/store.py`. App restarted, no rebuild.
- Wispr comparison found in MAC_PLAN §6, ROADMAP_DETAIL, WISPR_DEEPDIVE; ~10 decided items were missing from
  ROADMAP.md. "Now" rewritten (9 items) after a critic: demo first with a code freeze; real speech set gates step 1
  too (~1 day, not 2 h); verbose_json and the Dictionary cap before step 1; C2 + W2 merged into step 1; W1/W3 after
  the demo. New "Parked" table (₹15k phone, Mac certificate, build 29 check, Android key backup + release key).
- Stale fixed: header date, Wispr row, "shading unsure words", language order; requests #236, #238, #240, #244.

---

## 2026-10-16 (03:10) · Claude Code (Opus 5.5) · Mac: back-to-back meetings + working dots built

**Next step:** founder tries two real calls back to back; check both notes and the "Others" track.

- Each meeting is its own object; Stop finishes in the background; Start waits only for the old one to let go of the mic.
- Found while testing live: every 2nd meeting in a session failed ("Out is overriding existing Objective-C class") -
  `SystemAudio.start` defined its class each time. Fixed (defined once). A failed start now closes the mic.
- `mic_trouble` now logs the reason (it only showed a pop-up, which hid the cause during this test).
- UI: dot on Meetings / Files / Dictations tabs (red = recording, grey = working; still under reduced motion);
  "Finishing the last words…" on the row.
- Tests: `tests/test_mac_meetings.py` (B keeps its first 2 s, A keeps all of its own); 11 Mac tests pass. Live test
  with sample audio: two meetings 14 s apart, each with only its own text. Snapshot checked.
- Four test meeting notes left in the founder's list (03:02-03:06).

---

## 2026-10-16 (03:00) · Claude Code (Opus 5.5) · Mac: back-to-back meetings planned; assistant idea tested on paper

**Next step:** founder's go-ahead on the meetings plan (founder request 251) and on the 7-day assistant test (252).

- Bug fixed: `Meeting.start` never cleared `segments`, so a 2nd meeting in one app session saved the 1st's lines too. Saved meetings unaffected (each was in a different session).
- Two races found, unfixed: after Stop, Start is allowed at once; the old `stop()` then calls `app.mic.stop()` (kills the new mic) and `pump(force=True)` (reads the new meeting's audio from the shared mic queue).
- Research: Granola admits back-to-back calls can merge; macOS 14+ lists which app holds the mic (poll; listeners reportedly don't fire). Anthropic forbids routing users' Claude plans through third-party apps (API keys only). WhatsApp bans automating personal accounts.
- Founder usage: 127 of 167 notes were typed into Terminal or the Claude app; Ask AI used 14 times.

---

## 2026-10-16 (02:30) · Claude Code (Opus 5.5) · Mac: stuck mic, for real this time; assistant question answered

**Next step:** watch the log for "restarting indite to get the microphone back" to confirm the self-restart works on a real lock-up.

- Pill showed, nothing recorded, right after a meeting. A live stack sample showed a deadlock between PortAudio's stop
  and CoreAudio's audio thread, and the next open waiting on the same device lock forever. The 16 Oct "abandon the
  stream" fix cannot recover this: only a new process can. Force-restarted the app.
- Fix (critic: adopt with changes): `MicStuck`; `Mic.start` waits at most 8 s; a stuck close or open marks the mic
  stuck; the next press restarts indite (detached `open -n`, then `os._exit`, since `sys.exit` would hang in
  sounddevice's exit hook), at most once per 10 min (`restart_allowed`), else an alert. Test added; 10 Mac tests pass.
- Untested: the restart on a real lock-up. Unproven: that meetings are the trigger (1 of 2 lock-ups followed plain
  dictation). Worth checking: whether a newer PortAudio (bundled one is V19.7.0-devel) fixes the cause.
- Founder asked: build a personal assistant (Slack/Gmail/Drive) into indite, or use Claude? Critic-reviewed answer:
  use Claude/Gemini; nothing new now. Added to ROADMAP "Not doing". WhatsApp pre-fill is the one gap, if testers ask.
- uv.lock synced to the pynput==1.8.2 pin already in pyproject.

---

## 2026-10-15 (late night) · Claude Code (Opus 5.5) · Mac: key access fixed; it was a crash

**Next step:** restart the Mac (clears the frozen copy), then the demo video. B22 (real meeting) still open.

- Founder removed and re-added indite in Accessibility; it now reads True. Three dictations typed fine.
- Root cause of "permission doesn't work": pynput crashed indite the moment keys arrived (keyboard-layout call off the
  main thread, macOS 26). Fixed by reading the layout once on the main thread; pynput pinned to 1.8.2.
- The log's Accessibility line was really checking Input Monitoring; now both are logged. Crashes now leave a Python
  stack in the log (faulthandler).
- A frozen indite copy can't be killed (probably the company security agent); window opened via `demo.cmd` meanwhile.
- launcher.c: no endless wait loop on errors (applies at the next rebuild).
- Ask AI panel (critic-reviewed): no redraw unless something changed (scroll, cursor, choices kept); answers
  formatted (headings, bold, bullets; action-item tables stay as pipes); long answers folded with Show more; Ask box
  pinned at the bottom; errors shown in the panel and cleared on the next ask; dictation into indite's own window is
  no longer saved as a note (process check, not app name). Settings → AI lists what AI unlocks vs what is offline.
- Round 2 (critic-reviewed): Ask AI beside the list when wide, highlighted note, no dim layer, 32 px close, three
  plain sections, own Rewrite/Translate menus, growing Ask box, full question kept as the title. Caught and fixed my own
  bug (empty list: the list read a variable before it existed). Full self-test passed (see MAC_TEST_PLAN Part A).
- Heard twice: "indite" transcribed as "in diet" / "In night" - a word-fix candidate.
- Round 3 (founder: "maybe worse"): Ask AI rebuilt after a critic (answers as documents, options on a sunken surface,
  one-click Rewrite/Translate chips, loading + ready/failed message, calm styling app-wide). Summary scales with the
  note; API limits raised (300 s, 4000 tokens; long meetings untested).
- Roadmap research (web + MAC_PLAN §6) critic-reviewed -> `docs/ROADMAP_DETAIL.md`; ROADMAP "Now" 6-7 updated.
- Round 4: pill-after-hide bug fixed (tested with indite hidden); Ask AI closes on page switch; AI usage in Insights +
  "With AI" filter; gold AI chip; "Make it a prompt"; meeting/file → AI warning; optional swear masking (critic-reviewed).

## 2026-10-15 (night) · Claude Code (Opus 5.5) · Mac: UX restructure, AI providers, shareable build

**Next step:** founder sends `dist-share/indite-mac.zip` to his boss; says what still feels bad in Settings; tries a
real call with the meeting recorder. Me: the dropped-sentence-end test (running), then P6 (local clean-up test).

- UX review → one job per page, Settings in six sections with a finder, "…" menu per note, Light/Dark/Like the Mac.
- AI: off for new users; Claude login (account shown, Sign in opens Claude's login) or API key in the Keychain.
- Pill over full-screen Terminal fixed (Dock-app panels cannot enter another app's full screen).
- Blank window found via a real-window snapshot; page watcher reloads it. Slider ran backwards; full-screen width capped.
- `mac/build_share.sh`: self-contained 624 MB zip; engine library path from this Mac removed; first start 63 s → app waits.
- Roadmap with done / pending / future: `docs/MAC_PLAN.md` §0.
- Dictations no longer shows the words/speed/wait line (Insights has it).
- Night 2: who spoke automatic, app menus + full-screen focus fix, live pill glass with 10 % steps, Insights page, demo-video runner (blocked: Screen Recording permission not actually granted — also means meetings hear only the mic).
- Text card multi-line + dynamic height; reopening shows the window; AI answers collapsed; Objective-C double-class crash fixed. `docs/MAC_TEST_PLAN.md`: Part A (tested by Claude) + B1–B32 for the founder.
- Dropped-ending test: one real case (s38, `no_timestamps` makes the model stop after the first sentence); the rest were test-file faults. Retry fix designed and measured, not built (tiny gain, junk risk). The long_15min reference timings need fixing.

## 2026-10-15 (afternoon) · Claude Code (Opus 5.5) · Mac fixes

**Next step:** founder names what they miss from Wispr; then build personal word fixes + Esc cancel, and test a 60 s hold.

- Mac hotkey died when the default mic (a Bluetooth headset, off) failed to open. Fixed with a mic fallback; founder tested.
- Android and Mac apps separated: Mac has its own model link and spelling list.
- Leftover `whisper-server` processes (3 × 574 MB) after crashes; the app now clears them at startup.
- Critic review of Wispr-like Mac features (see HANDOFF "Mac fixes").
- Built: your own word fixes (`my_fixes.txt`, menu item) and Esc-to-cancel. Founder says both work.
- 60 s hold test: 75% words wrong at 62 s. Fixed by cutting long holds at quiet points: 19.0% at 62 s, 19.7% at 93 s.
- Log was empty (buffered prints); launcher now `python -u`.
- Evening: full screen (own Space), hands-free key + taps, transparency slider, notes/stars/To do, files in-app, AI (9 actions, improve keeps original), backup/restore, setup screen, meeting recording (mic + system audio), who spoke (59/60, 56/60), accuracy passes (clean 19.9% → 14.4%). All committed feature by feature.
- Pill animation fixed (underline glitch, blurred tick, abrupt cuts); capture checked from the log; MAC_PLAN holds R1–R27 + all answers + built-vs-planned.
- Founder's list R1–R24 (MAC_PLAN §3). Built: hands-free, ⌃⌘V, sounds, mic picker (old 'remember what worked' never saved), drag strip, clear glass pill + border + writing animation. Critic opinions on to-do, improve-with-original, assistant, meeting capture, install, commercial use.
- Android vs Mac and Wispr Flow research → `docs/MAC_PLAN.md`; critic: "all Android features" is the wrong goal. Built password guard, fix-a-word from history, Transcribe a file (web app), Login Items help. `mac/README.md` rewritten (was stale).
- Window redesigned (white, design-critic reviewed); Clear history fixed (it never worked); Liquid Glass pill; "nan" no longer typed.

## 2026-10-13/14 · Claude Code (Opus 5) · builds 16-29

**Next step:** founder's hand check of everything since build 15; back up the signing key; a new OpenRouter key so
an AI feature can answer on the phone for the first time; then the ₹15k phone and the install-size decision.

**Live dictation is under 10 seconds for the first time with accuracy intact: 9.6 s median, 17.1% words wrong,
15-min import unchanged at 25.0%, speakers 96.7%** (build 29, phone 33.5 → 36.9 °C).

- **The engine fix.** `Pauses.audioCtx` sizes the window to the piece instead of using a flat number. Two wrong turns
  first, both caught by the phone test: a flat 512 truncated 11 s pieces (live WER 18.3 → 32.8%), and the test
  override shipped enabled in build 28 so every piece got a 10.2 s window (15-min import 25.0 → 75.7%). `AudioCtxTest`
  now fails on all three mistakes.
- **`adb install` is 60x slower than push + `pm install`** for a 681 MB APK: 34 minutes vs 30 seconds. Three installs
  failed before this was found. Recorded in HANDOFF section 3.
- **Built:** restorable backup with a format version; one AI door replacing three duplicate buttons and a ten-label
  menu; per-paragraph speaker correction with merge and "Not sure"; retry one failed part; briefs linking tasks back to
  their paragraph; task states; keyboard rewrite chips; "say this calmly"; delete asks audio/text/both; reminders that
  ring on the alarm stream and stop every way a user might try.
- **Audit (Stage A) delivered:** 37 findings, coverage register, eight batches, published as an artifact. Stage B ran
  batches 1-5 and 8; R01 and R02 remain partly open (R02's speed half is now done).
- **Licence question closed:** the Hinglish model is Apache 2.0 — commercial use allowed, no permission needed.
  whisper.cpp is MIT. The repo still has no LICENSE of its own.
- **Corrections to earlier claims:** the model does *not* invent sentences from silence (it writes `nan`); the
  "invented words" in the scorer are real speech whose timestamps drift into a silence window. Whisper's own VAD was
  measured and rejected for transcription: 1,017 real words lost against 748 without it.
- Housekeeping: 2.4 GB of old speed-test APKs deleted (test audio kept), 4.3 GB free; `docs/PRD.md` written.

---

## 2026-10-11 (early) · Claude Code (Opus 5) · builds 12-14

**Next step:** alarm volume up, then Settings → Reminders → Test the sound. If it still doesn't ring, read the line
under the button. Then a new OpenRouter key → `apodex/apodex-1.1-mini:free` → one "Rewrite to send" end to end.

- **Merged the cloud branch** (automatic speaker labels, reminder diagnostics + test button, Translate language fix,
  Formal version). Three conflicts resolved by hand; pushed to GitHub (`df70283..caff151`).
- **Why AI features did nothing:** a saved OpenRouter key only counted if "Answer inside indite" was also ticked under
  "Where AI requests go". A working key is now always a route.
- **Why the reminder was silent:** a notification channel freezes its sound and stream at creation.
  `reminders_ring_v2` was born while the alarm switch was off (`usage=USAGE_NOTIFICATION`), so every later change was
  ignored. Channel ids now carry a fingerprint of their sound settings; stale `reminders*` channels are deleted.
  Verified after the fix: new channel, right sound, importance 4, no blocking setting. **Sound at the ear: unverified**
  (alarm volume is 5/16; the phone left the cable mid-test).
- **Rewrite to send**: one request with 9 styles (formal, polite, WhatsApp Hinglish, casual Hinglish, email, firm,
  apology, thank-you, short-and-crisp) or your own. Replaces "Formal version".
- **Delete asks what to delete**: audio only, text only, or the whole note, with the size. Now on the home long-press
  menu as well as inside the note — one shared dialog.
- **Free-model test (Mac, 45 requests):** `apodex/apodex-1.1-mini:free` 15/15, median 25 s, keeps Roman Hinglish and the
  `task | who | by when` format. `dots-3-note` translates to English and is slow. `gemma-4-31b` is rate-limited upstream.
- **Accessibility vs banking apps (researched + critic):** no test or certification exists; bank security SDKs flag any
  enabled third-party accessibility service. Never set `isAccessibilityTool="true"` (Play policy strike). Keep the
  service personal-only; the keyboard types with `commitText()` and never touches the clipboard.
- **Multiple keys to raise the free limit: no.** OpenRouter governs capacity per account, not per key.
- Invented words in silence: both model-side filters measured and killed (no_speech_prob 0.000 even on pure silence;
  95.5% word confidence on noise). Reverted; the finding is recorded in `NoteService.kt`.

---

## 2026-10-10 (night) · Claude Code (Opus 5)

---

## 2026-10-10 (night) · Claude Code (Opus 5, cloud session) · reminder sound, translation, formal version

**Next step:** build 11 on the Mac, install, then Settings -> Reminders -> **Test the reminder sound** (switch ON, then
OFF), one real 2-minute reminder with the phone locked, one Translate, one Formal version. **Nothing in this entry was
compiled:** the cloud container has no Android SDK, no model assets and no signing key.

The founder reported three hand-check failures: "alarm is not giving me sound", "the translations are not working", and
"making formal statement out of the context I have shared" does not work.

**Reminder sound.** Ranked causes, after an independent critic knocked down the first theory:
1. **"Ring like an alarm" defaulted to OFF** (`Reminders.ringLikeAlarm` returned `false`), so every reminder was a
   2.6 s chime on the notification stream - muted by silent/vibrate, Do Not Disturb or a low notification volume.
   Request #84 was "alarm-like sound" and it shipped as an opt-in switch, off, buried in Settings. **Now ON by default**,
   and the alarm path is the channel's own sound with `USAGE_ALARM` + `FLAG_INSISTENT` (alarm stream, alarm volume,
   repeated by the phone until seen, through silent mode and through DND wherever DND allows alarms).
2. **POST_NOTIFICATIONS was only ever requested when recording or importing**, never when a reminder was set. Denied =
   nothing appears and nothing sounds. `RemindDialog` now asks when it opens, `show()` reports whether the phone took
   the notification, and `fire()` marks a reminder `fired` only then, so one that could not be shown is not lost.
3. **OxygenOS force-stopping indite** drops its alarms. Settings -> Reminders now says so and opens the phone's battery
   setting; that button existed only under the floating-mic section before.

**Wrong theory, recorded so nobody repeats it:** that the channel's sound URI used the numeric `R.raw.reminder` id and
that AAPT2 had moved it. `reminder.wav`, the channel ids and `setSound` all arrived in one commit (`3d42717`) and
`res/raw` has not changed since, so the stored number still resolved. The URI is named anyway (via
`getResourceEntryName`, which also keeps a code reference so resource shrinking can't strip the WAV), and the channel
ids went to `_v2` because a channel's sound is frozen at creation and the `USAGE_ALARM` change needed a new id. ⚠ A
further change needs `_v3`: deleting a channel does not reset it - recreating the same id restores the old settings.

**Written and then deleted: a foreground service that played the alarm itself** (`notes/AlarmRing.kt`). The critic was
right that it was over-engineering: it marked a reminder `fired` before the notification was confirmed, and opening
indite removed its own ongoing notification - both ways to lose a reminder, inside the fix for a lost reminder. The
channel route does the same job with the system playing the sound. Add a player back only if a device test shows the
phone cutting the channel sound short.

Also fixed: a missed reminder re-announced itself on every app open (`rescheduleAll` notified every past reminder and
nothing marked it done) - now a `fired` flag in `reminders.json`, shown once, quietly. And there is now a way to test
the sound in 2 seconds: Settings -> Reminders -> **Test the reminder sound** + Stop, `soundProblem()` naming the
blocking phone setting (notifications off, channel blocked or muted, silent/vibrate, notification volume 0, DND, alarm
volume 0), and a "Last reminder: ..." line recording what happened the last time one fired.

**Translate.** Two real bugs: *Ask my AI -> Translate* called `ask("Translate")` with no language, so `{lang}` became
"English" - and the Hinglish rule was already skipped for Translate, so a Hinglish note came back looking almost
unchanged; it now opens the language picker. And the Google Translate route (free, offline, no key) was the last line of
a scrolling dialog; it is now the first button when the app is installed. **But the real block is configuration:**
indite has no translator or AI of its own, `MacCompanion` needs Tailscale and `OpenRouter` needs a key, so every AI
request can today only hand the text to another app and wait for a paste. Settings -> AI now prints one line
(`aiRouteNow()`) saying exactly what will happen. **An OpenRouter key is the highest-value thing the founder can do.**

**Another wrong theory, checked against Google's docs:** that Android 11+ package visibility made
`startActivity(setPackage(...))` throw for Google Translate and the AI apps. It does not - `startActivity()` needs no
package visibility, for implicit or explicit intents; filtering hits *queries* and starting another app's *service*.
`<queries>` was kept for one package only, because `installed()` asks whether Google Translate is there.

**"Formal version" added** to `AskPrompts`: formal English, every fact/name/number/date kept, nothing invented,
"(unclear)" where it can't tell. It and Translate are in `OwnLanguage`, so the "reply in Hinglish" rule is skipped -
that rule would have wrecked a formal English statement.

**Speaker labels now run by themselves** (founder: "why does speaker diarization not work automatically? ... the
initial speaker diarization should be done by you"). The honest answer to "why": **nothing ever decided it had to be
manual.** It was built as an on-demand card and request #60 removed the *count* question but left the tap. No technical
blocker either - PLAN.md line 230 records 15.9 s on the phone for a 15-minute file, about 1 s per minute of audio.
- `NoteService` now labels every note it just finished, once the queue has nothing left to transcribe, inside the
  foreground service (so Android cannot kill it half-done). Only notes *this run* finished - never a sweep of the whole
  back catalogue. Dropped rather than queued when the phone is hot or the battery is low: labels are not urgent, and
  `waitUntilSafe()` would have pinned the foreground service open (it never gives up on a low battery) for a note whose
  text was already finished.
- ⚠ **Corrected after the critic:** "never delays a live dictation" was false and had been written into the code, the
  commit message and three docs. `labelFinished()` runs in the one queue job and `onStartCommand` only starts a queue
  `if (job?.isActive != true)`, so a recording started mid-pass waits for it - and with `Notes.transcribing` false the
  recorder would have cut 1 s pieces that piled up unprocessed. Mitigations (both unmeasured on a device):
  `Notes.transcribing = true` while labelling, and an abort check passed into the pass and tested every 50 windows
  (~1-2 s of phone time), which saves nothing and leaves the note for the next run.
- `catch (e: Exception)` became `runCatching` (Throwable): a failed sherpa-onnx native load throws `UnsatisfiedLinkError`
  and a big `readPcm` can throw `OutOfMemoryError`, neither of which is an `Exception`, and both would have killed the
  queue coroutine - at the end of every long note instead of only when the user tapped. `Notes.import` already used
  `Throwable` for the same reason.
- The one-voice test counts `seg`, not just `of`: a second speaker can live entirely inside paragraphs (the short
  interview question, which is the shape of the real 15-min recording) and never win one, and the first version would
  have thrown all those per-sentence turns away.
- An explicit "2" that collapses to one voice used to show nothing at all, so the run looked like a no-op. The note
  screen now says "indite could only hear one voice in this note".
- Gate: over 60 s, 2+ paragraphs, no speakers file yet, and not a `test` note, so `phone_test.sh`'s `--ei k 2` scoring
  is untouched.
- `Speakers.labelAuto()` and `Speakers.status` (a MutableStateFlow: `Speakers.running` is a plain set and not
  observable, so the note screen could not show a run it did not start). The note screen now has one `busy` value for
  "something is working on this note", whoever started it.
- **One voice = no labels at all**, however the run started. An explicit "1" used to write "Speaker 1" on every
  paragraph. `heardOne()` saves `skipped=true, k=1, guessed=<indite decided it>`, and the note screen shows a one-line
  "indite heard one voice. Two people spoke?" only when indite decided it, not when the user chose 1.
- The existing "indite heard N people. Is that right?" card is unchanged: that is the "ask and update later" half.
- The "one voice = no labels" rule is the part that matters most: before it, once `speakers.json` existed there was no
  way back to plain text (the "Just me" button needs `speakers == null`, and the confirm card's "1" wrote `k=1`
  *labelled*, putting "Speaker 1" on every paragraph). **A wrong automatic guess is now undoable in one tap.**
- Consent framing: the only place that said "when you record others, tell them first" was the card that automatic
  labelling makes disappear. That line moved onto the "indite heard N people" card, and `privacy.txt` / `docs/privacy.md`
  now say what this does - compared on the phone, within one recording only, no voiceprint saved. `speakers.json` holds
  only ints, sample offsets and names the user typed; the fingerprints live in RAM for one note and are never written.
- No setting added on purpose. ⚠ **This is ahead of the project's own gate.** PLAN.md line 230 already says "auto count
  fragile on real audio", `phone_test.sh` only ever scores a *given* count (so 96.7% / 93.3% are given-count numbers),
  and #61 "can I trust Find who spoke?" is still waiting on the founder's listen-check - and the guess is now the
  default output for every long note. `auto()`'s 1-vs-2 call rests on one threshold (centres >= 0.35 cosine distance
  apart, and 3 windows ~ 4.5 s is enough to declare a second speaker on a 60 s note), so the expected failure is
  splitting one person into two: background TV, or music, which Silero hears as speech. Keep it in the personal build;
  it must not reach testers until measured. Also unmeasured: "15.9 s for a 15-min file" is a `--ei k 2` run, while
  `auto()` runs k-means for k = 2..5 (embedding extraction, the expensive part, still happens once).
  **Next action, no new code:** `--es test_label "<name>" --ei k 0` runs `auto()` on a benchmark note and writes the
  labels and `label_ms`; `score.py diar` scores it. Both dialogues plus the 15-min 3-voice file, ~20 min of phone time,
  answers accuracy and cost together. Numbers go in PLAN.md section 7.
- Known and not fixed: "Copy all text" on a labelled note joins consecutive turns by the same speaker into one block
  (`allText()`), so an interview where one person speaks five paragraphs running becomes one wall of text - pre-existing,
  but automatic labelling makes it the default. Floating-mic dictations over 60 s with 2+ paragraphs also pass the gate,
  so a long solo dictation with a TV on can pick up labels (the pasted text is unaffected).

Docs: founder requests 178 (reminder sound), 179 (translation), 180 (formal statement), 181 (automatic speaker labels);
summary counts corrected to 181 rows; ROADMAP "Now" item 0; HANDOFF section 5 tables with the ranked causes and both
dead theories.

**Open question for the founder:** when the reminder was due, did it appear on screen with no sound, or did nothing
appear at all? Silent-but-visible points at cause 1; nothing at all points at 2 or 3.

**Untested:** all of the above, plus everything from builds 8-10 that has not been hand-checked.

---

## 2026-10-10 (later) · Claude Code (Opus 5 / Opus 5.5) · builds 8-10

**Next step:** founder's 20-minute hand check of builds 9–10. Then the Sarvam Edge / Gboard Roman-Hinglish desk check
(1 h), the import-vs-live cut-point run (1 h), real-voice WER on ~6 min (2 h). Batch A (build 11) only after that.

- **Full phone test of build 10 passed the 15-min gate** (`SKIP_LIVE=1 ./phone_test.sh`, phone 34.7–36.8 °C):
  import WER 25.3% (build 7: 28.7%; Mac: 24.7%), 39 parts, 1.16x real time, no crash or memory failure.
  Similar voices 93.3% / 86.4%; 2-speaker dialogue 98.3% / 96.6%.
- **New finding:** 2 of 5 no-speech stretches produced invented text (10 words in pink noise, 4 in fan noise; 14 of 1545).
- **Trap found and documented:** `SKIP_LIVE=1` reuses the live result on the phone — here the ROUND=64 A/B arm, so the
  printed live numbers (87.3 s, 17.9%) are not build 10's.
- Independent critic reviewed a 17-item research / improvement / use-case list. Dropped: thread-emulation of a ₹15k phone
  (PLAN section 7 already has the numbers, and nothing calibrates it), cutting pieces earlier (a 5.3 s piece costs the
  same ~9 s of engine as a 10.0 s one, and short pieces score worse), deleting the dropped-text re-run, and all six "new
  use cases" (already built or already ruled out — recruitment copy, not code). Kept: Sarvam/Gboard check,
  start-temperature line in the test script, import-vs-live cut-point run, real-voice WER, note format version.
- **Critic's find:** `Pauses.audioCtx` is a flat 768 (15 s window) for every piece under ~13 s, so short sentences pay
  full price. A per-piece 512 (10.2 s, still a multiple of 256) could move the live wait from ~9 s toward ~6 s. Untested.
- **Recorded, not acted on:** the signing key still has one copy (5-minute founder task); "model downloads on first open"
  conflicts with the public build having no INTERNET permission, and a Play asset pack (~512 MB limit) may not fit the
  574 MB model — check the limit before writing code.
- ChatGPT: in-app login is still not a legal route (preview is application-only, no mobile; faking Codex's client risks
  the founder's own account). Founder's alternative — genuine Codex CLI under Termux on the phone — is unproven and needs
  a critic plus a 1-hour install test before it becomes a plan.

---

## 2026-10-10 (evening) · Claude Code (Opus 5.5)

**Next step:** founder hand check of builds 9–10; full phone test on a cool phone; then build 11 per ROADMAP.

- Root cause of "same audio, different text" confirmed on the phone: audio window rounded to 256 → identical text across
  runs; A/B vs old rounding: live wait 9.1/14.1 s vs 78.8/87.3 s. Heat (+1 °C) costs ~5 s. Kept 256.
- Added: Mac route can answer with ChatGPT via the founder's own Codex CLI; Settings → Your stats dashboard; header and
  subtitle fixes; chips padding; A/B test hook + `phone_test.sh` ROUND= / LIVE_ONLY=.
- ChatGPT login inside the app: not allowed yet (application-only preview, no mobile); founder may apply.
- Repo: GitHub `vaibhavk93/Indite` (public) at `790924c`; local is 32 commits ahead (not pushed).

## 2026-10-10 (afternoon) · Claude Code (Opus 5.5)

**Next step:** quick phone test of build 10 (engine fix), founder hand check, then build 11 per ROADMAP plan.

- Root cause of "same audio, different text": flash attention + audio windows not a multiple of 256. Fixed (`a69dab5`).
- Builds 9–10: reminders, floating-mic switch rework + tile, cards/menus/sticky dates, swipe hint, keyboard redesign,
  password guard, Undo/Redo, Settings Reminders/Tutorial, header/subtitle polish. Tags `build-9`, `build-10`.
- Research: one-speaker focus (feasible for turn-taking; overlap not now), value-adds per journey (top 8), vernacular
  Roman script (demand check first), iOS costs. All critic-reviewed.
- New doc: `docs/FOUNDER_REQUESTS.md` (every founder request + status).

## 2026-10-10 · Claude Code (Opus 5.5)

**Next step:** founder tries build 7; then `QUICK=1` phone test; record the 15-min run-to-run finding.

Later the same day (build 7, tag `build-7`): Settings in 6 groups; bubble hide → notification; OpenRouter key +
"where AI requests go"; Remind me; password/OTP guard; versioning (0.7, build 7, git hash in About); handoff docs;
look-and-feel batch (transitions, voice glow, fade-in, "All written", day headers, swipe-right copy).

Built (all committed; pushed up to `738a118`):
- v0.6 part 2: export, privacy policy, debug info, auto titles, storage check, consent reminder, test hooks personal-only.
- Floating mic "no speech" fixed (mic service type dropped on stop cut the last read; last piece now saved in `finally`).
- Bubble: spinner while writing, green copy button, hold 0.4 s to cancel, shrink when idle, drag away = hidden with a
  "Tap to show" notification. Keyboard: listening → writing → typed in; skips password/OTP boxes.
- Personal build: accessibility auto-paste into the focused box; OpenRouter key (answers saved inside indite).
- Speaker labels per sentence (51.7% → 96.7% on the phone test); guess the count, then confirm.
- Make notes / Action items / Translate buttons; meeting notes include task rows (Calendar, Remind me, Share);
  "where AI requests go" (tick several); language picker; AI requests v2 (date, title, transcript-is-data).
- Settings split into 6 groups; floating Record button on home.
- Imports: dropped-text re-run limited to live recordings (it made the 15-min file worse).
- `phone_test.sh`: `QUICK=1` mode (~12 min).
- Docs: ROADMAP.md merged into one roadmap (+ page); research reports on translation, iOS, UI/UX, Wispr Flow.

Untested on the phone: Settings groups, bubble hide notification, OpenRouter, Remind me, keyboard password guard.

Decisions (founder): bubble without accessibility now, accessibility add-on later (personal has it); guess-then-confirm
speaker count; iPhone not now (trigger: 5+ tester asks); one roadmap.

## 15 Oct 2026 (evening) — Wispr Flow screenshots: gap check, critic pass, plan

The founder sent 15 Wispr Flow screenshots and asked which features indite lacks, which are easy, which are not.
Checked each against the code (not from memory), then put the whole list past an independent critic.

**The result overturned most of the list.** 5 of 14 "missing" features are already built:
- Snippets = the existing word fixes (`store.apply_my_fixes`; the file's own example is a full postal address).
- The Dictionary page, add/remove, and "teach this" from a past dictation all exist (`ui/app.html:452`, `:1300`).
- Words per minute, time saved, by app, by hour, day streak and the heat map are all on Insights (`:1368`-`1394`).
  Note the contradiction: ROADMAP says "no streaks", the code shows one. Someone should decide which is right.

**Build now (~2 h):** W1 one example phrase row on the Dictionary page; W2 "teach this word" one click from the
Dictations list; W3 a "fixes made" count on Insights.

**Gated:** W4 feed the Dictionary to whisper as `initial_prompt` — the only item that can actually lower the error
rate, and the only one whose failure is invisible (the model already wrote `nan` into a real app on a 1.7 s hold).
Gate: the 360-clip bench must improve *and* show 0 false insertions of dictionary words. W5 "Light" clean-up with no
AI at all (strip a fixed filler list in `tidy()`, keep the raw text) — gate: 30 real dictations, 0 real words removed.

**Dropped, 11 items** — AI clean-up on every dictation (4-7x slower, spends the founder's quota, replaces the raw
text), transforms hotkey, per-app styles, command mode, stacked messages, Dock-icon toggle (would break the pill over
full-screen apps), mute music, LaunchAgent login, scratchpad, IDE file reading, extra languages, team/sync/referrals.
Reasons in `docs/MAC_PLAN.md` section 6.

**What the critic said matters more:** (1) Screen & System Audio Recording is still not granted, so meeting recording
and the demo video are built-but-dead; (2) the 53 real dictations have never been scored — every accuracy number is
from 360 synthetic clips, and `digits.py` admits its pass changed 0 of those 53; (3) nothing is signed or notarised,
and 10 items are still "built, founder to check". Also: the public repo has no LICENSE file, and the keystore still
has one copy.

Corrected in this session: I first reported snippets, the Dictionary UI and the Insights stats as missing. They are
all present. The error came from checking for new files instead of reading the ones that exist.

## 16 Oct 2026 · Mac: ready for the leadership demo

- **Long dictation no longer crawls in** (founder, request 244). pynput sends two key events per character, so a
  paragraph was hundreds of events and Chromium apps drained them a frame at a time. One macOS key event can carry
  20 UTF-16 units instead — about 40x fewer events. Measured through indite itself: TextEdit 0.23–0.61 s, a Chrome
  textarea 0.48–0.85 s, character-exact at 197 / 788 / 1576 chars. Numbers in
  `docs/research/mac_typing_speed_2026-10-16.txt`. The clipboard is still never touched.
  **The clipboard route was rejected** by the critic: a restore racing a slow app can paste the *previous* clipboard
  (a password manager entry) into the target, and a missed secure-field check would leave a spoken secret on the
  clipboard. It would also adopt the mechanism MAC_PLAN names as Wispr's weakness.
- **Word fixes no longer break contractions.** With `don = Dawn`, "don't go" became "Dawn't go". Found by the
  research agent, reproduced, fixed, covered by `store.py`'s self-check. Possessives are left alone too, on purpose.
- **Demo script updated** (request 242): a scene for the gold AI edge, "Make it a prompt" named in the Ask AI line,
  AI usage named in the Insights line, the "about a second" claim narrowed to "a second for a sentence like that",
  and `stage()` pre-answers the meeting→AI warning so the modal cannot interrupt a take.
- **"Make it a prompt" rebuilt** (request 243) to Anthropic's published guidance: says why the rules exist, five
  numbered parts, one worked Hinglish→prompt example, keeps Indian words with a gloss. `max_tokens` 4000 → 8000 and
  a cut-off answer now says so instead of looking finished.
- **`docs/WISPR_DEEPDIVE.md`** (732 lines, request 238): how Wispr builds each feature we lack, every option for us,
  the best two each, challenges and workarounds, multi-language routes, the AI-review algorithms, profanity design.
  Three findings that change decisions: the offline near-miss check only passes its gate when gated on the engine's
  own confidence (1.9 → 0.4 false alarms per 100 words); feeding the Dictionary to whisper as `initial_prompt` makes
  overall accuracy *worse* in published measurements, and collapsed on German (6.3% → 15.2%), and our model is a
  non-English fine-tune; the tester keystore is byte-identical to `~/.android/debug.keystore`.
- Founder's decision: the Android release key waits for the next Android build; the Mac demo comes first.

**Still open:** swear masking is stored rather than shown (breaks R5 — see HANDOFF §5). Slack and VS Code typing
untested. The note-before-instructions change for all 13 AI actions is deliberately **not** done before the demo.

## 16 Oct 2026 (early hours) · Mac: four bugs found by testing the whole app, demo cut built

Full end-to-end run, 21 checks. First pass: 16 passed, 5 failed. Final: **21 of 21**.

**Bugs found and fixed**
1. **CoreAudio deadlock.** Four threads wedged in `FinishStoppingStream` → `std::recursive_mutex::lock()`. Dictation
   worked once, then every press was dead: pill up, bars frozen, nothing written. `_drop()` now aborts instead of
   stopping, closes on its own thread and abandons the stream after 1.5 s.
2. **PortAudio left shut down** — caused by the first fix. The per-press device rescan is `Pa_Terminate` +
   `Pa_Initialize`; when the terminate wedged and we moved on, it finished later with nothing to re-initialise, so
   every open after that failed with "Error querying device -1". The rescan now runs only after every device has
   failed to open, and `_alive()` restarts PortAudio before each use.
3. **The consent dialog landed in `who_spoke()` as well as `ask_ai()`** (my edit, 15 Oct). Speaker detection is
   entirely local, so it asked about a send that never happens — and crashed, since `NSAlert` is imported in
   `ask_ai`. Every file transcribed fine and was then reported "file failed", with no speakers. Removed.
4. **The app was breaking its own signature every run.** Python wrote `.pyc` files into the bundle (249 found), the
   seal broke, and macOS dropped Accessibility mid-session — the log shows `allowed: True` → `not trusted` →
   `allowed: False`. `PYTHONDONTWRITEBYTECODE=1`, bundle cleaned and re-signed, `build_app.sh` now verifies the seal
   and refuses a build that does not hold, and `signature_broken()` warns at start-up.

**Measured after:** 6 recordings back to back; 389 characters typed exactly in 0.32 s; 230 s two-speaker file → 31 s
to transcribe, 58 s to find 2 voices; all 8 pages draw; signature still valid after a full run.

**Demo:** `docs/DEMO_PLAN.md` (researched, critic-reviewed — it overturned 6 of its own 8 first recommendations).
22 scenes → 8 beats, 6–8 min → 3:20, hero at second zero, Wi-Fi off on camera instead of a privacy sentence, live
meeting recording cut because its permission is still unproven in a real call. `demo.py --short` built.
Biggest finding: every sound in the current demo is synthetic, including the Hinglish spoken *into* the app.

**Open:** the founder's narration, and whether to show a real error on camera. Signing certificate: after the demo.
