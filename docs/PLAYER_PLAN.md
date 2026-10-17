# Player plan: listen to a note inside indite, with the words following along

**Draft - not yet critic-reviewed.** Written 2026-10-17. Mac app first; Android notes at the end.

**Verdict: play the recording in the Ask AI side panel (the "drawer"), using the Mac's own audio player called from
Python, and light up the line being played. Build it in 5 small steps; leave word-by-word sync for later.**

---

## 1. Today, and what we can reuse

| What | Today | File |
|---|---|---|
| Play | `⋯ → Play recording` runs `open <wav>`: QuickTime opens outside the app. A meeting opens two QuickTime windows (you, others). | `mac/window.py` act `play` |
| Kept audio | Dictation: `audio/<id>.wav`, only if "Keep audio" is on (off by default). Meeting: `<id>-you.wav` + `<id>-others.wav`. File: its original path. | `store.audio_files` |
| Timings | Meetings and files have `segments` `[{start, end, speaker, text}]`. Dictations have none. | `meeting.py`, `indite_mac.py` |
| Side panel | Ask AI drawer: 460 px, focus handling, Escape closes. | `app.html` `openDrawer` |
| Edit | Edit text (one undo) - **only for notes without speakers**. Speaker rename (whole note). Flags (Mark likely mistakes) and Fix a word. | `window.py`, `app.html` |
| Android | Tap a paragraph -> sheet with Edit / Play / Copy. Plays **that one piece** and highlights it. No whole-note player. | `NotesApp.kt` `Player` |

**⚠ Remember:** how fine the highlight can be depends on the note type. File segments are 15-20 s pieces (the cut
made by `pieces()`), so a file's highlight moves paragraph by paragraph, not sentence by sentence. Meeting lines are
one stretch of speech between pauses.

**Note:** Edit text on a file note today changes `text` but not `segments`. So after an edit the two disagree. The
player shows segments, so step 3 must fix this (edit a line, then rebuild the text from the lines).

---

## 2. What others do (checked 2026-10-17)

