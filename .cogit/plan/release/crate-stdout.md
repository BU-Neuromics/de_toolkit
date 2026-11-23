---
kind: task
objective: A command that writes its result to standard output records no File entity for it in the Process Run Crate (today the out_file_path marker 'stdout' becomes a File with @id ../stdout)
acceptance:
  - 'crate.py treats the out_file_path (and out_file_paths entry) ''stdout'' as the standard-output marker it is: the CreateAction lists no File for it, and the crate holds no @id ending in stdout; a file the user actually named stdout (-o stdout is the marker, so -o ./stdout) is still listed as a File; tests in tests/report/test_crate.py for detk-norm cpm to stdout (no stdout entity, the input still listed) and to -o out.csv (out.csv listed)'
  - the crate still validates under the process-run-crate profile at REQUIRED level (test_crate_validates_against_profile passes, and a case with output to stdout is validated too); module JSON's out_file_path stays 'stdout' as module_schema.json documents it; CHANGELOG under Fixed
scope: [+de_toolkit/crate.py, +de_toolkit/report.py, +tests/report/test_crate.py, +CHANGELOG]
issue: 147
visited: 501927d
status: done
done: c74a781
---

# The crate does not list stdout as a file

## Implementation plan

- [x] @developer Leave the stdout marker out of the crate's files, keep a file really named stdout, tests including profile validation; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: run a detk command to stdout and one to a file, read both crates, and check them with rocrate-validator <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-22 from the release/report-paths review (#134, not
blocking). Reproduced on main at d201819: `detk-norm cpm c.csv > n.csv`
writes module JSON with `out_file_path: "stdout"` (the documented marker),
and the crate turns it into a File `../stdout`, a file that does not exist.
The fix belongs where crate.py collects out_file_path(s) (`_paths`, about
line 291) into File entities.

The published example's crate (docs/example/ro-crate-metadata.json) holds
no stdout entry, so this does not touch release/example-paths. No
unfinished node holds `crate.py` or `tests/report/test_crate.py`: ready
now. Before release/cli-docs (whose docs/report.md crate section may name
the rule) and release/cut.

Scope extended 2026-11-23 by `+de_toolkit/report.py` (`_file_relpath`
records a file named stdout as `./stdout`), following DETK-0420 option 1,
accepted under Adam's delegation via the driver session, 2026-11-20
(DETK-0063).
