# indite for Mac

Hold the right-hand **Option** key, speak, let go. The text is typed where your cursor is — in any app.

Everything happens on this Mac. The recording goes to a temporary file, is transcribed by whisper.cpp with the same
Hinglish model the phone uses, and is deleted. Nothing is sent anywhere.

## Run it

```sh
.venv/bin/python mac/indite_mac.py
```

A 🎙 appears in the menu bar. Red while you hold the key, hourglass while it writes.

## The two permissions macOS will ask for

| Permission | Why | Where |
|---|---|---|
| **Microphone** | to hear you | asked on first use |
| **Accessibility** | to type into the app you are in, and to notice the hotkey | System Settings → Privacy & Security → Accessibility |

For the Accessibility one, add the **Terminal** (or whichever app runs the command) — macOS grants it to the running
program, not to the script. Nothing is granted silently: you tick it yourself, once.

## Speed, measured

On an M1, 15 Oct, with the model kept loaded:

| Utterance | Time to text |
|---|---|
| 3 s | 0.67–0.71 s |
| 5 s | 0.70–0.71 s |
| 8 s | 0.77–0.81 s |

**Median 0.71 s.** For comparison: the phone takes 9.6 s for the same work, and Wispr Flow's cloud takes 1–2 s.

Two things make that number, and both are easy to lose:

- **The model stays loaded.** Reloading it per sentence cost 0.9 s (1.35 s per sentence instead of 0.71).
- **The window is sent with every request.** Without it the engine pads every sentence to 30 seconds and takes
  **2.19 s** - slower than not keeping the model loaded at all.

## What it does not do yet

- No installer beyond `indite.app` in `dist/`: it still borrows Python and the model from this folder, so it cannot
  be handed to anyone else yet.
- The engine takes ~17 s to load at startup. The menu bar shows 🎙… until it is ready.
- No settings window — the hotkey is fixed to right-Option in the code.
- No notes, no history: it types the text and forgets it. Use the phone app for anything you want to keep.
