---
kind: task
objective: A recorded command line writes an absolute path that exists relative to workdir, whitespace or not, as DETK-0590 Option A says; an argument that names no existing file keeps DETK-0580's rule, so a script or pattern that starts with / is still recorded as typed
acceptance:
  - _is_path in de_toolkit/report.py (used by relative_arg) takes an argument for a path when os.path.lexists says it exists, whitespace or not, and otherwise only as DETK-0580 says (starts with /, no whitespace, parent directory exists); run in a working directory with a 'My Data' folder, detk-util record -i "$PWD/My Data/c.csv" -o g.csv -- cp "$PWD/My Data/c.csv" g.csv records argv with 'My Data/c.csv', not the absolute path; a test in tests/report/test_report_paths.py
  - 'every DETK-0580 case still stays as typed: awk ''/^gene/ {print}'', ''/^g1,/'', and sh -c "/usr/bin/env echo hi"; an output not yet written in an existing directory is still relative; the --opt=/abs and -o/abs forms follow the same rule; every existing test in tests/report/test_report_paths.py and tests/docs/test_report_paths_doc.py passes'
  - docs/report.md's 'An argument that is not a path' bullet states the rule (an existing path, whitespace or not, or else DETK-0580's) and the CHANGELOG's DETK-0580 entry gets the sentence
from: [DETK-0590]
scope: [+de_toolkit/report.py, +tests/report/test_report_paths.py, +tests/docs/test_report_paths_doc.py, +docs/report.md, +CHANGELOG]
---

# detk-util record writes an existing path with spaces relative

## Implementation plan

- [ ] @developer Pass the sheet's name to _sniff in read_column_data; a FIFO test through detk-util tidy; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: run detk-util tidy -p with the ragged sheet through <(cat sheet.csv) and as a file, and read both messages <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Implementation plan copied from `release/tidy-sheet-name` by `cogit node new`.
