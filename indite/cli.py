import argparse
import json
from pathlib import Path

from . import bench
from .core import ENGINES, transcribe
from .styles import STYLES


def main():
    p = argparse.ArgumentParser(prog="indite", description="Hinglish-first speech-to-text")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("transcribe", help="transcribe an audio/video file, or re-style a saved .indite.json")
    t.add_argument("file", type=Path)
    t.add_argument("--engine", choices=ENGINES, default="local")
    t.add_argument("--model", help="override the engine's default model")
    t.add_argument("--style", choices=STYLES, default="timestamped",
                   help="srt/vtt = subtitles, timestamped = interviews & calls, paragraphs = lectures & notes")

    b = sub.add_parser("bench", help="score engines on hand-typed clips")
    b.add_argument("clips", type=Path)
    b.add_argument("--engine", choices=ENGINES, nargs="+", default=list(ENGINES))

    sv = sub.add_parser("serve", help="run the web app on this Mac")
    sv.add_argument("--port", type=int, default=8000)

    n = sub.add_parser("notes", help="meeting notes using your own Claude or ChatGPT (Codex) login (experimental)")
    n.add_argument("file", type=Path, help="a .indite.json transcript")
    n.add_argument("--via", choices=["claude", "codex"], default="claude")

    a = p.parse_args()
    if a.cmd == "notes":
        from .notes import notes

        if not a.file.name.endswith(".indite.json"):
            raise SystemExit("Give a .indite.json file. Run 'indite transcribe' on the audio first.")
        md = notes(json.loads(a.file.read_text()), a.via)
        out = a.file.with_name(a.file.name.removesuffix(".indite.json") + ".notes.md")
        out.write_text(md)
        print(md + f"\n[notes via your own {a.via} login · saved {out.name}]")
        return
    if a.cmd == "serve":
        from .web import serve

        serve(a.port)
        return
    if a.cmd == "bench":
        print(bench.table(bench.run(a.clips, a.engine)))
        return

    if a.file.name.endswith(".indite.json"):  # re-style without transcribing (or paying) again
        result = json.loads(a.file.read_text())
        stem = a.file.with_name(a.file.name.removesuffix(".indite.json"))
    else:
        result = transcribe(a.file, a.engine, a.model).to_dict()
        stem = a.file.with_suffix("")
        Path(f"{stem}.indite.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))

    fn, ext = STYLES[a.style]
    out = Path(f"{stem}.{a.style}{ext}" if ext == ".txt" else f"{stem}{ext}")
    out.write_text(fn(result))
    print(fn(result))
    flagged = sum(1 for s in result["segments"] if s.get("flags"))
    print(f"[{result['engine']} · {result['audio_seconds']:.0f}s audio in {result['elapsed_seconds']:.1f}s"
          f" · {flagged} part(s) to check · saved {out.name}]")


if __name__ == "__main__":
    main()
