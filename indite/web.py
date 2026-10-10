"""Local web app: upload -> background transcription -> editor -> export.

Each job is a folder: data/<id>/audio.<ext>, job.json (status), result.json (transcript).
ponytail: one worker thread, one job at a time (protects 8 GB RAM with the local model);
add a real queue (e.g. arq/Redis) when hosting for many users.
"""
import json
import queue
import subprocess
import re
import shutil
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from .bench import AUDIO_EXT
from .core import ENGINES, available, transcribe
from .styles import STYLES

DATA = Path("data")
KEEP_DAYS = 3 * 365  # founder's choice for now; per-transcript retention is on the roadmap
MAX_BYTES = 1 << 30  # 1 GB upload cap
INDEX = Path(__file__).with_name("index.html")

app = FastAPI(title="indite")
todo: "queue.Queue[Path]" = queue.Queue()


def _write(path: Path, obj) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    tmp.replace(path)  # atomic, so the worker and the API never see half a file


def _job(d: Path) -> dict:
    return json.loads((d / "job.json").read_text())


def _update(d: Path, **changes) -> None:
    _write(d / "job.json", _job(d) | changes)


def _dir(job_id: str) -> Path:
    d = DATA / job_id
    if not re.fullmatch(r"[0-9a-f]{32}", job_id) or not d.is_dir():  # id check blocks path tricks
        raise HTTPException(404, "No such transcript")
    return d


def _audio(d: Path) -> Path:
    return next(d.glob("audio.*"))


def _result(d: Path) -> dict:
    if not (d / "result.json").exists():
        raise HTTPException(409, "Transcript is not ready yet")
    return json.loads((d / "result.json").read_text())


class Cancelled(Exception):
    pass


def plain_error(e: BaseException) -> str:
    """What the user sees. The raw message is kept separately as 'detail'."""
    msg = str(e)
    if type(e).__module__.startswith("av") or isinstance(e, ValueError):
        return "This file couldn't be read. It may be damaged or not an audio file. Re-export it as MP3 or M4A and try again."
    if msg.startswith("whisper.cpp failed"):
        return "The local engine stopped unexpectedly. Try again. If it happens again, the file may be badly damaged."
    if msg.startswith("Sarvam error"):
        code = msg.split()[2].rstrip(":")
        hint = {"401": "Check SARVAM_API_KEY in .env.", "403": "Check SARVAM_API_KEY in .env.",
                "429": "Too many requests. Wait a minute and try again."}.get(code, "Try again later.")
        return f"Sarvam rejected the request (code {code}). {hint}"
    return msg or "Something went wrong. Try again."


def worker() -> None:
    while True:
        d = todo.get()
        if not d.is_dir():  # deleted while waiting
            continue
        preview, last = [], [0.0]

        def progress(stage, fraction, lines, audio_seconds):
            if not d.is_dir():  # user cancelled: the engine stops and kills whisper.cpp
                raise Cancelled
            preview.extend(l.strip() for l in lines if l.strip())
            del preview[:-6]  # keep the latest few lines for the peek view
            now = time.time()
            if lines or now - last[0] > 1 or fraction in (0.0, 1.0):  # at most ~1 write/s
                last[0] = now
                _update(d, status="working", stage=stage, progress=round(fraction, 3),
                        audio_seconds=audio_seconds, preview=preview)

        try:
            _update(d, status="working", stage="reading", started=time.time())
            t = transcribe(_audio(d), _job(d)["engine"], progress=progress).to_dict()
            _write(d / "result.json", t)
            _update(d, status="done", stage="done", progress=1.0, took=round(time.time() - _job(d)["started"], 1),
                    audio_seconds=t["audio_seconds"], damaged_packets=t["damaged_packets"], preview=[])
        except Cancelled:
            pass
        except (Exception, SystemExit) as e:  # engines raise SystemExit with a readable message
            if d.is_dir():
                _update(d, status="error", error=plain_error(e), detail=str(e)[:500])


def cleanup() -> None:
    while True:
        cutoff = time.time() - KEEP_DAYS * 86400
        for d in DATA.glob("*/job.json"):
            if _job(d.parent)["created"] < cutoff:
                shutil.rmtree(d.parent, ignore_errors=True)
        time.sleep(3600)


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX.read_text()


@app.get("/engines")
def engines():
    return available()


