"""Score speech-to-text output against the synthetic benchmark. Stdlib only.

Text (WER/CER):
  python score.py text sentences.tsv HYP
    HYP = JSON lines {"id": "noisy10/s05", "text": "..."} or TSV lines "noisy10/s05<TAB>text".
    The id prefix before "/" is the condition (clean, noisy10, noisy5); no prefix = clean.
Long file (WER + words invented during no-speech stretches):
  python score.py long long_15min_ref.tsv HYP_SEGMENTS
Speaker labels:
  python score.py diar dialogue_turns.tsv HYP_SEGMENTS
    HYP_SEGMENTS = whisper-cli -oj JSON, JSON lines {"start","end","text"[,"speaker"]},
    or TSV "start<TAB>end<TAB>speaker_or_text".
Self-check:  python score.py test
"""
import csv
import itertools
import json
import re
import sys
from collections import defaultdict

SPELL = {"he": "hai", "hain": "hai", "hey": "hai", "nahin": "nahi", "nai": "nahi", "okay": "ok", "okk": "ok",
         "hun": "hoon", "hu": "hoon", "acha": "achha", "accha": "achha", "thik": "theek", "han": "haan",
         "rupees": "rupaye", "rupee": "rupaye", "rupay": "rupaye", "rupiya": "rupaye", "rupiye": "rupaye", "rupe": "rupaye", "rupye": "rupaye",
         "rs": "rupaye", "%": "percent", "mai": "main"}
