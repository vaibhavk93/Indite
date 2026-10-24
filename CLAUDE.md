# indite: instructions for coding agents

**Before doing anything, read `docs/HANDOFF.md`.** It has the rules, how to build and test, the code map and where things stand.

At the end of every session:
1. Update section 5 of `docs/HANDOFF.md` ("Where things stand").
2. Add a dated entry to `docs/WORKLOG.md`.
3. If anything was built, decided or dropped, update `ROADMAP.md` (the one roadmap).
4. Add every new founder request to `docs/FOUNDER_REQUESTS.md` and update its status (the founder's go-to checklist).

Key rules (details in HANDOFF): the GitHub repo is public (no recordings, keys, APKs or models in git); the public app
build has no internet permission; big suggestions (features, behavior, security/data, hard to undo) go past an independent critic first; write in
plain, simple language.

**Two founder rules (17 Oct), always:**
- **Our own design, not the common AI-tool look.** Before building or changing any screen, read `docs/DESIGN.md` and
  follow it; add any new pattern to it.
- **Never test on the founder's screen while he works.** Test in a separate space (see HANDOFF "Testing without
  disturbing the founder"). Until that exists: no opening other apps, no taking over the clipboard without restoring it,
  sound muted, no app restarts while he is dictating (check the log first), and ask before anything visible.