| App | Highlight while playing | Tap text to jump | Other |
|---|---|---|---|
| Otter.ai | Word | Yes | Speed; skip silence is paid ([App Store](https://apps.apple.com/us/app/otter-ai-voice-notes/id1276437113)) |
| Google Recorder (Pixel) | Word | Yes | Search a word, matches marked on the seek bar ([TechCrunch, Oct 2019](https://techcrunch.com/2019/10/15/googles-new-voice-recorder-app-transcribes-in-real-time-even-when-offline)) |
| Apple Voice Memos (iOS 18 / macOS 15) | Word (while recording) | Yes (per [Cult of Mac](https://www.cultofmac.com/?p=889140); Apple's [page](https://support.apple.com/en-gb/guide/voice-memos/view-a-transcription-of-a-recording-vm4a03609f0d/3.0/mac/15.0) does not say) | Apple silicon only |
| Descript | Word | Yes | Edit while playing: the text cursor moves on its own, apart from the playhead ([help](https://help.descript.com/descript-tour/playback-and-navigation)) |
| Trint | Word | Yes | Speed, keys to pause and jump back. Added/deleted words lose their timing ([help](https://info.trint.com/knowledge/how-do-i-playback-my-transcript-trint-help-center), [Six Colors 2017](https://sixcolors.com/post/2017/05/create-audio-transcripts-fast-with-trint/)) |
| Granola | - | - | Keeps no audio at all ([zackproser](https://zackproser.com/blog/how-does-granola-ai-work)) |
| Notion AI meeting notes | - | - | No synced playback; audio is temporary ([tl;dv review](https://tldv.io/blog/notion-ai-meeting-notes-review/)) |
| Rev | - | - | No primary source found; skipped |

**Lesson:** the common core is small: highlight, click to jump, speed, jump back a few seconds, keys. Word-level
highlight is normal elsewhere, but every app doing it keeps word timings from the start. We do not.

---

## 3. Where the player lives

```
                     WHERE DOES THE PLAYER GO?
          needs room for controls + the whole transcript
                              |
       +----------------------+----------------------+
       v                      v                      v
+--------------+   #======================#   +--------------+
| Inline in    |   # * THE SIDE PANEL     #   | Bottom bar   |
| the note row |   #   (Ask AI drawer)    #   | (whole app)  |
+------+-------+   #==========+===========#   +------+-------+
       |                      |                      |
 + no new surface      + drawer code exists     + keeps playing
 - rows are clamped    + room for every line      while browsing
   to 4 lines          + one note at a time     - a new layout
 - list jumps around   - covers part of list    - lines still need
   while you scroll      on small windows         a place to show

  * = recommended        # box = the pick
```

- **Opens from:** `⋯ → Play recording` (same item, new behavior), and a small ▶ on any note that has audio.
- **Closes:** Escape, the ✕, or opening another note. Closing stops playback.
- **Keep** "Show in Finder" and add "Open in QuickTime" in the panel's `⋯`, for anyone who wants the old way.

### The sketch

```
+------------------------------------------------- Listen ----- ✕ -+
| Meeting with Rohit · 14 Oct · 32 min                               |
|  [<<15] [<<5]   ( ▶ )   [5>>] [15>>]      1x ▾   You+Others ▾      |
|  12:41 ━━━━━━━━━━━━━━●──────────────────────────────── 32:07       |
|--------------------------------------------------------------------|
|  12:02  You    So the release is Thursday?                     ⋯   |
| >12:38  Rohit  Yes, but CleverTap wala change is still open.   ⋯ < |  <- playing line, tinted
|  12:55  You    OK, I'll ping them.                             ⋯   |
|                                                                    |
|              [ ↓ Back to the playing line ]   (only after you     |
|                                                scroll away)       |
+--------------------------------------------------------------------+
   ⋯ on a line: Play this line · Edit line · Change speaker · Copy line
```

### Keys (only when the cursor is not in a text box)

| Key | Does |
|---|---|
| Space | Play / pause |
| ← / → | Back / forward 5 s |
| Shift + ← / → | Back / forward 15 s |
| Escape | Close the panel (stops) |

---

## 4. How the sound plays

**⚠ Remember:** the page cannot just use an HTML `<audio>` tag. The window only lets the page read files in
`mac/ui/` (`loadFileURL ... allowingReadAccessToURL` in `window.py`). Recordings live in `~/Library/Application
Support/indite/audio/` or anywhere on disk. Widening that permission would let the page read the whole home folder.

```
                     WHO PLAYS THE SOUND?
                              |
       +----------------------+----------------------+
       v                      v                      v
+--------------+   #======================#   +--------------+
|x <audio> +   |   # * Python plays it    #   |x <audio> via |
|  wider file  |   #   (AVAudioPlayer)    #   |  own URL     |
|  access      |   #==========+===========#   |  scheme      |
+--------------+              |               +--------------+
 x page could read      + already installed     x must answer byte-range
   any home file          (pyobjc-avfoundation)   requests for seeking;
                        + speed, seek, volume     more code, more risk
                        + 2 players = 2 tracks
                        - page asks Python for the time
  * = recommended        # box = the pick        x prefix = ruled out
```

- **Time to the page:** while playing, a 0.25 s timer in Python sends `tick(seconds)` to the page. Off when paused.
- **Meetings:** two players (you, others) started together with `playAtTime`. A menu picks You / Others / Both by
  setting each player's volume.
- **Files AVAudioPlayer cannot open** (for example `.ogg`, `.webm`, some videos): decode once with the existing
  `load_audio` (PyAV) into a temporary wav, delete it on close.
- **One at a time:** opening another note stops the first.

**⚠ Remember:** playback must never touch the microphone (`Mic` / sounddevice input). AVAudioPlayer only outputs sound,
so it does not. But two clashes are real:

| Clash | Why it matters | Rule |
|---|---|---|
| You press the dictation key while a note plays | The mic hears the speakers and types the recording | Pause playback in `Mic.start` |
| A meeting is recording | System audio capture records the playback as "Others" | Play is disabled, with the reason shown |

---

## 5. Following along

| Note type | What lights up | How |
|---|---|---|
| Meeting | The line playing | `start <= t < end` on that track's lines |
| File | The 15-20 s piece playing | Same, from `segments` |
| Dictation with audio | The whole text (no timings) + the seek bar | Nothing new |
| No audio kept | No player | Panel says: "No recording kept. Turn on Keep audio in Settings to keep future ones." |

- **Click a line** -> jump there and play.
- **Auto-scroll** keeps the playing line in view. If you scroll yourself, it stops following and shows "Back to the
  playing line". Scrolling is instant when the Mac's Reduce motion is on.

### Word-by-word for dictations (later, unproven)

- The resident whisper-server can send each word with `start` / `end`: `verbose_json` turns `token_timestamps` on
  (`server.cpp` lines 632-635, 1139-1141).
- Cost: asking for detail made a 4 s clip take 0.8 s -> 1.4 s (measured 16 Oct, `Engine.confidence`). So it must run
  only when you press Play, never while dictating.
- **⚠ Remember:** the new words will not match the saved text exactly (tidy, Dictionary fixes, your edits). They
  must be lined up with the saved text (Python's `difflib`), and some words will have no time.
- **Why it waits:** most dictations are 5-20 s. A whole-text highlight is probably enough. No one has asked for word
  level yet.

---

## 6. Changing a part

Pause, change, carry on. Editing a line pauses playback. Saving does **not** restart it. You press Space.

| Action on a line | New or reuse | Note |
|---|---|---|
| Play this line | New, small | Stops at the line's end. Same as Android today |
| Edit line | **New** `edit_line` action: changes `segments[i].text`, rebuilds `text`, one undo | Fixes the stale-segments problem; gives meetings an edit for the first time |
| Change speaker of this line | Same action, `speaker` field, picker of this note's speakers | Rename stays whole-note |
| Flags / Fix a word | Reuse the existing flag rendering in that line | No new logic |
| Copy line | Reuse the clipboard | Trivial |
| Re-transcribe this part | **Left out** | Same audio + same model mostly gives the same words. Unproven |
| Loop a part | **Left out** | "Play this line" covers hearing a hard word again |

**Note:** timings stay with the line, so editing a line's words never breaks sync. Only whole-text edits did that.

---

## 7. Things not asked for

| Topic | Plan |
|---|---|
| Playing aloud in an office | Plays through whatever output is chosen. No headphone check (YAGNI). Space pauses at once |
| Audio moved or deleted | No ▶ shown (already true via `audio_files`). Later: "File moved - Locate…" |
| Long files, 15-60 min | AVAudioPlayer reads from disk, so memory is fine (60 min wav = about 115 MB on disk). The panel shows every line, not 6 |
| Two notes at once | Not allowed; the new one stops the old one |
| Window closed / Mac sleeps | Closing the window stops playback |
| Accessibility | Real buttons with labels; the seek bar is a native `input type=range` (keys work); the playing line gets `aria-current`; ticks are **not** announced |
| Battery | Timer runs only while playing |
| Two tracks drift apart | Each track counts its own samples. If system audio started late, lines may be off. **Unproven either way: measure on one real meeting before building step 1's "Both"** |
| Search in a recording | Later (M): a find box in the panel, matches marked on the seek bar, like Google Recorder |
| Export a clip | Later (S): "Save this line as audio" with stdlib `wave`. Unproven need |
| Media keys / Control Center | Left out |
| Bookmarks, skip silence | Left out; star and Space cover it |

---

## 8. Build plan

1. **Player core (S-M).** `mac/player.py`: AVAudioPlayer, one at a time, two tracks, speed 0.75 / 1 / 1.25 / 1.5 / 2
   (`enableRate`), seek, tick timer, temp-wav fallback. Pause in `Mic.start`; refuse while a meeting records.
   Replace the `open` call in `window.py`.
2. **Listen panel (M).** Reuse the drawer: controls, seek bar, lines, highlight, click to jump, auto-scroll with
   "Back to the playing line", keys.
3. **Edit a line (S-M).** `edit_line` (text and speaker) with one undo, for meetings and files.
4. **In place (S).** Flags and Fix a word inside lines; Copy line; Play this line.
5. **Dictations (S).** Whole-text highlight; the "No recording kept" message.

Later, only if asked: word timings, search, export a clip.

### Tests

- `tests/test_mac_player.py`: make a 3 s wav with numpy; player loads it, reports length, seeks, changes speed; two
  tracks start within 50 ms; an `.ogg` goes through the fallback.
- `edit_line`: text and segments both change; undo restores both; speaker change keeps timings.
- `Mic.start` pauses a playing player.
- The real window: the existing snapshot request (`window.py` `snapshot`) with the panel open.

### Android parity

- Android already does "tap a paragraph -> Play this part", with the paragraph tinted. That matches step 4.
- Missing there: a whole-note player with follow-along. Its `Player` plays one piece with `AudioTrack` (static mode).
  A whole note needs streaming mode and a position timer. Size M. Do it after the Mac version has been used.
- Keep the words the same on both: "Play this line", "Edit line", "Copy line", "Back to the playing line".
