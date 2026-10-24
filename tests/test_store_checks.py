"""mac/store.py and mac/models.py carry their own asserts (history cap, cache, append-only saving, delete choices,
Dictionary rules); this runs them with the rest of the tests."""
import runpy
from pathlib import Path

MAC = Path(__file__).resolve().parents[1] / "mac"


def test_store_self_check():
    runpy.run_path(str(MAC / "store.py"), run_name="__main__")
