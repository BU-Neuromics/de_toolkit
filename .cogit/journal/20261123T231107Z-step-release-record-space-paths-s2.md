---
kind: step
time: 2026-11-23T23:11:07Z
by: DETK/reviewer
node: release/record-space-paths
step: s2
branch: review/record-space-paths
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: in a working directory with a `My Data` folder run `detk-util record -i "$PWD/My Data/c.csv" -o g.csv -- cp "$PWD/My Data/c.csv" g.csv` and the awk, regex and `sh -c` cases of DETK-0580, read argv in the module JSON and the crate, and re-run the recorded lines from the working directory

## Summary

Approved: an existing absolute path with a space is recorded relative ('My Data/c.csv' in argv, command, inputs and crate) and re-runs from workdir; the DETK-0580 awk, sed/regex and sh -c cases stay as typed, an unwritten output is still relative; docs and CHANGELOG state the rule; CI green including the R job

## Artifacts

## Findings

Checks: CI green on b3b072b, every job, including test with R (bioconda) (28m22s), docs build (strict), ruff, runtime dependencies only, combined coverage and CodeQL. Locally (uv, Python 3.13, no R): full suite 2623 passed, 154 skipped; ruff clean; tests/report/test_report_paths.py and tests/docs/test_report_paths_doc.py 37 passed.

detk-util record, run in a working directory with a `My Data` folder, argv read from the module JSON and the crate's argv/command/inputs/outputs parameters:
- `-i "$PWD/My Data/c.csv" -o g.csv -- cp "$PWD/My Data/c.csv" g.csv`: argv `['cp', 'My Data/c.csv', 'g.csv']`, command `cp 'My Data/c.csv' g.csv`, inputs `['My Data/c.csv']`; the crate's file entity is `../My Data/c.csv`.
- `awk '/^gene/ {print}' "$PWD/counts.csv"`: `['awk', '/^gene/ {print}', 'counts.csv']`, the program as typed.
- `sed -n '/^g1,/p' "$PWD/counts.csv"`: `['sed', '-n', '/^g1,/p', 'counts.csv']`.
- `sh -c "/usr/bin/env echo hi"`: `['sh', '-c', '/usr/bin/env echo hi']`.
- an output not yet written: `cp "$PWD/counts.csv" "$PWD/newout.csv"` records `cp counts.csv newout.csv`; `"$PWD/My Data/new2.csv"`, not yet written and with a space, is recorded `'My Data/new2.csv'` too, because relative_arg runs after the command wrote it.
- `sh -c 'cp "$1" out3.csv' x "$PWD/counts.csv"`: the positional path is made relative and the script kept.
No absolute scratch path anywhere in the crate. All seven recorded command lines, re-run from the working directory with the outputs removed, exit 0 and write the same files.

The change: _is_path returns True for an absolute path that os.path.lexists finds, and otherwise applies DETK-0580's rule unchanged. relative_arg's --opt= and -X forms go through the same function, and the new relative_arg cases cover them. The new end-to-end test reruns the recorded command. docs/report.md's bullet and the CHANGELOG's DETK-0580 entry state the rule. lexists returns False on a name that is too long (I checked a 15 kB script), so a long script can't raise.

The tradeoff (an argument that is exactly an existing path is taken for a path): this widens DETK-0580 only for an argument with whitespace that is exactly the path of an existing file. An argument without whitespace naming an existing file already counted as a path under DETK-0580 (its parent exists). A script or pattern that is, character for character, an existing absolute path with a space in it is rare enough to accept. When it does happen, the recorded relative form names the same file from workdir, so the re-run still works on the same tree. Acceptable as DETK-0590 says. No decision needed.

Non-blocking: relative_arg's docstring line "one that merely starts with ``/`` is kept. The command line then re-runs the same" is now 89 characters (ruff passes, so the line limit isn't enforced on docstrings). Cosmetic only.

## Questions
