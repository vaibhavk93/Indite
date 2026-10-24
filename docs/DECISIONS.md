# Decisions waiting on the founder

Each one blocks or shapes something in `ROADMAP.md`. When one is decided, write the answer and the date here, move it
to "Decided", and update the roadmap item it touches.

## Waiting

| # | Decision | What it blocks or shapes | Options |
|---|---|---|---|
| D1 | A LICENSE for the public GitHub repo | Anyone may copy the code today without terms | MIT / Apache-2.0 / all rights reserved / make the repo private |
| D2 | Un-park the Android build 29 check and the release key | **Every new Android build** (Android next #2-3) | Now / later |
| D3 | Leadership demo: length, your own narration, show a real mistake | Mac next #8 | 3:00-3:30 or ~9:30; your voice or synthetic; yes / no |
| D5 | 7-day assistant test: plan and pass bar written in `docs/ASSISTANT_TEST.md` (24 Oct). You said go: it starts when you ask your first question to Claude Code about your notes | Whether indite grows an assistant mode (#252) | 5-10 min a day for 7 days |
| D8 | Subtitle style and wording (#110, #175) | Android home screen | Keep italic / plain; wording |
| D9 | A commercial-use review before selling | Ownership, security review, privacy law | When to start |
| D10 | A smaller speech model if the Play Store asset pack is too big | Android next #7 | Said "yes, if quality doesn't drop" (13 Oct): set the quality bar |
| D11 | The accessibility add-on in the public Android build (#33): see D30 | Auto-typing and "bubble only with a keyboard" for everyone | Decide in D30 |
| D13 | Pill vs window: what "dragging is not working" means (17 Oct) | A bug (window strip) or a new feature (move the pill) | Window / pill |
| D14 | **Grow the Dictionary to ~20 names of 6+ letters** (people, brands, medicines you say) | 24 Oct (second count): 32 entries, about **15 real names of 6+ letters** (Aishwarya, Coimbatore, Confluence, Tihaar Jail, Vaigai river, …). About 5 more. The two risky entries (`sau = Sure`, `and sure = Ensure`) are gone (24 Oct) | Add ~5 names |
| D15 | **Mark ~35 dictations "This is exactly what I said"** (Settings → Privacy → Speech test is on for you; fix the text first) | 24 Oct: **7 of 35 marked.** The first real accuracy number comes after 35; then `python mac/speechset.py score` | ~25 min more |
| D17 | Live clean-up while dictating with a local model | Needs 30 real dictations compared side by side (your judgement) | After D15 |
| D19 | Listen look ✅ (you checked, 24 Oct). Still open: **Both tracks on your next real call** and the card buttons in Settings | Built 17 Oct | With the call checks (D26) |
| D20 | **One real call with headphones on** (5 min is enough), after today's fix | The call's sound now reconnects if it drops (16 Oct it died after 7 s). Also check: Settings → General → Microphone is your headphone mic, else indite hears you only faintly | Do it / tell me what you saw |
| D21 | **Send your boss the new `indite-mac.zip`** (`dist/portable/`, 630 MB) and tell me what he sees. His Mac: Apple M2 ✓; still needed: the macOS version (needs 14+) | The old app could never run there (it needed your project folder) | Send it / tell me his macOS |
| D26 | **Meetings and calls checks, at the end** (you keep 3 waiting): live meeting with mic + system sound, "Record this call?" card, pill hidden during a screen share. Say "start the call checks" and I walk you through one step at a time | Not testable without a real call | ~15 min |
| D27 | **Optional: live model list**: save an Anthropic API key (Settings → AI) and press Refresh list next to Model; tell me what appears | The only way to test the live list; a Codex list is not built (Codex is not installed here) | 2 min, needs a key |
| D28 | **Optional: Android** - nothing changed today; only needed if you want build 29 re-checked | Same as D2 | Now / later |
| D29 | **Trademark for "Inditeflow": IP India search done by the founder (24 Oct, classes 9 and 42); next searches and the filing.** Result: **no INDITE or INDITEFLOW mark in class 9.** Closest: (a) **INDITECH** (Inditech Electrosystems Pvt Ltd): class 9 "downloadable applications for mobile devices / software for smartphones" (label mark registered 2018, valid to 2028; a word mark applied 29 Dec 2025 is under examination) and class 42 data backup (applied Dec 2025). Same goods, and the first five letters INDIT are shared: **the most likely citation**. (b) **Indite Technologies Pvt Ltd**, class 42 "software design, technical writing, IT solution services": registered 2011, **validity shows 18 Mar 2021, so renewal status must be checked** (the portal may be out of date). (c) INDITE ARCHITECTS (class 42, objected, architecture) and indiTESP (SaaS, 2032): different words and fields. Not yet searched: **classes 35, 41, 44** (transcription services), Canada, USA, WIPO. Risk: **medium** for India | Whether to keep the name and what to file | Search 35/41/44 and the phonetic search for INDIT*; check Indite Technologies' renewal; then a trademark agent's opinion before filing (two plausible objections to answer) |
| D30 | **Android: accessibility add-on in the public build?** Research done (Google Play rules). My recommendation: public build = keyboard with a mic button (no declaration needed); accessibility typing stays in your own build for now, and goes to Play later only as an opt-in with the full form | Decides how Android types into other apps for everyone | Decide: keyboard first / accessibility with the Play form now |
| D33 | **After the rename: things only you can do** (the code cannot do them): (1) **Mac:** rebuild with `mac/build_app.sh`, then re-allow Inditeflow in System Settings → Privacy & Security → Accessibility, Input Monitoring, Microphone and Screen & System Audio Recording (macOS ties these to the app's id, which changed); re-add it under Login Items. Your notes and Dictionary move on their own. (2) **Android:** the new app (`com.inditeflow.app`) installs next to the old one and starts empty. In the old app: Settings → Backup; in the new app: Restore. Then remove the old app. (3) **GitHub:** rename the repository (Settings → General); the old link redirects. (4) Re-run the name check for **Inditeflow** (D29 was for "indite"). (5) The logo and the word on it still say "indite" in the picture files; a designer pass is needed | None of these can be done from the code | 20-30 min |
| D34 | **"Flow" and Wispr Flow:** the name ends in the same word as the app we compare ourselves to. "Flow" is a common word in software names (a separate, weaker risk than D29). Fine, or a risk? | Brand / trademark | Your call after D29 |

## Decided

| # | Decision | Answer | Date |
|---|---|---|---|
| D6 | Retry button on cards (#56) | **Add it** | 24 Oct (built, compiles; not on a phone yet) |
| D7 | Logo: orange dot on the "i" | **Keep it.** Trademark search first: preliminary web check done (no live clash found, but the official registers could not be searched). Next: D29 | 24 Oct |
| D16 | Note-before-instructions order for AI actions | **Tested, no difference: leave the order as it is** (30 requests, Haiku low, 3 made-up notes x 5 actions x 2 orders: both orders 15 of 15 fine; the injected "reply HACKED" line was ignored in all) | 24 Oct |
| D18 | ₹ / lakh-crore / % / $ / time / email formatting | **Yes. Built** inside "Numbers as digits" (see worklog 24 Oct) | 24 Oct |
| D23 | Esc cancels a dictation | **Works** (founder live check). The direct Esc check fixed it | 24 Oct |
| D24 | How many to keep / Restore fixes | **Work** (founder live check) | 24 Oct |
| D25 | "Record this call?" card for Meet / Zoom in a browser | **Yes, after a minute of steady mic use. Built** (needs a real browser call to check: D26) | 24 Oct |
| D4 | One name for word fixes | **"Dictionary"** on both Mac and Android (Android renamed 24 Oct, compiles; not on a phone yet) | 24 Oct |
| D12 | Two unclear 10 Oct messages ("…prompt and transcript…", "double long-press") | **Dropped** (founder, 24 Oct) | 24 Oct |
| D32 | Rename the app from Indite to Inditeflow | **Yes** (founder, 24 Oct). Done on the branch `rename-inditeflow`; merge after you check the list in D33 | 24 Oct |
| D22 | "Don't save the next dictation" | Yes, build it (also skips the clipboard) | 18 Oct |
| — | OpenRouter "train on my data" | Turned off by the founder | 17 Oct |
| — | Slack and VS Code typing | Works, confirmed by the founder | 17 Oct |
| — | Park: ₹15k phone, Mac signing certificate, build 29 check, Android key | Parked | 16 Oct |
