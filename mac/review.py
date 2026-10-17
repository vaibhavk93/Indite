"""
Mark likely mistakes in a dictation, offline (roadmap Mac next #3; design: docs/WISPR_DEEPDIVE.md §2, option A1).

A Dictionary word ("Crocin", "CleverTap") that the engine wrote as something that SOUNDS like it ("cross in") is
flagged - but only where the engine itself was unsure of the words (per-word confidence below GATE). Without that
gate the same check raised 1.9 false alarms per 100 words on the synthetic bench; with it, 0.4 (16 Oct). Nothing is
ever changed here: this only finds candidates; the person decides.
"""

from __future__ import annotations

import difflib
import re

GATE = 0.9          # look only where the engine was less sure than this
SIMILAR = 0.85      # how alike two phonetic keys must be
MIN_LEN = 6         # shorter Dictionary words collide with everyday words ("call" vs "chalo")

# Wispr's skip list, by kind: these are never "near misses" of a name (docs/WISPR_DEEPDIVE.md §2.1)
EVERYDAY = set("""
the and for that this with have from your what when will would there their about which could should because
hai hain tha thi kya nahi nahin bhi aur kar karo karna kal aaj abhi maine mujhe mera meri hum tum aap yeh woh
please thank thanks okay sorry right just like really actually also
""".split())


def key(text: str) -> str:
    """
    A rough Hinglish sound-key: "Crocin" and "cross in" come out alike. Collapses long vowels, aspirates, soft c ("ci" sounds "si"), v/w, s/sh,
    z/j and double letters, then drops vowels after the first letter. Stock Soundex is for English names and
    over-collides on Indian ones, so this is hand-rolled.
    """
    s = re.sub(r"[^a-z]", "", text.lower())
    for a, b in (("x", "ks"), ("aa", "a"), ("ee", "i"), ("oo", "u"), ("ph", "f"), ("kh", "k"), ("gh", "g"),
                 ("chh", "C"), ("ch", "C"), ("ci", "si"), ("ce", "se"), ("ck", "k"), ("c", "k"), ("q", "k"),
                 ("th", "t"), ("dh", "d"), ("bh", "b"), ("jh", "j"), ("sh", "s"), ("w", "v"), ("z", "j")):
        s = s.replace(a, b)
    s = re.sub(r"(.)\1+", r"\1", s)
    return s[:1] + re.sub(r"[aeiouy]", "", s[1:]) if s else ""          # "C" is the ch sound, kept apart from k


PARTICLES = set("ka ki ke ko ne se mein me hai kar par pe aur toh to".split())   # Hindi joining words: never part of a name


def skip(span: str) -> bool:
    """Numbers, links, paths, codes and everyday words are never flagged; nor a join that holds a Hindi particle."""
    w = [x.strip(".,!?") for x in span.lower().split()]
    return (any(c.isdigit() for c in span) or "/" in span or "@" in span or "." in span.strip(".,!?")
            or all(x in EVERYDAY for x in w) or (len(w) > 1 and any(x in PARTICLES for x in w)))


def flags(words: list[tuple[str, float]], targets: list[str]) -> list[dict]:
    """
    words: the engine's words with confidence, in order. targets: the Dictionary's "you meant" side.
    Returns non-overlapping {"heard", "want", "start", "end"} - start/end index into words - best match first.
    """
    targets = [t for t in dict.fromkeys(targets) if len(re.sub(r"[^A-Za-z]", "", t)) >= MIN_LEN]
    keys = {t: key(t) for t in targets}
    found = []
    for i in range(len(words)):
        for n in (1, 2, 3):                                   # joins: "cross in" -> "Crocin"
            if i + n > len(words):
                break
            span_words = words[i:i + n]
            if min(p for _, p in span_words) >= GATE:          # the engine was sure: leave it alone
                continue
            span = " ".join(w for w, _ in span_words).strip(" ,.!?")
            if not span or skip(span):
                continue
            k = key(span)
            for t in targets:
                if span.lower().replace(" ", "") == t.lower().replace(" ", ""):
                    continue                                   # already right
                r = difflib.SequenceMatcher(None, k, keys[t]).ratio()
                if r >= SIMILAR:
                    found.append((r, i, i + n, span, t))
    out, used = [], set()
    for r, a, b, span, t in sorted(found, reverse=True):
        if used.isdisjoint(range(a, b)):
            used.update(range(a, b))
            out.append({"heard": span, "want": t, "start": a, "end": b})
    return sorted(out, key=lambda f: f["start"])


def on_text(text: str, conf: list[tuple[str, float]], targets: list[str]) -> list[dict]:
    """
    Flags in the SAVED text. The engine's second listen (the one with confidence) can come out differently -
    "crasin" typed, "crossin" when asked again (16-17 Oct) - so its words only say which words were heard clearly:
    a saved word counts as sure only if the second listen heard the same word with confidence >= GATE.
    """
    norm = lambda w: re.sub(r"[^\w]", "", w.lower())
    sure = {norm(w) for w, p in conf if p >= GATE}
    return flags([(w, 1.0 if norm(w) in sure else 0.0) for w in text.split()], targets)


if __name__ == "__main__":        # the rules: python mac/review.py
    assert key("Crocin") == key("cross in")
    w = [("Mujhe", 1.0), ("cross", 0.4), ("in", 0.6), ("chahiye", 1.0)]
    assert flags(w, ["Crocin"]) == [{"heard": "cross in", "want": "Crocin", "start": 1, "end": 3}]
    assert flags([("cross", 0.99), ("in", 0.99)], ["Crocin"]) == []            # the engine was sure: no flag
    assert flags([("Crocin", 0.5)], ["Crocin"]) == []                          # already right
    assert flags([("call", 0.3)], ["Chalo"]) == []                             # too short to be a target
    assert flags([("12", 0.2), ("baje", 0.5)], ["Twelve"]) == []                # numbers are skipped
    assert flags([("kar", 0.5), ("ne", 0.5)], ["Crocin"]) == []                 # a join with "ne" is not a name
    conf = [("Haan,", 0.6), ("chemist", 0.99), ("crossin", 0.14), ("le", 0.99)]
    assert on_text("Haan, chemist crasin le", conf, ["Crocin"]) == [{"heard": "crasin", "want": "Crocin", "start": 2, "end": 3}]
    sure = [("Haan,", 0.99), ("chemist", 0.99), ("crasin", 0.99), ("le", 0.99)]
    assert on_text("Haan, chemist crasin le", sure, ["Crocin"]) == []         # heard clearly both times: left alone
    print("ok")
