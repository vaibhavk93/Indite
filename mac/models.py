"""
Which AI models and effort levels can be chosen (founder request, 24 Oct 2026).

Live where a provider can say what it has:
  - Anthropic: GET /v1/models lists every model with the effort levels it supports (needs an API key).
  - OpenAI: GET /v1/models lists model ids (no effort information).
The Claude login (the `claude` CLI) has no listing call and OpenRouter has hundreds of models, so those use the
built-in table below, copied from Anthropic's docs on 24 Oct 2026. It is a starting point, not live: a model Anthropic
adds later appears here only after a refresh with an API key (or an update of this table).

The last answer from each provider is kept in models.json in indite's data folder, so Settings opens without a network
call. Only model ids and names are stored, never keys.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

import store

LEVELS = ("low", "medium", "high", "xhigh", "max")
_NO_XHIGH = ("low", "medium", "high", "max")

# id, name, effort levels (Anthropic effort docs, 24 Oct 2026). Haiku 4.5 has no effort setting.
BUILTIN = [
    ("claude-fable-5-1", "Fable 5.1", LEVELS), ("claude-fable-5", "Fable 5", LEVELS),
    ("claude-opus-5-5", "Opus 5.5", LEVELS), ("claude-opus-5", "Opus 5", LEVELS),
    ("claude-opus-4-8", "Opus 4.8", LEVELS), ("claude-opus-4-7", "Opus 4.7", LEVELS),
    ("claude-opus-4-6", "Opus 4.6", _NO_XHIGH), ("claude-opus-4-5-20251101", "Opus 4.5", ("low", "medium", "high")),
    ("claude-sonnet-5-5", "Sonnet 5.5", LEVELS), ("claude-sonnet-5", "Sonnet 5", LEVELS),
    ("claude-sonnet-4-6", "Sonnet 4.6", _NO_XHIGH),
    ("claude-haiku-5-5", "Haiku 5.5", LEVELS), ("claude-haiku-4-5", "Haiku 4.5", ()),
]
# What `claude --model` accepts for "the latest of this kind", and "" = whatever the account uses. The real model
# behind them is unknown here, so all levels are offered; the CLI uses the highest one the model supports.
ALIASES = [("", "Claude’s default for your account", LEVELS), ("haiku", "Haiku (latest)", LEVELS),
           ("sonnet", "Sonnet (latest)", LEVELS), ("opus", "Opus (latest)", LEVELS)]
CACHE = store.DIR / "models.json"


def _row(id_: str, name: str, efforts) -> dict:
    return {"id": id_, "name": name, "efforts": list(efforts)}


def parse_anthropic(resp: dict) -> list[dict]:
    """A Models API page → rows {id, name, efforts}. Retired models are skipped; a model whose reply carries no
    capabilities falls back to the built-in table for its effort levels."""
    known = {i: e for i, _n, e in BUILTIN}
    rows = []
    for d in resp.get("data") or []:
        if d.get("lifecycle") == "retired" or not d.get("id"):
            continue
        eff = ((d.get("capabilities") or {}).get("effort")) or {}
        if eff:
            levels = [lv for lv in LEVELS if (eff.get(lv) or {}).get("supported")] if eff.get("supported") else []
        else:
            levels = list(known.get(d["id"], ()))
        rows.append(_row(d["id"], d.get("display_name") or d["id"], levels))
    return rows


_NOT_CHAT = ("audio", "realtime", "image", "tts", "transcribe", "search", "embedding", "moderation", "whisper", "dall")


def parse_openai(resp: dict) -> list[dict]:
    ids = sorted({d["id"] for d in resp.get("data") or []
                  if d.get("id", "").startswith(("gpt-", "o1", "o3", "o4")) and not any(w in d["id"] for w in _NOT_CHAT)})
    return [_row(i, i, ()) for i in ids]


def _get(url: str, headers: dict) -> dict:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError({401: "the API key was refused. Check it in Settings → AI.",
                            403: "this key is not allowed to list models"}.get(e.code, f"the provider answered error {e.code}"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"no internet connection ({e.reason})")


def fetch(provider: str, key: str) -> list[dict]:
    if provider == "openai":
        return parse_openai(_get("https://api.openai.com/v1/models", {"Authorization": f"Bearer {key}"}))
    rows, after = [], ""
    for _ in range(5):                                           # 1000 a page; a handful of pages is plenty
        url = "https://api.anthropic.com/v1/models?limit=1000" + (f"&after_id={after}" if after else "")
        page = _get(url, {"x-api-key": key, "anthropic-version": "2023-06-01"})
        rows += parse_anthropic(page)
        if not page.get("has_more") or not page.get("last_id"):
            break
        after = page["last_id"]
    return rows


def _cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def refresh(provider: str) -> int:
    """Asks the provider for its list with the saved API key and keeps the answer. Returns how many models."""
    import ai
    src = "openai" if provider == "openai" else "anthropic"      # the Claude login lists through an Anthropic key
    if provider == "openrouter":
        raise RuntimeError("OpenRouter has hundreds of models. Type the one you want under Custom…")
    key = ai.key_get(src)
    if not key:
        raise RuntimeError(f"no {ai.PROVIDERS[src]} saved. Add one in Settings → AI to refresh the list.")
    rows = fetch(src, key)
    if not rows:
        raise RuntimeError("the provider returned no models")
    data = _cache()
    data[src] = {"at": time.time(), "models": rows}
    CACHE.write_text(json.dumps(data))
    return len(rows)


def catalog() -> dict:
    """For the Settings page: per provider the models to offer, where the list came from, and when."""
    data = _cache()
    live = data.get("anthropic")
    api = live["models"] if live else [_row(*b) for b in BUILTIN]
    out = {"anthropic": {"models": api, "source": "live" if live else "built-in", "at": live["at"] if live else None},
           "claude": {"models": [_row(*a) for a in ALIASES] + api, "source": "live" if live else "built-in",
                      "at": live["at"] if live else None}}
    if data.get("openai"):
        out["openai"] = {"models": data["openai"]["models"], "source": "live", "at": data["openai"]["at"]}
    return out


def efforts_for(model: str) -> list[str]:
    """The effort levels a model id is known to support ([] when unknown, so a request never sends a level it might
    reject)."""
    for row in catalog()["claude"]["models"]:
        if row["id"] == model and model:
            return row["efforts"]
    return []


if __name__ == "__main__":      # the one check: .venv/bin/python mac/models.py
    sample = {"data": [
        {"id": "claude-opus-5-5", "display_name": "Claude Opus 5.5", "lifecycle": "active", "capabilities": {"effort": {
            "supported": True, "low": {"supported": True}, "medium": {"supported": True}, "high": {"supported": True},
            "max": {"supported": True}, "xhigh": {"supported": True}}}},
        {"id": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6", "lifecycle": "deprecated", "capabilities": {
            "effort": {"supported": True, "low": {"supported": True}, "medium": {"supported": True},
                       "high": {"supported": True}, "max": {"supported": True}, "xhigh": None}}},
        {"id": "claude-old", "display_name": "Old", "lifecycle": "retired"},
        {"id": "claude-haiku-4-5", "display_name": "Claude Haiku 4.5", "lifecycle": "active",
         "capabilities": {"effort": {"supported": False}}},
        {"id": "claude-fable-5-1", "display_name": "Claude Fable 5.1", "lifecycle": "active"}]}     # no capabilities
    rows = {r["id"]: r for r in parse_anthropic(sample)}
    assert "claude-old" not in rows                                                    # retired: skipped
    assert rows["claude-opus-5-5"]["efforts"] == list(LEVELS)
    assert rows["claude-sonnet-4-6"]["efforts"] == ["low", "medium", "high", "max"]    # xhigh: null = not supported
    assert rows["claude-haiku-4-5"]["efforts"] == []                                   # effort not supported at all
    assert rows["claude-fable-5-1"]["efforts"] == list(LEVELS)                         # no capabilities: built-in table
    assert [r["id"] for r in parse_openai({"data": [{"id": "gpt-5"}, {"id": "gpt-4o-realtime-preview"},
                                                    {"id": "whisper-1"}, {"id": "o3-mini"}]})] == ["gpt-5", "o3-mini"]
    assert efforts_for("claude-opus-4-6") == ["low", "medium", "high", "max"] and efforts_for("nonsense") == []
    assert efforts_for("") == [] and catalog()["claude"]["models"][0]["id"] == ""     # "account default" is first
    print("ok")
