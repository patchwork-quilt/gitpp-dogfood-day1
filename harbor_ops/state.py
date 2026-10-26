"""State loading for harbor-ops.

Two layers, kept separate on purpose:

* **Derived state** — the fold of the git.pp records in
  ``.gitpp/records/``, snapshotted into ``derived-state.json`` next to
  this module by ``tools/derive.py``. This is the shared, multi-writer
  truth: release freeze, on-call primary, feature flags, season. The
  CLI never edits it by hand; it changes when records land and the
  snapshot is regenerated.

* **Demo state** — a small local JSON file (default
  ``./harbor-ops-demo.json``, override with ``--demo-file`` or the
  ``HARBOR_OPS_DEMO_FILE`` environment variable) holding one person's
  local experiments. It can shadow exactly one thing: the effective
  ``feature.new_checkout`` value shown by the ``canary`` command, so
  the canary can be flipped on a laptop without touching the shared
  record. It is gitignored and never part of the derived state.
"""

import json
import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
DERIVED_STATE_PATH = PACKAGE_DIR / "derived-state.json"
TIMETABLE_PATH = PACKAGE_DIR / "data" / "timetable.json"

DEFAULT_DEMO_FILE = "harbor-ops-demo.json"
CANARY_KEY = "feature.new_checkout"
CANARY_VALUES = ("off", "canary", "full")


def load_derived(path=None):
    """Load the derived-state snapshot (state + conflicts + orphans)."""
    with open(path or DERIVED_STATE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def load_timetable(path=None):
    """Load the sailing timetable, keyed by season name."""
    with open(path or TIMETABLE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def winner_for(derived, key):
    """The record that decided ``key``, if the key was contested."""
    for conflict in derived.get("conflicts", []):
        if conflict["key"] == key:
            return conflict["winner"]
    return None


def losers_for(derived, key):
    """The records whose claims on ``key`` lost, in fold order."""
    for conflict in derived.get("conflicts", []):
        if conflict["key"] == key:
            return list(conflict["losers"])
    return []


def demo_file_path(explicit=None):
    if explicit:
        return Path(explicit)
    env = os.environ.get("HARBOR_OPS_DEMO_FILE")
    if env:
        return Path(env)
    return Path.cwd() / DEFAULT_DEMO_FILE


def load_demo(path):
    """Read the demo state file; a missing file means no overrides."""
    if not Path(path).exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_demo(path, demo):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(demo, fh, indent=2, sort_keys=True)
        fh.write("\n")


def effective_canary(derived, demo):
    """The canary value in force locally: demo override, else derived."""
    if CANARY_KEY in demo:
        return demo[CANARY_KEY], "demo file"
    return derived["state"][CANARY_KEY], "derived state"
