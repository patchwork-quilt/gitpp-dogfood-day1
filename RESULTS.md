# RESULTS — M2 live-day test, harbor-ops

*Run 2026-10-23 (UTC), referee-run. Five agents wrote conflicting git.pp
records on separate branches of this repo; the referee merged their PRs in
a deliberately unkind order; after every merge, the state in the git.pp
Check on the merged main head was compared — aspect by aspect — against an
independent local derivation of the same tree (the gitpp-action renderer,
`fold.mjs`, over the merged `.gitpp/records`).*

**Verdict: PASS. 5/5 branch Checks and 5/5 merge Checks matched the
independent derivation on state, conflicts, and orphans.**

## Setup

Base state on `main` (seed `e72a162`, README fix `273dc76`): project
`harbor-ops`, 5 records — `genesis` (witness), `task-freeze-a`
(release.freeze = billing-v2 2026-10-19..2026-10-23), `task-oncall-a`
(oncall.primary = priya), `task-flag-a` (feature.new_checkout = off),
`witness-1` (deploy.last_seen = green). Delivery control before the run:
push `10b6333` → Check `120167229259`, "5 records · 6 keys · 0
conflict(s) · 0 orphan(s)".

## The five claims

| Agent | Branch | PR | Records added | Claim |
|---|---|---|---|---|
| CAPTAIN | agent/captain | #3 | override-freeze (override, parents [task-freeze-a]) | release.freeze = none — "freeze lifted, ship it" |
| LATECOMER | agent/late | #1 | override-oncall (override, parents [genesis]) | oncall.primary = jonas |
| FREEZE-EXTENDER | agent/freeze | #4 | task-freeze-b (task, parents [task-freeze-a]) | release.freeze = billing-v2 2026-10-19..2026-10-27 |
| FLAG-FLIPPER | agent/flag | #2 | task-flag-b (task) + witness-flag (witness) | feature.new_checkout = canary |
| ONCALL-SWAP | agent/oncall | #5 | task-oncall-b (task, parents [task-oncall-a]) | oncall.primary = mara |

Branch heads and their Checks (each verified MATCH against a local fold
of the branch tree — state, conflicts, orphans):

| Branch | Head | Check | Counts |
|---|---|---|---|
| agent/captain | 3baee3b | 120167878842 | 6 records · 1 conflict |
| agent/late | 5369296 | 120167858319 | 6 records · 1 conflict |
| agent/freeze | a255b71 | 120167970357 | 6 records · 1 conflict |
| agent/flag | d8e84e3 | 120167861695 | 7 records · 1 conflict |
| agent/oncall | 1e42c36 | 120167972654 | 6 records · 1 conflict |

## Merge order — unkind on purpose

