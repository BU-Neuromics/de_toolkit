---
kind: task
objective: 'The docs show the finished 1.0 CLI as it is, state what it promises, and are kept in step by a test (DETK-0001, DETK-0025)'
acceptance:
  - 'every usage block in docs/tools/*.md and docs/report.md matches the installed --help, and a test in CI checks it as DETK-0010''s test does for the skill'
  - 'docs/index.md and docs/api.md (where the #37 statement says the CLI is the promise) state what 1.0 promises about help, per DETK-0025 Option B: the structure, the listed facts and the examples, not the wording'
  - 'the exit codes are documented as 0 success, 2 usage error, 1 anything else (DETK-0031), on docs/concepts.md; how to enable bash, zsh and tcsh completion from the shipped scripts is documented (DETK-0032); detk-filter''s usage shows no --column-data (DETK-0030)'
  - 'no page describes command lines as built from docopt docstrings; docs/dev/ says how to add a command or option with argparse, including its help example'
  - 'the README, quickstart and example commands run as written on the migrated CLI'
  - 'docs/agent-skills.md lists every file under skills/detk/references/ (today it leaves out covariates.md, the Miller recipes reference of release/miller-recipes), and a test in tests/docs/ fails when a file there is not listed'
  - 'docs/report.md''s paragraph on recorded paths ("No recorded path is absolute") says the exception: a path inside a quoted argument, such as the script of detk-util record -- sh -c "cp /abs/a /abs/b", is one argument and is written as typed, absolute paths and all, so write such steps with relative paths; and, as DETK-0390 is answered, says what a report directory or program outside the working directory''s tree records (the workdir ../ chain, with the existing advice to keep the report directory and data under the working directory, and under Option B record''s program by name, with its exception: where /bin and /usr/bin are separate directories, a program typed as /bin/cp is still recorded as a relative path when PATH finds /usr/bin/cp first); the crate section says standard output is not listed as a file (release/crate-stdout); a test in tests/docs/ runs the sh -c example through detk-util record and asserts the paths appear as the page says'
  - 'docs/concepts.md, where it says detk sniffs the delimiter, says that a one-field header over rows that split unalike is an error (release/ragged-sheet)'
  - 'crate.py''s module docstring says which File entities carry sha256 and contentSize: only the files detk-util record checksummed (DETK-0061), not every input and output of a recorded step nor any file of a detk command; a test in tests/report/test_crate.py builds a crate from a detk command and a recorded step and asserts that exactly the files the envelope checksummed carry sha256 and contentSize, and that docs/report.md''s crate section, where it names them, says the same'
  - 'as DETK-0580 (Accepted, Option A) is implemented here: relative_arg rewrites an absolute argument only when it has no whitespace and its parent directory exists, with tests for awk ''/^gene/ {print}'', ''/^g1,/'', sh -c "/usr/bin/env echo hi" and a real absolute path (still rewritten); docs/report.md''s quoted-argument bullet states the rule; a CHANGELOG line under Fixed'
  - 'uv run --group docs mkdocs build --strict passes'
from: [DETK-0001, DETK-0025, DETK-0031, DETK-0032]
scope: [+de_toolkit/crate.py, +tests/report/test_crate.py, +de_toolkit/report.py, +tests/report/test_report_paths.py, +de_toolkit/common.py, +tests/completion/test_completion.py, docs/tools/, docs/report.md, docs/index.md, docs/quickstart.md, docs/concepts.md, docs/api.md, docs/agent-skills.md, docs/example.md, docs/dev/, README.md, new:tests/docs/, +CHANGELOG]
prev: [release/cli-migrate, release/cli-gaps, release/size-factors, release/formula-rename, release/record, release/miller-recipes, release/tutorial-quant, release/tutorial-airway, release/tutorial-covariates, release/help-options, release/tidy-output, release/record-help, release/report-paths, release/example-paths, release/recipe-notes, release/ragged-sheet, release/crate-stdout, release/record-program, DETK-0390, DETK-0580]
issue: 162
visited: cedd7c3
status: done
done: 291c932
---

# Update the docs for the 1.0 CLI

## Implementation plan

- [x] @developer Regenerate the usage blocks from `--help`, add the docs usage test, state the help promise, document exit codes and completion, rewrite what describes the docstring-as-interface pattern, add the how-to-add-a-command note, CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR and build the docs <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-18 on Adam's answer to DETK-0001 (option B); widened
2026-11-19 for DETK-0025 Option B and the CLI gaps. Comes after every
node that changes the CLI (release/record included, which adds a subcommand), and after
the tutorials (DETK-0064), so the CLI pages and the tutorials are written against the same CLI.
The airway walkthrough in `docs/example.md` becomes release/tutorial-airway's.
`docs/formulas.md` belongs to release/formula-migrate and
release/formula-rename.

Widened 2026-11-21: docs/agent-skills.md does not list
`skills/detk/references/covariates.md` (#121); this node owns that page, so
it lists it and a test keeps the list complete. Now also after
release/report-paths (which changes detk-report clean's help and where the
docs say the crate goes), release/example-paths (docs/example/) and
release/recipe-notes (the recipes page and record's failure message).

Widened 2026-11-22 from the release/report-paths review (#134, not
blocking): docs/report.md says no recorded path is absolute, but a path
inside a quoted shell string (`detk-util record -- sh -c "cp /abs/a
/abs/b"`) is one argument and is recorded as typed; the page says so. The
`workdir` `../` chain for a report directory in another tree, and record's
absolute program, are DETK-0390's (Proposed, recommending Option B); this
node documents whichever way it is answered, so it waits on it and on
release/record-program. Also after release/ragged-sheet (docs/concepts.md
on sniffing) and release/crate-stdout (the crate section).

Widened 2026-11-23 from the release/crate-stdout review (#151, not
blocking): crate.py's module docstring says each File of a recorded step
carries `sha256` and `contentSize`, but only the files detk-util record
checksummed do (`../out.csv` and `../stdout` in the review had neither).
A docstring fix, so it is folded in here with a test pinning the rule it
states (`+de_toolkit/crate.py` for the docstring only, `+tests/report/test_crate.py`
for the test). DETK-0390 was accepted with Option B on 2026-11-23, so this
node documents record's program by name; it still comes after
release/record-program, which implements it.

Widened 2026-11-23 from the release/record-program review (#161, not
blocking), under Adam's delegation via the driver session, 2026-11-20
(DETK-0063): on systems where /bin and /usr/bin are separate directories,
`detk-util record -- /bin/cp a b` is still recorded as a relative path
when PATH finds `/usr/bin/cp` first, since the program is written by name
only when PATH resolves it to the same file (DETK-0390); docs/report.md
says so.

Widened 2026-11-23 from the s2 review (#163), under Adam's delegation via
the driver session, 2026-11-20 (DETK-0063): DETK-0580 was accepted with
Option A and is implemented here rather than in a separate node, so the
docs and the code land together. Scope gains the `relative_arg` code in
`de_toolkit/report.py` and its tests (`+de_toolkit/report.py`,
`+tests/report/test_report_paths.py`). The review's Broken pipe nit
(`detk completion bash | head`) is fixed too, in the completion branch of
`de_toolkit/common.py` only, with a test (`+de_toolkit/common.py`,
`+tests/completion/test_completion.py`).
