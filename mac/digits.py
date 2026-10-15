"""
Number words → digits, after the engine ("chaar baje" → "4 baje", "do hazaar tin sau pachaas rupaye" → "₹2350").

Measured 15 Oct on 360 bench clips: numbers written as Hindi words were 21% of all wrong words, and this pass took
the clean set from 18.7% to 14.4% wrong (with the punctuation fix). Unproven on real use: it changed 0 of the
founder's 53 dictations. Words that are also ordinary words (ek = a, do = give, das, saath = with, tin...) are only
converted next to a counting word (baje, percent, rupaye...), so "ek number ka banda", "ek ek karke" and
"tere saath se" are left alone. Settings → Numbers as digits turns it off.
"""

from __future__ import annotations

import re

ONES = {"ek": 1, "do": 2, "teen": 3, "tin": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhah": 6, "chhe": 6,
        "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "gyaarah": 11, "barah": 12, "baarah": 12,
        "terah": 13, "chaudah": 14, "pandrah": 15, "pandraah": 15, "solah": 16, "satrah": 17, "atharah": 18,
        "unnis": 19, "bis": 20, "bees": 20, "ikkis": 21, "baais": 22, "teis": 23, "chaubis": 24, "chaubees": 24,
        "pachchis": 25, "tees": 30, "chalis": 40, "chaalis": 40, "pachaas": 50, "pachas": 50, "sattar": 70,
        "assi": 80, "nabbe": 90}
COUNTING = {"baje", "percent", "tarikh", "minute", "minat", "rupaye", "rupay", "rupees", "sau", "hazaar", "hazar",
            "strip", "tickets", "ticket", "number", "ghante", "din", "saal"}
AMBIGUOUS = {"ek", "do", "das", "saath", "tin", "so", "char", "sat"}


def digits(text: str) -> str:
    w, out, i = text.split(), [], 0

    def bare(x: str) -> str:
        return re.sub(r"[^\w]", "", x).lower()

    while i < len(w):
        b = bare(w[i])
        if b not in ONES:
            out.append(w[i])
            i += 1
            continue
        nxt = bare(w[i + 1]) if i + 1 < len(w) else ""
        prv = bare(w[i - 1]) if i else ""
        if b in AMBIGUOUS and ((nxt not in COUNTING and prv not in ("number", "no")) or (b == "ek" and nxt == "number")):
            out.append(w[i])
            i += 1
            continue
        val, j = ONES[b], i + 1
        if j < len(w) and bare(w[j]) == "sau":
            val, j = val * 100, j + 1
            if j < len(w) and bare(w[j]) in ONES:
                val, j = val + ONES[bare(w[j])], j + 1
        elif j < len(w) and bare(w[j]) in ("hazaar", "hazar"):
            val, j = val * 1000, j + 1
            if j + 1 < len(w) and bare(w[j]) in ONES and bare(w[j + 1]) == "sau":
                val, j = val + ONES[bare(w[j])] * 100, j + 2
            if j < len(w) and bare(w[j]) in ONES:
                val, j = val + ONES[bare(w[j])], j + 1
        last = w[j - 1]
        out.append(str(val) + (re.sub(r"^\w+", "", last) if not last[-1].isalnum() else ""))
        i = j
    return re.sub(r"\b(\d+)\s+(rupaye|rupay|rupees|rupee)\b", r"₹\1", " ".join(out), flags=re.I)


if __name__ == "__main__":       # the one check: python mac/digits.py
    assert digits("Kal meeting chaar baje hai") == "Kal meeting 4 baje hai"
    assert digits("do hazaar tin sau pachaas rupaye") == "₹2350"
    assert digits("client gyaarah baje call karega.") == "client 11 baje call karega."
    for keep in ("tere saath se baat karunga", "ek number ka banda hai", "ek ek karke bhejo", "do na yaar",
                 "das minute mein aata hoon"[:0] or "mujhe ek kaam hai"):
        assert digits(keep) == keep, digits(keep)
    assert digits("das minute mein aata hoon") == "10 minute mein aata hoon"
    print("ok")
