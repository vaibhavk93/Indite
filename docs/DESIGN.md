# indite design guidelines

**⚠ Remember:** these are our own rules, taken from what indite already looks like. Founder, 17 Oct: "The design
guidelines should be our own." **Before you build any new screen, card or control, read this file. If you add a new
pattern, add it here in the same change.**

---

## 1. The principle

**Calm, Hinglish-first, honest about what stays on the device. It should look like a well-made notes app, not an AI tool.**

- Calm: white paper, grey ink, one orange. Nothing glows, nothing shouts.
- Hinglish-first: examples, sample text and labels use real Roman Hinglish ("Kal 3 baje meeting hai…").
- Offline-honest: say plainly when something stays on the device and when text leaves it (AI routes).

---

## 2. Not us

These patterns are common in AI products. Avoid them unless there is a written reason.

| Avoid | Why | Our way instead |
|---|---|---|
| Purple or blue gradients | The generic AI-tool look | Flat paper; orange only in small spots |
| Sparkles ✨ everywhere | Says "magic", hides what happened | A plain verb: "Summary", "Make it a prompt" |
| Emoji as icons | Uneven, childish at small sizes | Our own line icons (SVG / drawables) |
| Chat bubbles for non-chat things | A note is a document, not a chat | Answers as plain documents (`.doc`) |
| Glowing cards, coloured tints | Founder #224: "AI-vibe-coded"; glows removed app-wide | Hairline border or sunken `--well` |
| Every block the same rounded card | Research: sameness reads as "AI-made" | Plain rows with dividers; cards only for groups |
| Typewriter text animation | Fake, slow; the text is already done | Show the whole answer when it lands |
| "AI magic", "supercharge", "effortless" | Hype; not true for a 9 s offline wait | Say what it does and how long it takes |
| Dark-mode-only neon | Founder asked for white | Light by default; dark is a matched option |

