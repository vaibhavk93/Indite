"""Full web flow with the local engine. Run: uv run python tests/test_web.py (needs scripts/setup_local.sh once)."""
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from indite import web


def test_flow():
    web.DATA = Path(tempfile.mkdtemp())
    threading.Thread(target=web.worker, daemon=True).start()
    c = TestClient(web.app)
    audio = Path(tempfile.mkdtemp()) / "talk.aiff"
    subprocess.run(["say", "-o", str(audio), "Tomorrow we have a meeting at ten."], check=True)

    assert "indite" in c.get("/").text
    assert c.post("/jobs", files={"file": ("x.exe", b"MZ")}, data={"engine": "local"}).status_code == 400
    assert c.get("/jobs/../../etc").status_code == 404
    assert c.get("/jobs/" + "0" * 32).status_code == 404

    job_id = c.post("/jobs", files={"file": ("talk.aiff", audio.read_bytes())}, data={"engine": "local"}).json()["id"]
    for _ in range(120):
        job = c.get(f"/jobs/{job_id}").json()
        if job["status"] in ("done", "error"):
            break
        time.sleep(1)
    assert job["status"] == "done", job
    assert "meeting" in job["result"]["text"].lower()
    assert c.get(f"/jobs/{job_id}/audio").status_code == 200

    n = len(job["result"]["segments"])
    assert c.put(f"/jobs/{job_id}/segments", json={"texts": ["kal meeting hai"] * n}).json() == {"saved": True}
    seg = c.get(f"/jobs/{job_id}").json()["result"]["segments"][0]
    assert seg["text"] == "kal meeting hai" and "meeting" in seg["original"].lower()
    assert c.put(f"/jobs/{job_id}/segments", json={"texts": []}).status_code == 400

    srt = c.get(f"/jobs/{job_id}/export/srt")
    assert srt.text.startswith("1\n00:00:00,000") and 'filename="talk.srt"' in srt.headers["content-disposition"]
    assert c.get(f"/jobs/{job_id}/export/nope").status_code == 404

    assert c.delete(f"/jobs/{job_id}").json() == {"deleted": True}
    assert c.get("/jobs").json() == []


if __name__ == "__main__":
    test_flow()
    print("ok")
