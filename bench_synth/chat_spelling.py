"""Apply indite's chat-spelling list (the same file the app uses) to a hypothesis TSV.  python3 chat_spelling.py IN.tsv OUT.tsv"""
import re, sys
from pathlib import Path
SPELL = Path(__file__).resolve().parent.parent / "android/app/src/main/res/raw/spelling.tsv"
pairs = dict(l.rstrip("\n").split("\t") for l in SPELL.read_text().splitlines() if l and not l.startswith("#"))
rx = re.compile(r"(?<![\w'])(" + "|".join(map(re.escape, sorted(pairs, key=len, reverse=True))) + r")(?![\w'])", re.I)
def fix(t):
    def rep(m):
        w = m.group(0); c = pairs[w.lower()]
        return c.capitalize() if w[0].isupper() else c
    return rx.sub(rep, t)
if __name__ == "__main__":
    with open(sys.argv[2], "w") as o:
        for line in open(sys.argv[1]):
            k, _, t = line.rstrip("\n").partition("\t"); o.write(f"{k}\t{fix(t)}\n")
