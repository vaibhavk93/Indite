"""The Claude CLI's JSON reply carries its own usage and cost; inditeflow shows them instead of "no cost reported"."""
from inditeflow import notes


def test_last_usage_reads_the_cli_reply():
    notes._last.out = {"modelUsage": {"claude-haiku-5-5": {}}, "total_cost_usd": 0.0001326,
                       "usage": {"input_tokens": 2, "cache_creation_input_tokens": 652,
                                 "cache_read_input_tokens": 0, "output_tokens": 4}}
    assert notes.last_usage() == {"model": "claude-haiku-5-5", "in_tok": 654, "out_tok": 4,
                                  "cost_usd": 0.0001326, "cost_basis": "list"}


def test_no_reply_means_honest_nones():
    notes._last.out = None
    assert notes.last_usage()["cost_usd"] is None and notes.last_usage()["model"] is None


def test_a_typed_model_name_can_never_become_a_flag():
    import pytest
    for bad in ("--tools", "-x", "haiku --tools bash", "a b", ""[:0] + "$(x)"):
        with pytest.raises(SystemExit):
            notes._claude("x", ".", model=bad)


def test_a_bad_effort_level_is_refused_before_anything_runs():
    import pytest
    for bad in ("--tools", "ultra", "High"):
        with pytest.raises(SystemExit):
            notes._claude("x", ".", effort=bad)
