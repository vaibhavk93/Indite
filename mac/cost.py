"""
Per-answer cost estimates for the AI providers indite talks to.

Rates are in US dollars per million tokens, (input, output). They go stale as providers change prices; the only
authority is the provider's own dashboard. indite shows the number only when it is confident; a model not in RATES
reports as "cost not estimated" rather than "$0.00", which is honest.

Local Claude (`provider == "claude"`, the signed-in-on-this-Mac path through the `claude` CLI) returns no usage
counts to the app — those calls are marked "no cost reported" and never attributed a number.

Rates listed below are the providers' published numbers as of October 2026. Update when a provider changes a price
or indite starts using a new model.
"""

from __future__ import annotations

# model id → (USD per million INPUT tokens, USD per million OUTPUT tokens)
# Keys match the strings used in DEFAULT_MODEL + whatever the founder types in Settings → AI → Model.
RATES: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-haiku-5-5":       (1.00,  5.00),
    "claude-haiku-4-5":       (1.00,  5.00),
    "claude-sonnet-5":        (3.00, 15.00),
    "claude-opus-5":          (15.0, 75.00),
    "claude-opus-4-7":        (15.0, 75.00),
    "claude-fable-5":         (1.00,  5.00),            # ← guess; verify when exact rate ships
    # OpenAI
    "gpt-4.1-mini":           (0.40,  1.60),
    "gpt-4o-mini":            (0.15,  0.60),
    "gpt-5":                  (2.50, 10.00),
    # OpenRouter varies by sub-model; "openrouter/auto" picks for the user, so cost is unknown without the response
    # itself naming the model (returned in OpenRouter's response.model). Handled in extract_from_response below.
}


def estimate(model: str, in_tokens: int | None, out_tokens: int | None) -> float | None:
    """Dollar cost for one call, or None if we can't say honestly."""
    if not model or in_tokens is None or out_tokens is None:
        return None
    rate = RATES.get(model)
    if rate is None:
        # OpenRouter prefixes like "anthropic/claude-haiku-5-5" → try the trailing slug
        tail = model.split("/", 1)[1] if "/" in model else model
        rate = RATES.get(tail)
    if rate is None:
        return None
    in_rate, out_rate = rate
    return round(in_tokens * in_rate / 1_000_000 + out_tokens * out_rate / 1_000_000, 5)


def extract(provider: str, response: dict) -> tuple[str | None, int | None, int | None]:
    """
    Pull (model_used, input_tokens, output_tokens) from a provider's JSON response.
    Returns Nones if the response doesn't carry them (OpenRouter sometimes omits).
    """
    if provider == "anthropic":
        usage = response.get("usage") or {}
        return response.get("model"), usage.get("input_tokens"), usage.get("output_tokens")
    # OpenAI, OpenRouter — both follow the OpenAI shape
    usage = response.get("usage") or {}
    return response.get("model"), usage.get("prompt_tokens"), usage.get("completion_tokens")


if __name__ == "__main__":
    # Self-check: tiny, no network. Verifies the two paths users care about and the honest-None path.
    assert estimate("claude-haiku-5-5", 1000, 200) == round(0.001 + 0.001, 5)         # 1k in @ $1, 200 out @ $5 = $0.001 + $0.001 = $0.002
    assert estimate("gpt-4.1-mini", 10_000, 1_000) == round(0.004 + 0.0016, 5)        # $0.004 + $0.0016 = $0.0056
    assert estimate("anthropic/claude-haiku-5-5", 1000, 200) == 0.002                 # provider-prefixed slug resolves
    assert estimate("some-model-nobody-ever-added", 1000, 200) is None                # honest
    assert estimate("claude-haiku-5-5", None, 200) is None
    # Anthropic response shape
    anth = {"model": "claude-haiku-5-5", "usage": {"input_tokens": 1234, "output_tokens": 567}}
    assert extract("anthropic", anth) == ("claude-haiku-5-5", 1234, 567)
    # OpenAI / OpenRouter shape
    openai_r = {"model": "gpt-4.1-mini", "usage": {"prompt_tokens": 500, "completion_tokens": 100}}
    assert extract("openai", openai_r) == ("gpt-4.1-mini", 500, 100)
    assert extract("openrouter", openai_r) == ("gpt-4.1-mini", 500, 100)
    # No usage block — honest Nones, no exception
    assert extract("anthropic", {"model": "x"}) == ("x", None, None)
    assert extract("openai", {}) == (None, None, None)
    print("ok")
