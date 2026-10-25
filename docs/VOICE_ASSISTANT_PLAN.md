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
