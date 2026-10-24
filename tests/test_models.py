"""Model and effort lists: parsing the Anthropic Models API reply, the built-in table, the effort filter."""
import runpy
from pathlib import Path

MODELS = Path(__file__).resolve().parents[1] / "mac" / "models.py"


def test_models_self_check_passes():
    runpy.run_path(str(MODELS), run_name="__main__")      # its own asserts: capabilities, retired, xhigh null, OpenAI filter
