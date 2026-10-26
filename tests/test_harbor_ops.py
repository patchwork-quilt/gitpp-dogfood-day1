"""Tests for the harbor-ops CLI.

Two kinds of assertions live here, on purpose:

* Behaviour tests drive the CLI against synthetic derived states, so
  they pin what the commands *do* regardless of what the records
  currently say.
* One consistency test pins the shipped snapshot to the records: the
  state in ``harbor_ops/derived-state.json`` must equal a fresh fold
  of ``.gitpp/records/``. If records land without regenerating the
  snapshot, this test fails — that is the point of it.
"""

import glob
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harbor_ops import cli, state as state_mod  # noqa: E402


def load_fold():
    spec = importlib.util.spec_from_file_location(
        "repo_fold", ROOT / "tools" / "fold.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(argv, derived, demo_file=None):
    """Invoke cli.main's dispatch with an injected derived state."""
    args = cli.build_parser().parse_args(argv)
    if demo_file is not None:
        args.demo_file = demo_file
    out = io.StringIO()
    with redirect_stdout(out):
        code = cli.COMMANDS[args.command](args, derived)
    return code, out.getvalue()


SYNTHETIC = {
    "state": {
        "project": "harbor-ops",
        "status": "open",
        "release.freeze": "none",
        "oncall.primary": "jonas",
        "feature.new_checkout": "canary",
    },
    "conflicts": [
        {"key": "release.freeze", "winner": "override-freeze",
         "losers": ["task-freeze-a", "task-freeze-b"]},
        {"key": "oncall.primary", "winner": "override-oncall",
         "losers": ["task-oncall-a", "task-oncall-b"]},
        {"key": "feature.new_checkout", "winner": "task-flag-b",
         "losers": ["task-flag-a", "witness-flag"]},
    ],
    "orphans": [],
    "order": ["genesis"],
}


class DerivedStateTests(unittest.TestCase):
    def test_shipped_snapshot_matches_fresh_fold(self):
        fold = load_fold()
        records = []
        for path in sorted(glob.glob(
                str(ROOT / ".gitpp" / "records" / "*.json"))):
            with open(path, encoding="utf-8") as fh:
                records.append(json.load(fh))
        fresh = fold.derive(records)
        shipped = state_mod.load_derived()
        self.assertEqual(shipped["state"], fresh["state"])
        self.assertEqual(shipped["conflicts"], fresh["conflicts"])
        self.assertEqual(shipped["orphans"], fresh["orphans"])

    def test_snapshot_has_the_coordination_keys(self):
        shipped = state_mod.load_derived()
        for key in ("release.freeze", "oncall.primary",
                    "feature.new_checkout", "project"):
            self.assertIn(key, shipped["state"])


class CommandTests(unittest.TestCase):
    def test_freeze_none(self):
        code, out = run_cli(["freeze"], SYNTHETIC)
        self.assertEqual(code, 0)
        self.assertIn("no release freeze in force", out)
        self.assertIn("override-freeze", out)

    def test_freeze_window(self):
        derived = json.loads(json.dumps(SYNTHETIC))
        derived["state"]["release.freeze"] = "billing-v2 2026-10-19..2026-10-23"
        code, out = run_cli(["freeze"], derived)
        self.assertEqual(code, 0)
        self.assertIn("releases are frozen", out)
        self.assertIn("2026-10-19..2026-10-23", out)

    def test_oncall_shows_primary_winner_and_losers(self):
        code, out = run_cli(["oncall"], SYNTHETIC)
        self.assertEqual(code, 0)
        self.assertIn("oncall.primary: jonas", out)
        self.assertIn("override-oncall", out)
        self.assertIn("task-oncall-b", out)

    def test_board_defaults_to_summer_without_season_key(self):
        code, out = run_cli(["board"], SYNTHETIC)
        self.assertEqual(code, 0)
        self.assertIn("summer timetable", out)
        self.assertIn("MV Kestrel", out)

    def test_board_uses_winter_when_record_says_so(self):
        derived = json.loads(json.dumps(SYNTHETIC))
        derived["state"]["schedule.season"] = "winter"
        code, out = run_cli(["board"], derived)
        self.assertEqual(code, 0)
        self.assertIn("winter timetable", out)
        summer_code, summer_out = run_cli(["board"], SYNTHETIC)
        self.assertNotEqual(out, summer_out)

    def test_status_lists_every_key(self):
        code, out = run_cli(["status"], SYNTHETIC)
        self.assertEqual(code, 0)
        for key in SYNTHETIC["state"]:
            self.assertIn(key, out)


class CanaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.demo_path = str(Path(self.tmp.name) / "demo.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_canary_shows_derived_value_by_default(self):
        code, out = run_cli(["canary"], SYNTHETIC,
                            demo_file=self.demo_path)
        self.assertEqual(code, 0)
        self.assertIn("feature.new_checkout: canary (from derived state)",
                      out)

    def test_canary_toggle_writes_demo_file_and_flips(self):
        code, out = run_cli(["canary", "toggle"], SYNTHETIC,
                            demo_file=self.demo_path)
        self.assertEqual(code, 0)
        self.assertIn("canary -> off", out)
        demo = state_mod.load_demo(self.demo_path)
        self.assertEqual(demo["feature.new_checkout"], "off")
        # Derived state is not touched by the toggle.
        self.assertEqual(SYNTHETIC["state"]["feature.new_checkout"],
                         "canary")

    def test_canary_toggle_twice_restores(self):
        run_cli(["canary", "toggle"], SYNTHETIC, demo_file=self.demo_path)
        code, out = run_cli(["canary", "toggle"], SYNTHETIC,
                            demo_file=self.demo_path)
        self.assertEqual(code, 0)
        self.assertIn("off -> canary", out)

    def test_canary_reset_clears_override(self):
        run_cli(["canary", "toggle"], SYNTHETIC, demo_file=self.demo_path)
        code, out = run_cli(["canary", "reset"], SYNTHETIC,
                            demo_file=self.demo_path)
        self.assertEqual(code, 0)
        self.assertIn("effective value is canary (derived state)", out)
        code, out = run_cli(["canary"], SYNTHETIC,
                            demo_file=self.demo_path)
        self.assertIn("(from derived state)", out)


if __name__ == "__main__":
    unittest.main()
