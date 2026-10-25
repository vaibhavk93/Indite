# Personal voice assistant: plan (founder idea, 25 Oct 2026, request #343)

**Idea:** speak to an assistant that reads Gmail, Drive, Calendar, Slack (and Figma / other tools), speaks a short brief of
what needs the founder's input, takes a spoken reply, and leaves a polished **Gmail draft** to review and send.

**Decision (critic reviewed, one critic, 25 Oct): do Phase 0 as a text-first test. Do not build Phase 1 until Inditeflow's
next release ships and the Phase 0 numbers pass.** It is a separate project, not a branch of Inditeflow: Inditeflow's promise is
"offline and private" (the public Android build has no internet permission); an assistant is online by nature.

## Layers

| Layer | Today | Notes |
|---|---|---|
| Voice in | Inditeflow dictation (local) | Names are the weak spot: add them to the Dictionary |
| Brain | `claude` on the founder's Mac, his own login | Usage limits of his plan apply: measure tokens per brief |
| Hands | claude.ai connectors in Claude Code: Gmail (search, read, create draft), Drive, Calendar, Slack, Figma | **Zoom failed to connect: dropped for now.** Google Meet has no connector of its own: Calendar (meeting invites) plus Drive/Gmail (notes and transcripts, only if the Google plan saves them) |
| Voice out | macOS `say` (robotic, mangles names) | A brief takes ~2 min to hear and ~30 s to read: test text against voice |
| Review gate | The founder reads every draft | The model cannot know office history, so "politics-safe" is a tone helper, not a guarantee |

## Hard rules (enforced by a tool allowlist, not by asking nicely)

1. Read and draft only. The allowlist holds search, read, create-draft. **Send, forward, reply, trash, delete and post are not on it.**
2. Email text is untrusted data: a hostile email may say "add this link / this Drive fact to your reply". Drafts are read before sending.
3. Write down what is excluded before day 1 (legal, HR, finance, anything under a confidentiality rule). **Check your company's rules before pointing it at a work mailbox.**
4. One week, then stop and decide.

## Phase 0: one week, no code

- Days 1-3 text only (ask in Claude Code, read the answer). Days 4-7 the same with a spoken brief. Compare which he uses.
- Routine: "What mail came in today that needs my input? Brief, most critical first." Then: "Reply to X: <context>. Formal, clear, no blame. Draft only."
- Log every question in `docs/ASSISTANT_TEST.md` (same log table).

| Pass bar (set now, not moved later) | |
|---|---|
| Brief right on at least 8 of 10 mornings | |
| Drafts needing under 3 edits | at least 70% |
| Days used | at least 5 of 7 |
| Wrong-recipient or wrong-fact drafts that reached him | 0 |

## Phase 1 (only after Inditeflow ships and Phase 0 passes)

A thin menu-bar helper that runs the fixed "morning brief" through `claude -p` with the allowlist, speaks or shows the result, and
turns one spoken reply into one draft. Measure time per brief (likely 30-90 s with several connectors) and fix what is too slow.

## Never

Auto-send, auto-reply, deleting mail, posting to Slack on its own, WhatsApp reading (breaks its terms).


---

# Part 2 (25 Oct): a standalone assistant with its own tool connections, training, costs, roadmap

## 1. Can a separate app connect to these tools itself (not through this Claude Code session)? Yes.

**Checked on the founder's Mac, 25 Oct (`claude mcp list`, run outside any session):** the `claude` program already sees
**Gmail, Google Calendar and Google Drive through Google's own MCP addresses** (`gmailmcp.googleapis.com`,
`calendarmcp.googleapis.com`, `drivemcp.googleapis.com`), plus **Figma and Atlassian (Jira / Confluence)**: all connected.
**Slack: "needs authentication".** Zoom: no working connector (its plugin failed with a login error). Google Meet: none of its own.

| Way to connect | How | Good | Bad |
|---|---|---|---|
| **A. Drive `claude -p`** (Phase 1) | The app runs the founder's own `claude` with a tool allowlist; his connectors come with it | No login code to write; fastest | Mac only; uses his plan's limits; Inditeflow's AI call today switches connectors OFF on purpose, the assistant would switch only the chosen ones ON |
| B. Claude Agent SDK / API | The app is an MCP client and logs in to each service itself | Full control, can run on a server or phone | Pay per token; you keep the logins safe; Google checks apps that ask for Gmail/Drive access if the app is public |
| C. Own small MCP client | Written by us | Most control | Most work and upkeep for one person |

**Recommended: A for Phase 1, B only if it is ever given to other people.**

## 2. "Train a model on what I speak": three different things

*Costs are estimates from general knowledge, not live quotes. I have not priced any of this today.*