**Note:** one deliberate exception. **The gold AI chip** (`.aichip.has`, `--gold`) marks a note that has AI work, so
it is findable at a glance (founder #231). Gold edge + gold icon only. No fill, no glow. "AI is writing…" stays grey.
Keep gold for that one meaning. Do not spread it to buttons or headings.

---

## 3. Tokens

### Mac colours (`mac/ui/app.html`, `:root`)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--brand` | `#e27619` | same | Dots, switches, bars, focus ring. **Never small text** |
| `--accent` | `#b85a0c` | `#f0903f` | Orange text, picked nav icon (4.6:1 on white) |
| `--accent-soft` | `#fdf1e6` | orange 16 % | Banners, the word being spoken in Listen, Copied tag |
| `--gold` / `--gold-soft` | `#a8812a` / 10 % | `#d4b062` / 12 % | The AI chip only |
| `--paper` | `#ffffff` | `#1e1e20` | The page |
| `--ink` / `--ink2` / `--ink3` | `#1d1d1f` / `#5f5f66` / `#737379` | `#f2f2f4` / `#a8a8b0` / `#8e8e95` | Text: main, secondary, faint. All pass WCAG AA (the contrast standard) |
| `--line` / `--line2` | `#ececef` / `#e2e2e6` | `#2c2c30` / `#36363b` | Dividers, borders |
| `--well` / `--hover` | `#f4f4f6` / `#f7f7f9` | `#2a2a2d` / `#252528` | Sunken areas, hover |
| `--who2` / `--who3` | `#2f6fb3` / `#7a4fb3` | `#6ea8e8` / `#b28be6` | Speaker names (others, a 2nd/4th person); "You" uses `--accent`. One helper: `whoCls()` |
| `--red` | `#c4372a` | `#ff6b5e` | Recording, delete, errors only |
| `--shadow` | two 4 % shadows | none | Settings cards only |

Themes: `data-theme="light"` (default), `"dark"`, or `"system"`. The sidebar is the only see-through part.

### Android colours (`ui/theme/Color.kt`)

Warm paper and ink, one amber, red only for recording. Light: `Paper #FAF7F2`, `Ink #1C1814`, `InkSoft #6E655B`,
`Line #E6DFD5`, `Amber #B45A16`. Dark: `Night #131110`, `Chalk #F4EFE8`, `AmberBright #F2A65A`. `RecordRed #E5484D`.
Dynamic colour (Material You) is **off**: our colours on every phone.

### Type

| | Mac | Android (`Type.kt`) |
|---|---|---|
| Family | System font (SF Pro) | Figtree, bundled (no internet) |
| Body | 13 px / 1.5; note text 14 px | `bodyLarge` 17/27, `bodyMedium` 15/22 |
| Page title | `h1` 22 px, 650, −0.5 tracking | `headlineMedium` 28/34, 700 |
| Section label | 12 px, 600, `--ink2` | `labelLarge` 15/20, 600 |
| Big number | `.kpi .n` 24 px, 650 | `displaySmall` 34/40 |
| Numbers | `.num` = tabular figures | — |

### Spacing, radii, depth

- Mac page gutter 32 px; reading width capped at 980 px. Android gutter 20 dp, onboarding 28 dp.
- Mac radii: 6-7 px small controls, 8-10 px fields and inner groups, 12 px tiles and boxes, 20 px pills and chips.
- Android radii: 14-18 dp cards and buttons, 24 dp for the largest.
- Depth: mostly none. Hairline borders first, then `--well`. Real shadow only on the drawer, toast and settings cards.
- **Glass is for floating things only**: the Mac sidebar and the pill. Never on page content.

---

## 4. Components

| Need | Use | Rule |
|---|---|---|
| Switch pages | `nav button` | Picked = `--side-pick` fill + orange icon |
| A list of notes | `.row` | Plain rows, divider line, hover fill. Not cards |
| Two to four choices | `.seg` | Picked segment turns white |
| Filter | `.chip` | Pressed = `--well` |
| Main action | `.btn.go` | Ink fill. One per view |
| Other actions | `.btn`, `.btn.danger` | Hairline border |
| Quiet action | `.lnk` | Grey text, underline on hover |
| Tell once, then go | `.toast` | Bottom centre; name what happened. Stays ~60 ms per character (1.8-8 s); 5 s with Undo |
| Needs attention | `.banner` | `--accent-soft`, one line + one button |
| Nothing here yet | `.empty` | Icon in a well, a heading, a next step |
| Menu-bar icon | `menubar_icon()` | indite's five bars as a template image (macOS colours it); status as short text beside it: ⚠ … ● 3/10. Never emoji |
| Work on one note | `.drawer` | Right side, tabs **Ask AI \| Listen** (`.dtabs`) |
| Play a recording | `.plisten` | Looks like the note list: 22 px gutter, `.who` speaker colours, 14 px text, hairline rows. Player = one `--well` strip (round ink play button, thin orange-fill slider). Line being spoken = `--well`; word being spoken = `--accent-soft` + `--accent`. Line actions = `.copy` icons on hover (play, copy, pen). No orange box or bar (founder, 17 Oct) |
| Settings | `.card` + `.item` | Grouped, label left, control right; with no room the control drops under the label (label ≥ 220 px) |
| Menus | `popup()` | One short line per item; the explanation goes in the hover title |

### Copy (founder #269, #270)

- **One copy icon (`.copy`), on the text it copies.** Not a second Copy button somewhere else.
- On click it turns into ✓ in place (`.copy.done`). The toast says plainly what was copied ("Summary copied").
- Words and AI answers already go to the clipboard when they land. Do not add copy UI the clipboard covers.

### Charts and Insights (founder #267: his rebuild was rolled back)

- **Keep the page he knows. Add and group; do not redesign.**
- Stat tiles (`.kpi`): number, label, optional change in green/red. **Hide a tile that has no data.**
- Bars (`.bars`) for time; horizontal bars (`.hbar`) for rankings. Orange marks on a `--well` track.
- No pie charts with more than 4 parts. No charts with two y-axes. Typical and slow values beat an average.

### The pill (`mac/overlay.py`)

- 116 × 30 pt, real macOS glass (Liquid Glass on macOS 26), hairline rim, user-set see-through level.
- **⚠ Remember: it never takes focus and never catches a click.** Otherwise your words go nowhere.
- Shows full strength at once (fades were throttled to invisible, 16 Oct). Leaves with a ~400 ms fade.

### The text card (`Preview` in `mac/overlay.py`)

- 460 pt wide, grows upward with the text, up to 320 pt. A long dictation keeps its end; an answer keeps its start.
- On screen 4 s + 0.25 s per word, **never more than 6 s** (`CAP`). The pointer resting on it keeps it up.
- Buttons: Ask AI, two favourite actions, To do. Clicks count only after the pointer moves onto the card.
- **Dependent settings (24 Oct, founder):** a setting that only matters when another is on sits **indented under it** and,
  when the parent is off, is **disabled, not hidden**: dimmed, not clickable, and its line says why ("Turn on “AI
  buttons on the card” to choose."). Done for the card's AI buttons and the two button pickers (`dep()` in `app.html`).
- **Button states (24 Oct, founder):** resting = clear with a hairline; **hover = ink at 9 %**, **pressed = ink at 20 %**
  (`button_look` in `overlay.py`). The tint shows only while a click would count (pointer has moved onto the card), so a
  button never looks clickable when it is not. **Working:** when an AI action runs, the buttons give way to the action's
  name with dots that cycle (`.` `..` `...`) and a gentle fade (55-100 %), until the answer lands ("Copied. Paste it
  anywhere.") or the failure reason appears. Motion says "busy"; nothing moves for decoration.

---

## 5. Words

- Plain and short. Say what happens: "Copied", "Saved", "Working… you can close this".
- Be honest about AI: name where text goes ("leaves the Mac for your AI"), how long it takes, and when it failed.
- Be honest about privacy: "stays on this phone" only when that is true.
- No hype words. No "magic". No exclamation marks.
- Hinglish examples come from real speech, not made-up English.
- One name per thing (copy review, 17 Oct): **Dictionary** (never "word fixes"), **talk key** in sentences
  ("Hold-to-talk key" only as the setting), **Ask AI**, **Save my dictations**, **card** (never "text box" for it).
- Mac words: click, not tap. Curly quotes and apostrophes (“ ” ’). Two short sentences instead of a " - " dash.
- Name the AI service in sentences as Claude / Anthropic / OpenAI / OpenRouter (`ai.NAMES`), not the menu label.

---

## 6. Motion

- **Motion must tell you something**: a state changed, a thing arrived, the app is busy. No motion for decoration.
- Mac timings are short: 0.16-0.2 s (toast, switch, drawer slide-in, the pill's 0.2 s word fade).
- Busy states pulse gently (`.working`, `.ndot`, the pill's dots). A real progress bar beats dots when we know progress.
- Mac: `prefers-reduced-motion` stops every loop. Android: everything obeys Settings → "Remove animations".
- Research note (ROADMAP "Look-and-feel top 10"): no motion at all also reads as "AI-made". Add purposeful motion
  (screen transitions, a "done" tick with a buzz, the Record button spring), not none.

---

## 7. Mac vs Android: allowed differences

| | Mac | Android |
|---|---|---|
| Paper | Pure white | Warm off-white `#FAF7F2` |
| Font | System font | Figtree |
| Glass | Sidebar, pill, card | None |
| Input | Hover, keyboard, focus ring | Swipe (right = copy, left = delete), long-press menu, haptic buzz |
| Density | Compact, 13 px | Larger, thumb-sized |

Shared everywhere: one orange family, red only for recording and danger, plain words, gold only for AI work.

---

## 8. Before any new UI ships

1. Does it use the tokens above, with no new colour, radius or font size?
2. Is it on the "Not us" list? If yes, is the reason written down?
3. Does it look right in light and dark?
4. Does every grey or orange text pass contrast (no `--brand` for small text)?
5. Does it work with reduced motion or "Remove animations" on?
6. Do the words say plainly what happens, with no hype?
7. Does copy stay one icon on the text it copies?
8. On the Mac pill or card: does it still never take focus or catch a stray click?
9. **No bare hex in a stylesheet.** Every colour comes from `var(--…)`. If you need a new shade, add it as a token first.
10. **No `opacity:` to dim text.** Use `--ink-dim` (secondary on `--well`) or a semantic state token.
11. **No browser `title=` on buttons.** Use `data-tt="…"` — the themed `.tt` component renders it.
12. **Menu rows carry their own subtitle** (`<b>Label</b><span>subtitle</span>`). No tooltip.
13. **One primary button per view**, class `.btn`. Everything else is `.btn.ghost`, `.btn.quiet` or `.btn.danger`.
14. **Pill and card copy comes from the state map** in `overlay.py` / `indite_mac.py`. No inline strings in the handler.

**When you create something new: read this file first, and add any new pattern to it.**

---

## 9. Theme pass v2 — the patterns added 24 Oct 2026

Ten commits (`bfb3f06 … 0db764b`) formalised what used to be ad-hoc. The vocabulary below is the one every new UI should reach for; the old vocabulary is gone from the codebase.

### 9.1 Tokens added

| Token | Light | Dark | Use |
|---|---|---|---|
| `--ink-dim` | `#8e8e95` | `#737379` | Secondary text on `--well`. **Replaces `opacity: 0.6` on text.** |
| `--state-busy` | `#5f5f66` | `#a8a8b0` | "Warming / working / saving" — grey, not orange |
| `--state-done` | `#2e8b47` | `#34a853` | Confirmation ticks (promoted from literal) |
| `--state-idle` | `#737379` | `#5f5f66` | "AI off / mic off" — grey, not red |
| `--panel-edge` | `rgba(0,0,0,.14)` | `#36363b` | Shelf / drawer edge where a shadow disappears in dark |
| `--tt-paper` | `#0f0f10` | `#0a0a0b` | Tooltip background — one place to adjust |

### 9.2 Scales added

- **Icon size**: `--i-sm 14`, `--i-md 18`, `--i-lg 28`. Collapses the previous 7 ad-hoc sizes (12–28). Use these on `<svg width=…>`.
- **Typography utility classes**: `.t-label` (11 px / 600 / 0.08 em uppercase), `.t-caption` (12 px / 500), `.t-body` (13 px / 1.5), `.t-h3` (15 px / 600), `.t-h2` (20 px / 650), `.t-h1` (24 px / 650). Named by role, not by size — a future scale shift changes one block.

### 9.3 Components formalised

| Component | Class | What it is |
|---|---|---|
| Button family | `.btn` / `.btn.ghost` / `.btn.quiet` / `.btn.danger` + `.btn.big` size variant | One vocabulary across every page. `.btn.go` kept as a one-line alias of `.btn` for out-of-tree patterns |
| Themed tooltip | `.tt` + `data-tt="…"` on any element | Delegated listener; 200 ms delay; positions below the target, flips above when it would clip. Replaces every `title=` on buttons |
| Menu row with subtitle | `<button><b>Label</b><span>subtitle</span></button>` inside `.menu` | `popup()` renders items this way. No browser tooltip; the subtitle is always visible |
| Input select / slider / text | `.pick` (select or text), `.slide` (range) | Already in use; formalised. Models like free-form configuration prefer `<select>` + Custom… over a free input |
| Shelf (combine notes) | `.shelf` + `.row .shelf-add` on each row | A right-side panel; drag-reorder; live preview; "Save as a note" vs "Save & Ask AI" |
| Cost chip | `.aicost` on each AI answer header | Known cost shows "$0.012"; unknown model shows "cost not estimated"; local-Claude answers show no chip |

### 9.4 State vocabulary

The pill's state → word mapping lives in `overlay.py`'s `_draw_content`. The card's `preview.show(text, buttons)` / `preview.ask()` / `preview.failed()` / `preview.answer()` keep the same shape; failure now routes a one-line reason onto the card at the moment it happens.

| Moment | What appears |
|---|---|
| Cold-start waiting (engine not ready) | pill: **"warming up…"** |
| Normal waiting after dictation | pill: "writing…" |
| Dictation typed in | pill: ✓ typed in |
| Clipboard fallback | pill: ✓ copied · card teaches "No text box — paste with ⌘V" |
| Dictation failed | pill: "didn't work · check the card" · card carries the reason |
| Meeting recording | pill: red dot + REC + time |
| AI thinking | drawer: animated bar + "Usually about N s" (unchanged — one of the strongest moments in the app) |
| Meeting record blocked by dictation | toast: "Finish the current dictation first." |

### 9.5 AI cost

- Per-answer `.aicost` chip on each AI reply header
- Monthly total line on Insights: **"This month: $X.XX across N answers · M answered via Claude on this Mac (no cost reported)"**
- Model picked from a `<select>` populated from `cost.py`'s RATES keys plus "Custom…"
- `cost.py` is strict: unknown model returns `None`, not `$0.00`

**Rates are 2026 published numbers.** `cost.py` says so at the top; keep them current.
