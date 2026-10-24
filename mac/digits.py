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


# ---- symbols: ₹ with lakh/crore grouping, %, $, times, emails (founder 24 Oct, D18) -----------------------------------
# Only what the founder's own notes showed ("rupees 1 lakh 25000", "Budget rupe 2 lakh", "80 percent", "example dot com"),
# and only where a word names the money: "2 lakh log" (people) is left alone. Runs after digits(), same switch.
_CUR = r"(?:rs\.?|rupees?|rupe|rupaye|rupay|inr|₹)"
_NUM = r"\d[\d,]*(?:\.\d+)?"
_SCALE = {"lakh": 10 ** 5, "lakhs": 10 ** 5, "lac": 10 ** 5, "lacs": 10 ** 5, "crore": 10 ** 7, "crores": 10 ** 7,
          "hazaar": 1000, "hazar": 1000, "thousand": 1000}
_TERM = rf"(?:{_NUM})(?:\s*(?:{'|'.join(_SCALE)})\b)?"
_AMOUNT = rf"{_TERM}(?:\s+{_TERM})*"


def indian(n: float) -> str:
    """Indian grouping: 125000 -> 1,25,000 (the last three digits, then pairs)."""
    whole, _, frac = f"{n:.2f}".partition(".") if n != int(n) else (str(int(n)), "", "")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r"(?<=\d)(?=(\d\d)+$)", ",", head)
        whole = f"{head},{tail}"
    return whole + ("." + frac if frac else "")


def _value(amount: str) -> float | None:
    """'1 lakh 25000' -> 125000. Each term is a number with an optional scale word; None when it is not an amount."""
    total = 0.0
    for m in re.finditer(rf"({_NUM})(?:\s*({'|'.join(_SCALE)})\b)?", amount, re.I):
        try:
            total += float(m.group(1).replace(",", "")) * (_SCALE[m.group(2).lower()] if m.group(2) else 1)
        except ValueError:
            return None
    return total


def _money(m: re.Match) -> str:
    v = _value(m.group("amt"))
    return m.group(0) if v is None else "₹" + indian(v)


_STOP_BEFORE_DOT = {"a", "the", "an", "this", "that", "my", "your", "our", "of", "in", "on", "to", "and", "or"}


def _dot(m: re.Match) -> str:
    return m.group(0) if m.group(1).lower() in _STOP_BEFORE_DOT else f"{m.group(1)}.{m.group(2)}"


def symbols(text: str) -> str:
    # ₹ before the amount ("rupees 1 lakh 25000", "₹4500") or after it ("2 lakh rupaye")
    text = re.sub(rf"(?<![\w₹])(?:{_CUR})\s*(?P<amt>{_AMOUNT})(?!\s*(?:%|percent))", _money, text, flags=re.I)
    text = re.sub(rf"(?<![\w₹.,])(?P<amt>{_AMOUNT})\s*(?:{_CUR})(?!\w)", _money, text, flags=re.I)
    text = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(?:percent|per cent|pct)\b", r"\1%", text, flags=re.I)
    text = re.sub(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s*(?:dollars?|usd)\b", r"$\1", text, flags=re.I)
    text = re.sub(r"(?<![\w.])(\d{1,2})(?::(\d\d))?\s*([ap])\.?m\b\.?", lambda m: f"{m.group(1)}{':' + m.group(2) if m.group(2) else ''} {m.group(3).upper()}M", text, flags=re.I)
    # emails and sites: "ravi at the rate gmail dot com" -> ravi@gmail.com ; "example dot com" -> example.com
    text = re.sub(r"\b([\w.+-]+)\s+at(?: the)? rate(?: of)?\s+([a-z0-9-]+)\s+dot\s+([a-z]{2,6})(?:\s+dot\s+([a-z]{2}))?\b",
                  lambda m: f"{m.group(1)}@{m.group(2)}.{m.group(3)}" + (f".{m.group(4)}" if m.group(4) else ""), text, flags=re.I)
    # ponytail: "dot com" after any word that is not a filler; "the dot com bubble" is guarded, other phrases are not
    return re.sub(r"\b([\w-]+)\s+dot\s+(com|in|org|net|io|ai|app|co)\b(?!\s+(?:bubble|era|boom|crash))", _dot, text, flags=re.I)


if __name__ == "__main__":       # the one check: python mac/digits.py
    assert digits("Kal meeting chaar baje hai") == "Kal meeting 4 baje hai"
    assert digits("do hazaar tin sau pachaas rupaye") == "₹2350"
    assert digits("client gyaarah baje call karega.") == "client 11 baje call karega."
    for keep in ("tere saath se baat karunga", "ek number ka banda hai", "ek ek karke bhejo", "do na yaar",
                 "das minute mein aata hoon"[:0] or "mujhe ek kaam hai"):
        assert digits(keep) == keep, digits(keep)
    assert digits("das minute mein aata hoon") == "10 minute mein aata hoon"
    for said, want in [("invoice rupees 1 lakh 25000 ka hai.", "invoice ₹1,25,000 ka hai."),      # the founder's own notes
                       ("Budget rupe 2 lakh hai.", "Budget ₹2,00,000 hai."),
                       ("₹4500 ka cab", "₹4,500 ka cab"), ("2 lakh 50 hazaar rupaye", "₹2,50,000"),
                       ("rupees 150", "₹150"), ("3 crore rupees", "₹3,00,00,000"), ("rs. 1,25,000 mila", "₹1,25,000 mila"),
                       ("2 lakh log aaye", "2 lakh log aaye"), ("rupee ka naya note", "rupee ka naya note"),   # no amount: untouched
                       ("80 percent aur 2.5 percent", "80% aur 2.5%"), ("it costs 100 dollars", "it costs $100"),
                       ("call at 3 pm or 10:30 a.m.", "call at 3 PM or 10:30 AM"), ("I am here", "I am here"),
                       ("example dot com par", "example.com par"), ("ravi at the rate gmail dot com", "ravi@gmail.com"),
                       ("the dot com bubble", "the dot com bubble"), ("mail at the rate of 5 percent", "mail at the rate of 5%"),
                       ("tera.n at the rate sharma dot co dot in", "tera.n@sharma.co.in")]:
        assert symbols(digits(said)) == want, (said, symbols(digits(said)))
    assert indian(1234567) == "12,34,567" and indian(999) == "999" and indian(1000) == "1,000"
    print("ok")
