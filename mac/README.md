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

On an M1, 14 Oct, 24 real clips:

| Utterance | Time to text |
|---|---|
| 3 s | 1.2–1.4 s |
| 5 s | 1.3–1.5 s |
| 8 s | 1.3–1.5 s |

For comparison: the phone takes 9.6 s for the same work. The difference is heat and small cores, not the model.

## What it does not do yet

- The model is loaded for every utterance (about 0.9 s of the time above). A resident engine would make it ~0.5 s.
- No installer: it runs from this folder. A drag-to-Applications bundle is the next step.
- No settings window — the hotkey is fixed to right-Option in the code.
- No notes, no history: it types the text and forgets it. Use the phone app for anything you want to keep.