NUM = {"ek": 1, "do": 2, "teen": 3, "tin": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5, "chhah": 6, "chhe": 6, "che": 6,
       "chah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "gyaarah": 11, "barah": 12, "baarah": 12,
       "pandrah": 15, "bees": 20, "chaubees": 24, "chalis": 40, "chaalis": 40, "pachas": 50, "pachaas": 50,
       "assi": 80, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
       "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
       "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
MULT = {"sau": 100, "hundred": 100, "hazaar": 1000, "hazar": 1000, "hajar": 1000, "thousand": 1000, "lakh": 100000}
# ponytail: number words cover only what sentences.tsv uses (+ common English); extend NUM when adding sentences.


def normalize(text: str) -> list[str]:
    t = text.lower().replace("₹", " ₹ ").replace("%", " percent ")
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    t = re.sub(r"\b(?:rs|inr)\.?\s*(?=\d)", " ₹ ", t)  # "Rs. 640" = "₹640"
    t = re.sub(r"(\d):00\b", r"\1", t)  # "9:00 baje" = "9 baje"
    t = re.sub(r"[^\w₹\s]", " ", t.replace("'", ""))
    words, out, rupee = [SPELL.get(w, w) for w in t.split()], [], False
    i = 0
    while i < len(words):
        w = words[i]
        if w == "₹":
            rupee = True; i += 1; continue
        if w in NUM or w in MULT or w.isdigit():
            total = cur = 0
            while i < len(words) and (words[i] in NUM or words[i] in MULT or words[i].isdigit()):
                v = words[i]
                if v in MULT:
                    cur = max(cur, 1) * MULT[v]
                    if MULT[v] >= 1000:
                        total, cur = total + cur, 0
                else:
                    cur += int(v) if v.isdigit() else NUM[v]
                i += 1
            out.append(str(total + cur))
            if rupee:
                out.append("rupaye"); rupee = False
            continue
        out.append(w); i += 1
    return out


def align(ref, hyp):
    """Levenshtein alignment -> list of (op, ref_index) with op in ok/sub/del, plus insert count."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): d[i][0] = i
    for j in range(m + 1): d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (ref[i-1] != hyp[j-1]))
    ops, ins, i, j = [], 0, n, m
    while i or j:
        if i and j and d[i][j] == d[i-1][j-1] + (ref[i-1] != hyp[j-1]):
            ops.append(("ok" if ref[i-1] == hyp[j-1] else "sub", i - 1)); i -= 1; j -= 1
        elif i and d[i][j] == d[i-1][j] + 1:
            ops.append(("del", i - 1)); i -= 1
        else:
            ins += 1; j -= 1
    return ops, ins


def edits(ref, hyp):
    ops, ins = align(ref, hyp)
    return sum(o != "ok" for o, _ in ops) + ins


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def read_hyp_text(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        if line.lstrip().startswith("{"):
            o = json.loads(line); out[o["id"]] = o.get("text", "")
        else:
            k, _, v = line.partition("\t"); out[k] = v
    return out


def english_words(row):
    """Words written in Latin letters in the TTS column are English (brands included)."""
    return {w for w in normalize(" ".join(re.findall(r"[A-Za-z']+", row["devanagari_for_tts"]))) if not w.isdigit()}


def score_text(ref_path, hyp_path):
    refs = {r["id"]: r for r in read_tsv(ref_path)}
    hyps = read_hyp_text(hyp_path)
    acc = defaultdict(lambda: defaultdict(int))
    for key, htext in hyps.items():
        cond, _, sid = key.rpartition("/")
        cond = cond or "clean"
        if sid not in refs:
            print(f"skip unknown id {key}", file=sys.stderr); continue
        row = refs[sid]
        r, h = normalize(row["roman_text"]), normalize(htext)
        ops, ins = align(r, h)
        eng = english_words(row)
        for c in (cond, "ALL"):
            a = acc[c]
            a["n"] += len(r); a["err"] += sum(o != "ok" for o, _ in ops) + ins; a["ins"] += ins
            rc, hc = " ".join(r), " ".join(h)
            a["cn"] += len(rc); a["cerr"] += edits(list(rc), list(hc)); a["utts"] += 1
            for o, k in ops:
                w = r[k]
                lang = "num" if w.isdigit() else "eng" if w in eng else "hin"
                a[lang + "_n"] += 1; a[lang + "_err"] += o != "ok"
    for c, a in sorted(acc.items(), key=lambda kv: kv[0] != "ALL"):
        pct = lambda e, n: f"{100 * e / n:5.1f}%" if n else "  n/a"
        print(f"{c:8} utts={a['utts']:3}  WER {pct(a['err'], a['n'])}  CER {pct(a['cerr'], a['cn'])}  "
              f"| word errors by ref word (sub+del): Hindi {pct(a['hin_err'], a['hin_n'])} "
              f"English {pct(a['eng_err'], a['eng_n'])} numbers {pct(a['num_err'], a['num_n'])}  insertions {a['ins']}")


def read_segments(path):
    txt = open(path, encoding="utf-8").read()
    if txt.lstrip().startswith("{") and '"transcription"' in txt:  # whisper-cli -oj
        return [{"start": s["offsets"]["from"] / 1000, "end": s["offsets"]["to"] / 1000, "text": s["text"]}
                for s in json.loads(txt)["transcription"]]
    segs = []
    for line in txt.splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("{"):
            segs.append(json.loads(line))
        else:
            a, b, c = line.split("\t")[:3]
            if a == "start":
                continue
            segs.append({"start": float(a), "end": float(b), "speaker": c, "text": c})
    return segs


def score_long(ref_path, hyp_path):
    ref = read_tsv(ref_path)
    segs = read_segments(hyp_path)
    r = normalize(" ".join(x["roman_text"] for x in ref if x["kind"] == "speech"))
    h = normalize(" ".join(s.get("text", "") for s in segs))
    rc, hc = " ".join(r), " ".join(h)
    print(f"long: WER {100 * edits(r, h) / len(r):.1f}%  CER {100 * edits(list(rc), list(hc)) / len(rc):.1f}%  "
          f"(ref {len(r)} words, hyp {len(h)} words)")
    gaps = [(float(x["start"]), float(x["end"]), x["kind"]) for x in ref if x["kind"] != "speech"]
    for a, b, kind in gaps:
        words = [w for s in segs if a <= (s["start"] + s["end"]) / 2 <= b for w in normalize(s.get("text", ""))]
        print(f"  no-speech {kind:7} {a:7.1f}-{b:7.1f}s: {len(words)} words invented {' '.join(words)[:80]!r}")
    print("  (segment counted if its midpoint is inside the stretch; long segments that span a stretch are missed)")


def score_diar(ref_path, hyp_path):
    ref = read_tsv(ref_path)
    segs = read_segments(hyp_path)
    labels = sorted({s["speaker"] for s in segs})
    spk = sorted({x["speaker"] for x in ref})
    over = []  # per ref turn: {hyp_label: overlap seconds}
    for x in ref:
        a, b, o = float(x["start"]), float(x["end"]), defaultdict(float)
        for s in segs:
            o[s["speaker"]] += max(0.0, min(b, s["end"]) - max(a, s["start"]))
        over.append(o)
    best, best_map = -1, {}
    pad = labels + [None] * max(0, len(spk) - len(labels))
    for perm in itertools.permutations(pad, len(spk)):  # one-to-one; extra hyp labels stay unmapped
        m = {h: r for h, r in zip(perm, spk) if h is not None}
        score = sum(o.get(h, 0) for x, o in zip(ref, over) for h, r in m.items() if r == x["speaker"])
        if score > best:
            best, best_map = score, m
    pred = [best_map.get(max(o, key=o.get)) if o and max(o.values()) > 0 else None for o in over]
    ok = sum(p == x["speaker"] for p, x in zip(pred, ref))
    print(f"diar: turns with right majority speaker {ok}/{len(ref)} = {100 * ok / len(ref):.1f}%  map {best_map}")
    pairs = list(zip(range(len(ref) - 1), range(1, len(ref))))
    chg = sum((ref[i]["speaker"] != ref[j]["speaker"]) == (pred[i] != pred[j]) for i, j in pairs)
    print(f"  speaker-change accuracy {chg}/{len(pairs)} = {100 * chg / len(pairs):.1f}%  "
          f"(each turn boundary: did the label change exactly when the real speaker did)")


def test():
    assert normalize("Total ₹640 ho gaya, okay?") == ["total", "640", "rupaye", "ho", "gaya", "ok"]
    assert normalize("Rs. 2,350 aaya") == ["2350", "rupaye", "aaya"]
    assert normalize("chhe sau chaalis rupees") == ["640", "rupaye"]
    assert normalize("do hazaar teen sau pachaas") == ["2350"]
    assert normalize("two thousand three hundred fifty") == ["2350"]
    assert normalize("Nahin, wo he") == ["nahi", "wo", "hai"]
    assert edits("a b c".split(), "a x c d".split()) == 2
    ops, ins = align("a b".split(), "b".split())
    assert ops.count(("del", 0)) == 1 and ins == 0
    print("ok")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    {"text": score_text, "long": score_long, "diar": score_diar}.get(mode, lambda *a: test())(*sys.argv[2:])
