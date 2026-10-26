#!/usr/bin/env python3
"""Regenerate ``harbor_ops/derived-state.json`` from the records.

This is how the snapshot the CLI reads was produced — and how it is
reproduced after new records land:

    python3 tools/derive.py

It reads every ``.gitpp/records/*.json`` file, folds them with
``tools/fold.py`` (this repo's own copy of the labelled minimal port
of the git.pp fold's derive semantics; see that file's header for
provenance), and writes the result — state, conflicts, orphans, and
the canonical application order — to ``harbor_ops/derived-state.json``.

Arrival order is never an input: the fold sorts records canonically
before deriving, so the output depends only on the record set.
"""

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from fold import derive  # noqa: E402


def main():
    paths = sorted(glob.glob(str(ROOT / ".gitpp" / "records" / "*.json")))
    records = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            records.append(json.load(fh))
    result = derive(records)
    out_path = ROOT / "harbor_ops" / "derived-state.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"folded {len(records)} records -> {out_path.relative_to(ROOT)}")
    for key in sorted(result["state"]):
        print(f"  {key} = {result['state'][key]}")
    print(f"conflicts: {len(result['conflicts'])}, "
          f"orphans: {len(result['orphans'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
