"""App test result JSON -> segments JSONL for score.py (long / diar), plus a timing summary.
   python3 phone_result.py RESULT.json OUT.jsonl"""
import json, statistics, sys
r = json.load(open(sys.argv[1]))
with open(sys.argv[2], "w") as o:
    for p in r["pieces"]:
        if p.get("segs"):  # sentence-level, with per-sentence speakers (v0.6+)
            for s in p["segs"]:
                o.write(json.dumps({"start": s["start"] / 16000, "end": s["end"] / 16000, "text": s["text"],
                                    "speaker": f"S{s.get('speaker', -1)}"}) + "\n")
        else:
            o.write(json.dumps({"start": p["start"] / 16000, "end": p["end"] / 16000, "text": p.get("shown", p["text"]),
                                "speaker": f"S{p.get('speaker', -1)}"}) + "\n")
ms = [p["ms"] for p in r["pieces"] if p.get("ms", -1) >= 0]
eng = [p["engine"] for p in r["pieces"] if p.get("engine", -1) >= 0]
lens = [(p["end"] - p["start"]) / 16000 for p in r["pieces"]]
print(f"{r['name']}: {len(r['pieces'])} parts, avg part {statistics.mean(lens):.1f} s; speed: {r.get('speed')}")
if ms: print(f"  wait after a pause until text: median {statistics.median(ms)/1000:.1f} s, worst {max(ms)/1000:.1f} s")
if eng: print(f"  model time per part: median {statistics.median(eng)/1000:.1f} s")
if "label_ms" in r: print(f"  speaker labelling took {r['label_ms']/1000:.1f} s")
