# gitpp-dogfood-day1

The M2 live-day test for [gitpp-app](https://github.com/patchwork-quilt/gitpp-app):
five agents write conflicting git.pp records on separate branches against
this shared state (project harbor-ops); a referee merges their pull
requests in a deliberately unkind order; after every merge, the state the
git.pp Check predicted for the branch must equal the state derived from
the merged tree. Results are written up in this repo when the run ends.
delivery control 2026-10-23T00:22:06Z
