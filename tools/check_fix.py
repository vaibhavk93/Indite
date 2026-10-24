"""
Finds out what inditeflow really hears for the company name in section 3, and writes the fix the demo will teach.

    .venv/bin/python tools/check_fix.py CleverTap

Runs the founder's own S03 recording through the engine that is already loaded, compares what came back with the
name, and writes "<what it heard> = <the real name>" to ~/Documents/inditeflow-demo-voice/fix.txt. If the engine gets the name
right, it says so and writes nothing - then the script needs a different name, because the mistake shown on camera
has to be a real one.
"""
import json, pathlib, subprocess, sys, time

D = pathlib.Path.home() / "Library/Application Support/inditeflow"
VOICES = pathlib.Path.home() / "Documents/inditeflow-demo-voice"
name = sys.argv[1] if len(sys.argv) > 1 else "CleverTap"
src = VOICES / "S03-16k.wav"
if not src.exists():
    sys.exit("S03 is not recorded yet - record it first: .venv/bin/python mac/narrate.py S03")

tmp = pathlib.Path("/tmp/s03check.wav")
tmp.write_bytes(src.read_bytes())
before = len((D / "history.jsonl").read_text().splitlines())
(D / "demo.cmd").write_text(f"file:{tmp}\n")
for _ in range(90):
    time.sleep(2)
    rows = [json.loads(l) for l in (D / "history.jsonl").read_text().splitlines() if l.strip()]
    if len(rows) > before and rows[-1].get("kind") == "file":
        heard = (rows[-1].get("text") or "").strip()
        break
else:
    sys.exit("the engine did not answer in 3 minutes")

print(f"  you said   : ...{name}...")
print(f"  it heard   : {heard}")
if name.lower().replace(" ", "") in heard.lower().replace(" ", ""):
    print(f"\n  It got '{name}' RIGHT. There is no real mistake to show.")
    print("  Pick a different name for S03/S04, or drop the Dictionary beat. Nothing was written.")
    sys.exit(1)
words = heard.split()
guess = " ".join(words[:2]) if words else ""
print(f"\n  Wrong, as hoped. Suggested fix:  {guess} = {name}")
print("  Edit ~/Documents/inditeflow-demo-voice/fix.txt if the wrong words are different from the first two.")
(VOICES / "fix.txt").write_text(f"{guess} = {name}\n")