Arrival order was late, flag, captain, freeze, oncall (PR #1–#5 in
creation order #1 late, #2 flag, #3 captain, #4 freeze, #5 oncall). The
referee merged instead: **(1) captain, (2) late, (3) freeze, (4) flag,
(5) oncall** — both overrides landed *before* the task claims they would
eventually outrank, and the two task claims whose branch-local Checks had
declared them winners (freeze extension, mara) merged *into* trees where
an override already stood. Arrival order is never an input to the fold;
this order was chosen to prove the merged result doesn't care.

## Per-merge comparison (Check on merged main vs independent local fold)

| # | PR merged | New main | Check | Counts (records · keys · conflicts · orphans) | State | Conflicts | Orphans |
|---|---|---|---|---|---|---|---|
| 1 | #3 captain | db62fc3 | 120168546255 | 6 · 6 · 1 · 0 | MATCH | MATCH | MATCH |
| 2 | #1 late | 1712073 | 120168762924 | 7 · 6 · 2 · 0 | MATCH | MATCH | MATCH |
| 3 | #4 freeze | dae5e63 | 120169002367 | 8 · 6 · 2 · 0 | MATCH | MATCH | MATCH |
| 4 | #2 flag | 6e0ae8b | 120169246517 | 10 · 6 · 3 · 0 | MATCH | MATCH | MATCH |
| 5 | #5 oncall | ab34243 | 120169485033 | 11 · 6 · 3 · 0 | MATCH | MATCH | MATCH |

## Final state (11 records)

- `deploy.last_seen` = green
- `feature.new_checkout` = canary
- `oncall.primary` = jonas
- `project` = harbor-ops
- `release.freeze` = none
- `status` = open

## Final conflicts (losers preserved)

- **feature.new_checkout** = canary — winner `task-flag-b`; losers
  `task-flag-a` (off, superseded) and `witness-flag` (canary, outranked —
  task beats witness).
- **oncall.primary** = jonas — winner `override-oncall`; losers
  `task-oncall-a` (priya, outranked) and `task-oncall-b` (mara,
  outranked).
- **release.freeze** = none — winner `override-freeze`; losers
  `task-freeze-a` (billing-v2 2026-10-19..2026-10-23, outranked) and
  `task-freeze-b` (billing-v2 2026-10-19..2026-10-27, outranked).

The narrative the test was built to produce: freeze-b's extension and
oncall-b's mara both *won their own branches* — their branch Checks were
correct for those trees — and both lost in the merged tree, because in
the merged tree an override of their key already stood. The per-tree
Checks never disagreed with the fold of their tree; that's the property
under test, and it held 10 times out of 10.

## API-call accounting

Counts are labelled: **[observed]** = read from the check-runs API, the
app's `/events` ring, or this run's action log; **[derived]** = computed
from the implementation's known call shape.

- Pushes caused by the run: 11 (5 branch + 5 merges + this write-up) —
  [observed, action log].
- Checks posted ("git.pp state", all conclusion neutral): 11 — 5 branch
  + 5 merge + 1 for this write-up commit — [observed, check-runs API;
  ids in the tables above + the write-up id recorded below].
- Deliveries: each push generates a push delivery and check_suite
  deliveries; the losing twin derivation is stopped at the app's
  per-commit claim and records `skipped-duplicate` — [observed in the
  ring throughout the run]. The ring retains only its last 20 entries,
  so a full-run delivery total is reconstructed, not read: ≥ 22 push /
  check_suite deliveries + ≥ 11 derive outcomes — [derived].
- App REST calls per posted Check: 4 (installation-token mint, repo
  tarball, check-exists GET, check POST) — [derived from the
  implementation]. Run total ≈ 44 app REST calls — [derived]. The
  referee's own read calls (check-runs API) are not the app's and are
  not counted.
- Write-up commit's own Check: 120170080462 (neutral) on commit
  2a9c1d7, the commit that added this file. (Its derived state is the final state above; the
  write-up changes no records.)

## Surprises

- Two of five agents had their **first push remote-rejected** with no
  reason in the output; an immediate retry succeeded as a new branch.
  Transient, unexplained by anything in the run; no data lost.
- `witness-flag` appears as a *loser* on its own branch even though it
  set the same value as the winner (`canary`): it set the key, it is a
  witness, and kind priority ranks it below the task that also set it
  (`task-flag-b`, which it descends from). The conflict itself is real
  (task-flag-a set `off`); witness-flag's loss is bookkeeping about
  whose claim stands, not about the value. Mechanically correct, and
  exactly the kind of line a first-time reader trips on — noted for
  the legibility file.
- No merge produced a git conflict: five branches, eleven record files,
  zero overlapping paths. The record-per-file layout keeps concurrent
  record work merge-trivial; the fold, not git, is where the claims
  collide.

---

## Day 2 — 2026-10-26: the project build, and two winter records

*The day-1 log above is untouched; this addendum is appended in the
same referee style — claims from the PRs, Checks read from the API,
agreement judged against an independent local fold (this repo's
`tools/fold.py`) of the merged record set.*

**The project build (commit `5309507`, harbor-ops 0.1.0).** Between
day 1 and the records below, the repo grew the project its records
describe — the CLI, a 12-test suite, CI, and a derived-state snapshot
generated from the 11 day-1 records — without changing any day-1
record or a byte of the log above. The snapshot's fold equals the
day-1 final state recorded above, and the tests workflow passed on
the push (run `40394594457`, success).

**The two records, in merge order:**

| # | PR | Record added | Claim | Merge commit | Check | Conclusion |
|---|---|---|---|---|---|---|
| 1 | #6 | task-season-winter (task, parents [genesis]) | schedule.season = winter | c524c08 | 121824647658 | neutral |
| 2 | #7 | override-oncall-winter (override, parents [override-oncall]) | oncall.primary = sanna | 779c836 | 121825082829 | neutral |

Parenting, as argued in the PRs: the timetable record is the first
setter of `schedule.season`, so it parents `genesis` — the day-1
first-setter pattern. The on-call override parents the record it
replaces, `override-oncall`, so the handover is decided by ancestry
dominance inside the override class; a sibling override would have
fallen through to the smallest-id tie-break, the wrong mechanism for
an intentional handover.

**Per-merge comparison (Check on merged main vs independent local fold):**

| # | Counts (records · keys · conflicts · orphans) | State | Winners |
|---|---|---|---|---|
| 1 | 12 · 7 · 3 · 0 | MATCH | MATCH |
| 2 | 13 · 7 · 3 · 0 | MATCH | MATCH |

## Final state (13 records)

- `deploy.last_seen` = green
- `feature.new_checkout` = canary
- `oncall.primary` = sanna
- `project` = harbor-ops
- `release.freeze` = none
- `schedule.season` = winter
- `status` = open

The `oncall.primary` conflict now preserves three losers:
`override-oncall` (jonas — the day-1 winner, superseded by its own
descendant), `task-oncall-a` (priya), and `task-oncall-b` (mara).

**Closing the loop.** This addendum ships with the regenerated
snapshot (`tools/derive.py` over the 13 records, harbor-ops 0.2.0),
so the program now reports what the records decided: `harbor-ops
board` shows the winter timetable and `harbor-ops oncall` shows
sanna. The snapshot-vs-fold consistency test in the suite guards the
regeneration step from here on.
