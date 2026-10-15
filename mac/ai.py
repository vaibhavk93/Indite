"""
AI on a note, the same actions as the phone's "Do something with this" sheet, answered by the user's own logged-in
`claude` on this Mac (indite/notes.py runs it: no tools, an empty folder, the transcript marked as data).

⚠ This is the one place text leaves the Mac. The window asks once before the first use and says so.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HINGLISH = ("The text is Hinglish (Hindi and English, written in Roman letters). Keep Roman letters, never "
            "Devanagari, and keep the speaker's mix of Hindi and English unless asked to translate. ")

# key: (label, what you get, group, prompt). Same set as android/.../ui/AiRequests.kt, written separately.
ACTIONS = {
    "improve": ("Improve the wording", "Clearer and tidier, same meaning. Your original stays", "Change the words",
                HINGLISH + "Rewrite it so it reads well: fix punctuation, drop filler words and false starts, and "
                "where the speaker corrected themselves (\"nahi nahi\", \"I mean\", \"actually\") keep only what they "
                "meant. Do not add anything they did not say. Reply with the rewritten text only."),
    "notes": ("Meeting notes", "Decisions, action items, open questions", "Turn it into something to read",
              HINGLISH + "Write meeting notes in Markdown: a two-line summary, Decisions, Action items "
              "(task | who | by when), Open questions. Use only what is in the text; say 'not mentioned' when "
              "something is missing."),
    "actions": ("Action items", "Every task as task | who | by when", "Turn it into something to read",
                HINGLISH + "List every task in the text, one per line, exactly as: task | who | by when. Use '-' "
                "when who or when is not said. No other text. If there are no tasks, reply: none"),
    "summary": ("Summary", "Five short bullets", "Turn it into something to read",
                HINGLISH + "Summarise in at most five short bullets."),
    "lecture": ("Lecture notes", "Topics, key ideas and revision questions", "Turn it into something to read",
                HINGLISH + "Write study notes in Markdown: topics, key ideas under each, then five revision "
                "questions."),
    "braindump": ("Brain dump", "Your thinking out loud, organised", "Turn it into something to read",
                  HINGLISH + "This is someone thinking out loud. Organise it into clear headed sections, keep every "
                  "idea, mark open questions."),
    "rewrite": ("Rewrite to send", "The same thing, in a style you pick", "Change the words",
                HINGLISH + "Rewrite it as a message to send, in this style: {extra}. Reply with the message only."),
    "translate": ("Translate", "The same thing, in another language", "Change the words",
                  "Translate the text into {extra}. Reply with the translation only."),
    "cleanup": ("Clean it up", "Punctuation fixed, the umms removed", "Change the words",
                HINGLISH + "Fix punctuation and remove filler words (umm, matlab, basically, you know) only. Change "
                "nothing else. Reply with the text only."),
}
STYLES = ["Formal English", "Polite request", "WhatsApp Hinglish", "Casual Hinglish", "Email with subject",
          "Short and crisp", "Firm", "Apology", "Thank you"]
LANGUAGES = ["English", "Hindi (Devanagari)", "Hinglish (Roman)", "Marathi", "Gujarati", "Tamil", "Telugu",
             "Bengali", "Kannada", "Punjabi"]


def _path() -> None:
    """An app opened from Finder gets a bare PATH, so `claude` in ~/.local/bin would not be found."""
    extra = [str(Path.home() / ".local/bin"), "/opt/homebrew/bin", "/usr/local/bin"]
    have = os.environ.get("PATH", "").split(":")
    os.environ["PATH"] = ":".join([p for p in extra if p not in have] + have)


def run(action: str, text: str, extra: str = "") -> str:
    """One answer, or raises RuntimeError with a sentence a person can act on."""
    _path()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from indite.notes import ask
    label, _gets, _group, prompt = ACTIONS[action]
    try:
        return ask(prompt.replace("{extra}", extra or "plain English"), text).strip()
    except SystemExit as e:                         # notes.py speaks in SystemExit; the app must not exit
        raise RuntimeError(str(e)) from None


def tasks(answer: str) -> list[str]:
    """'task | who | by when' lines from an Action items answer, as one readable line each."""
    out = []
    for line in answer.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set("".join(cells)) <= set("-: ") or cells[0].lower() in ("task", "none", ""):
            continue
        who, when = (cells + ["-", "-"])[1:3]
        bits = [cells[0]] + [f"{k}: {v}" for k, v in (("who", who), ("by", when)) if v and v != "-"]
        out.append(" · ".join(bits))
    return out


if __name__ == "__main__":       # the one check: python mac/ai.py
    assert tasks("task | who | by when\n|---|---|---|\nSend deck | Rohit | Friday\nBook room | - | -\nnone") == \
        ["Send deck · who: Rohit · by: Friday", "Book room"]
    assert re.search("Roman", ACTIONS["improve"][3])
    print("ok")