@app.post("/jobs")
async def create(file: UploadFile, engine: str = Form("local")):
    ext = Path(file.filename or "").suffix.lower()
    if engine not in ENGINES:
        raise HTTPException(400, f"Unknown engine. Choose one of: {', '.join(ENGINES)}")
    if reason := available()[engine]:
        raise HTTPException(400, f"The {engine} engine isn't ready: {reason}.")
    if ext not in AUDIO_EXT:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Use one of: {', '.join(sorted(AUDIO_EXT))}")
    job_id = uuid.uuid4().hex
    d = DATA / job_id
    d.mkdir(parents=True)
    size = 0
    with open(d / f"audio{ext}", "wb") as f:
        while chunk := await file.read(1 << 20):
            size += len(chunk)
            if size > MAX_BYTES:
                f.close()
                shutil.rmtree(d)
                raise HTTPException(413, "File is over 1 GB. Split it into parts and upload each one.")
            f.write(chunk)
    _write(d / "job.json", {"id": job_id, "name": Path(file.filename).stem, "engine": engine,
                            "status": "queued", "created": time.time()})
    todo.put(d)
    return {"id": job_id}


@app.get("/jobs")
def list_jobs():
    return sorted((_job(p.parent) for p in DATA.glob("*/job.json")), key=lambda j: -j["created"])


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    d = _dir(job_id)
    job = _job(d)
    if (d / "result.json").exists():
        job["result"] = _result(d)
    return job


@app.get("/jobs/{job_id}/audio")
def audio(job_id: str):
    return FileResponse(_audio(_dir(job_id)))


class Edits(BaseModel):
    texts: list[str]


@app.put("/jobs/{job_id}/segments")
def save(job_id: str, edits: Edits):
    d = _dir(job_id)
    result = _result(d)
    if len(edits.texts) != len(result["segments"]):
        raise HTTPException(400, "Segment count changed. Reload the page and try again.")
    for seg, text in zip(result["segments"], edits.texts):
        if text.strip() != seg["text"].strip():
            seg.setdefault("original", seg["text"])  # keep the engine's text: edit rate = our quality signal
            seg["text"] = text.strip()
    result["text"] = " ".join(s["text"].strip() for s in result["segments"] if s["text"].strip())
    _write(d / "result.json", result)
    return {"saved": True}


@app.get("/jobs/{job_id}/export/{style}")
def export(job_id: str, style: str):
    if style not in STYLES:
        raise HTTPException(404, "Unknown style")
    d = _dir(job_id)
    fn, ext = STYLES[style]
    name = _job(d)["name"] + (f".{style}" if ext == ".txt" else "") + ext
    ascii_name = name.encode("ascii", "ignore").decode().replace('"', "").strip() or f"transcript{ext}"
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"  # Hindi names too
    return PlainTextResponse(fn(_result(d)), headers={"Content-Disposition": disposition})


class Ask(BaseModel):
    prompt: str
    text: str
    via: str = "claude"  # or "codex": the founder's ChatGPT plan through his own Codex CLI


ASK_TOKEN_FILE = Path.home() / ".indite_ask_token"


def _ask_token() -> str:
    if not ASK_TOKEN_FILE.exists():
        import secrets
        ASK_TOKEN_FILE.write_text(secrets.token_urlsafe(24))
        ASK_TOKEN_FILE.chmod(0o600)
    return ASK_TOKEN_FILE.read_text().strip()


@app.post("/api/ask")
def ask(body: Ask, authorization: str = Header("")):
    """Personal use only: the founder's phone sends a note + request, this Mac's own `claude -p` answers.
    Reach it from the phone through Tailscale (`tailscale serve --bg 8000`); the server itself stays on 127.0.0.1."""
    import hmac
    from .notes import ask as run
    if not hmac.compare_digest(authorization.removeprefix("Bearer ").strip(), _ask_token()):
        raise HTTPException(401, "Wrong token. Copy it again from the Mac.")
    if len(body.text) > 200_000:
        raise HTTPException(413, "This note is too long to send.")
    try:
        return {"answer": run(body.prompt, body.text, body.via)}
    except SystemExit as e:  # not logged in, out of plan usage, claude missing: say so, don't crash the server
        raise HTTPException(502, str(e))
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "The AI took more than 10 minutes. Try a shorter note.")


@app.delete("/jobs/{job_id}")
def delete(job_id: str):
    """Also cancels: a running job notices its folder is gone and stops whisper.cpp."""
    shutil.rmtree(_dir(job_id))
    return {"deleted": True}


def serve(port: int = 8000) -> None:
    import uvicorn

    DATA.mkdir(exist_ok=True)
    for p in DATA.glob("*/job.json"):  # resume jobs cut off by a restart
        if _job(p.parent)["status"] in ("queued", "working"):
            todo.put(p.parent)
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=cleanup, daemon=True).start()
    print(f"indite running at http://127.0.0.1:{port}  (only this Mac can reach it)")
    print(f"Phone 'Ask my AI' (personal): run `tailscale serve --bg --set-path /api/ask http://127.0.0.1:{port}/api/ask` "
          f"(shares only that one address, not your transcripts), then in the app use your Mac's ts.net address and this token: "
          f"{_ask_token()}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
