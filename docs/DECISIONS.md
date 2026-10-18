# Decisions waiting on the founder

Each one blocks or shapes something in `ROADMAP.md`. When one is decided, write the answer and the date here, move it
to "Decided", and update the roadmap item it touches.

## Waiting

| # | Decision | What it blocks or shapes | Options |
|---|---|---|---|
| D1 | A LICENSE for the public GitHub repo | Anyone may copy the code today without terms | MIT / Apache-2.0 / all rights reserved / make the repo private |
| D2 | Un-park the Android build 29 check and the release key | **Every new Android build** (Android next #2-3) | Now / later |
| D3 | Leadership demo: length, your own narration, show a real mistake | Mac next #8 | 3:00-3:30 or ~9:30; your voice or synthetic; yes / no |
| D4 | One name for word fixes | Same app on both platforms | "Dictionary" (Mac) or "Word fixes" (Android) |
| D5 | Go-ahead for the 7-day assistant test (Claude Code over your notes) | Whether indite grows an assistant mode (#252) | Yes / no |
| D6 | A Retry button on cards (#56) | Android UI | Add / drop |
| D7 | Logo: the orange dot on the "i" (#107) | Branding; do a trademark search first | Keep / change |
| D8 | Subtitle style and wording (#110, #175) | Android home screen | Keep italic / plain; wording |
| D9 | A commercial-use review before selling | Ownership, security review, privacy law | When to start |
| D10 | A smaller speech model if the Play Store asset pack is too big | Android next #7 | Said "yes, if quality doesn't drop" (13 Oct): set the quality bar |
| D11 | The accessibility add-on in the public Android build (#33) | Auto-typing and "bubble only with a keyboard" for everyone | In / out (Play review risk) |
| D12 | Two unclear 10 Oct messages ("…prompt and transcript…", "double long-press") | Unknown | Say what was meant, or drop |
| D13 | Pill vs window: what "dragging is not working" means (17 Oct) | A bug (window strip) or a new feature (move the pill) | Window / pill |
| D14 | **Grow the Dictionary to ~20 names of 6+ letters** (people, brands, medicines you say) | The speech test proves nothing without them; Mark likely mistakes has nothing to look for | Add them in Dictionary |
| D15 | **Mark ~35 dictations "This is exactly what I said"** (Settings → Privacy → Speech test is on for you; fix the text first) | The first real accuracy number; then `python mac/speechset.py score` | ~30 min of your time |
| D16 | Note-before-instructions order test for the AI actions | Uses your Claude account: ~10 AI requests | Yes / no |
| D17 | Live clean-up while dictating with a local model | Needs 30 real dictations compared side by side (your judgement) | After D15 |
| D18 | ₹ / lakh-crore formatting ("2 lakh" → "₹2,00,000"?) | Unproven: no real note shows the need yet | Want it / wait for examples |
| D19 | Check the new things on your screen: Listen look, Both tracks on your next call, "Record this call?" card, card buttons in Settings | Built 17 Oct, tested off-screen only | Yes / what's wrong |
| D20 | **One real call with headphones on** (5 min is enough), after today's fix | The call's sound now reconnects if it drops (16 Oct it died after 7 s). Also check: Settings → General → Microphone is your headphone mic, else indite hears you only faintly | Do it / tell me what you saw |
| D21 | **Send your boss the new `indite-mac.zip`** (`dist/portable/`, 630 MB) and tell me what he sees. His Mac: Apple M2 ✓; still needed: the macOS version (needs 14+) | The old app could never run there (it needed your project folder) | Send it / tell me his macOS |

## Decided

| # | Decision | Answer | Date |
|---|---|---|---|
| D22 | "Don't save the next dictation" | Yes, build it (also skips the clipboard) | 18 Oct |
| — | OpenRouter "train on my data" | Turned off by the founder | 17 Oct |
| — | Slack and VS Code typing | Works, confirmed by the founder | 17 Oct |
| — | Park: ₹15k phone, Mac signing certificate, build 29 check, Android key | Parked | 16 Oct |