| What you might train | Possible? | Data needed | Rough cost | My advice |
|---|---|---|---|---|
| **The speech model (hears you better)** | Yes. Inditeflow's engine is already a Hinglish-tuned Whisper; a personal fine-tune is possible | 5-20 hours of your audio with **corrected** text (the correcting is your cost: roughly as many hours as the audio) | Rented GPU about $10-50 for the run | **Not yet.** Your 35 marked dictations are too few. First score them and see if names, accent or numbers cause the errors. The Dictionary already fixes names. Earlier research: biasing the engine with a word list made accuracy worse |
| **A language model (writes like you, decides like you)** | Claude models cannot be fine-tuned by an individual as far as I know. An open model can (LoRA) | 500-2,000 of your sent emails | About $20-150 plus running it | **No.** Putting 10 of your best sent emails and a short "my rules" file in the prompt gets most of the effect with no training, and you can edit it in a minute |
| **A voice that speaks (your own voice clone)** | Yes, with a TTS service | A few minutes of your voice | A few dollars a month | Optional polish, last. Your own voice only |

## 3. Running cost (estimates; prices from `mac/cost.py`, checked 24 Oct)

One morning brief of about 60,000 tokens read and 3,000 tokens written:

| Model | Per brief | If daily for a month |
|---|---|---|
| Haiku 5.5 ($0.10 / $0.50 per million) | about $0.008 (under ₹1) | about ₹20 |
| Sonnet 5.5 ($2 / $10) | about $0.15 (about ₹13) | about ₹400 |
| Opus 5.5 ($4 / $20) | about $0.30 (about ₹26) | about ₹800 |

Through your Claude login (Phase 0 and 1A) this uses your plan's limit, not cash. Spoken output: macOS voice is free; a good cloud voice is roughly a few rupees per brief (unverified).

## 4. Use-case roadmap and what is feasible

**Legend:** ✅ feasible now · 🟡 feasible with work or limits · ❌ not feasible (technology, or a rule we choose)

| # | Use case | By phase | Feasible | Note |
|---|---|---|---|---|
| **A. Inbox and replies** | | | | |
| 1 | Morning brief: mail that needs my input, most critical first | 0 | ✅ | Gmail read |
| 2 | Spoken reply, polished, saved as a **Gmail draft** | 0 | ✅ | Draft only |
| 3 | Tone check: blame, absolutes, risky cc lists, forwarded chains | 1 | ✅ | A helper, **not a guarantee** |
| 4 | "What did I promise / who owes me" from mail, Slack and notes | 1 | 🟡 | Needs good names (Dictionary) |
| 5 | Auto-send or auto-reply | never | ❌ | A rule we choose |
| **B. Meetings** | | | | |
| 6 | Pre-meeting brief: invite, related mail, related Drive files | 1 | ✅ | Calendar + Gmail + Drive |
| 7 | After a meeting: summary, action items, follow-up drafts from your Inditeflow recording | 1 | ✅ | Recording stays local |
| 8 | Meet notes and transcripts from Drive | 1 | 🟡 | Only if your Google plan saves them |
| 9 | A bot that joins Zoom or Meet and transcribes | later | ❌ | Platform rules and heavy work; Inditeflow's local recording does the job |
| **C. Work tools** | | | | |
| 10 | Slack digest: what needs me | 1 | 🟡 | Slack needs login; limited by your workspace's permissions |
| 11 | Drive: find, open, summarise the latest version of a file | 0 | ✅ | |
| 12 | Jira / Confluence: my tickets, due dates | 1 | ✅ | Atlassian is connected |
| 13 | Figma: files and comments needing a reply | 2 | 🟡 | Depends on what the Figma connector exposes |
| **D. Personal** | | | | |
| 14 | "What is my day?" | 0 | ✅ | Calendar read |
| 15 | Create or move calendar events | 2 | 🟡 | Writes need a confirm step |
| 16 | To-dos from what you said | 1 | ✅ | Inditeflow's To do page |
| 17 | Payments, bookings, anything with money | never for now | ❌ | Too costly if wrong |
| **E. Voice experience** | | | | |
| 18 | Hinglish voice in | 0 | ✅ | Inditeflow |
| 19 | Natural voice out in Hinglish | 2 | 🟡 | Names and Hindi words are the weak spot |
| 20 | Wake word ("Hey ...") always listening | later | 🟡 | A privacy and battery trade-off |
| 21 | Interrupt it while it speaks | later | 🟡 | Needs echo handling; hard |
| 22 | Phone version | later | 🟡 | A different app that needs internet |
| **F. Memory and style** | | | | |
| 23 | Remembers your tone, names, who is who | 1 | ✅ | A plain "my rules" file you can edit |
| 24 | Writes like you | 1 | ✅ | A few of your sent mails in the prompt |
| 25 | Knows office politics and who is sensitive | never | ❌ | It cannot see history; you write the rules |
| **G. Trust and safety** | | | | |
| 26 | Approval screen and a log for every action | 1 | ✅ | Must-have |
| 27 | Tool allowlist (read + draft only) | 0 | ✅ | Must-have |
| 28 | Test with hostile emails before real use | 1 | ✅ | Must-have |

## 5. Build or just use what exists?

Claude's own apps, Gemini (inside Gmail / Drive / Meet) and ChatGPT already offer connectors and voice. Before building, spend
one hour with them on the same morning-brief and draft tasks. What a **separate** assistant could add: Hinglish voice, your own
"my rules" file, the read-and-draft-only guard, and local-first notes. That is the reason to build, and the Phase 0 numbers
will say whether it is enough.
