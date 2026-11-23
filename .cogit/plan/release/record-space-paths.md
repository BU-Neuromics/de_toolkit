---
kind: task
objective: A recorded command line writes an absolute path that exists relative to workdir, whitespace or not, as DETK-0590 Option A says; an argument that names no existing file keeps DETK-0580's rule, so a script or pattern that starts with / is still recorded as typed
acceptance:
  - _is_path in de_toolkit/report.py (used by relative_arg) takes an argument for a path when os.path.lexists says it exists, whitespace or not, and otherwise only as DETK-0580 says (starts with /, no whitespace, parent directory exists); run in a working directory with a 'My Data' folder, detk-util record -i "$PWD/My Data/c.csv" -o g.csv -- cp "$PWD/My Data/c.csv" g.csv records argv with 'My Data/c.csv', not the absolute path; a test in tests/report/test_report_paths.py
  - 'every DETK-0580 case still stays as typed: awk ''/^gene/ {print}'', ''/^g1,/'', and sh -c "/usr/bin/env echo hi"; an output not yet written in an existing directory is still relative; the --opt=/abs and -o/abs forms follow the same rule; every existing test in tests/report/test_report_paths.py and tests/docs/test_report_paths_doc.py passes'
  - docs/report.md's 'An argument that is not a path' bullet states the rule (an existing path, whitespace or not, or else DETK-0580's) and the CHANGELOG's DETK-0580 entry gets the sentence
from: [DETK-0590]
scope: [+de_toolkit/report.py, +tests/report/test_report_paths.py, +tests/docs/test_report_paths_doc.py, +docs/report.md, +CHANGELOG]
issue: 166
visited: 21b692c
---

# detk-util record writes an existing path with spaces relative

## Implementation plan

- [x] @developer As DETK-0590 is answered (Option A): `_is_path` takes an existing path for a path, whitespace or not, and otherwise keeps DETK-0580's rule; the `My Data` test and the DETK-0580 cases kept; docs/report.md's rule; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: in a working directory with a `My Data` folder run `detk-util record -i "$PWD/My Data/c.csv" -o g.csv -- cp "$PWD/My Data/c.csv" g.csv` and the awk, regex and `sh -c` cases of DETK-0580, read argv in the module JSON and the crate, and re-run the recorded lines from the working directory <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-23 from DETK-0590 (the s2 re-review of release/cli-docs,
#163), accepted with Option A under Adam's delegation (DETK-0063).
DETK-0580 (in #163) made `_is_path` require no whitespace, so a real
absolute path with a space (`My Data/c.csv`) is recorded absolute, against
DETK-0281. `relative_arg` runs after the command ran, so an existence check
is exact for files read and written; DETK-0580's rule stays for a path that
does not exist. `-i`/`-o` lists go through `_file_relpath` and are
unaffected. The one cost: a script that is exactly the name of an existing
file is taken for a path, as before DETK-0580.

Scope is `+` only: no other open node touches report.py or these tests.
Ready now; before release/cut.
