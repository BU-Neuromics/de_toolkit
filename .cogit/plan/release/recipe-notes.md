---
kind: task
objective: The Miller recipes page and the skill's covariates reference say what a user hits in practice, the z-score and min-max recipes fail on a header-only sheet with a message of their own, and detk-util record names a failed command on one line without a stray quote
acceptance:
  - 'detk-util record''s failure messages (exit status, killed by signal, output file not written) show the whole command on one line: an argument that spans several lines is shown as its first line followed by ... inside its quotes (or as ''...''), so the line no longer ends in a lone quote; a test in tests/util/test_record.py with a multi-line argument asserts the message; the expected output on docs/recipes/covariates.md (the failing recipe, about line 265) is updated and passes under the tutorial harness'
  - docs/recipes/covariates.md and skills/detk/references/covariates.md say that Miller reads a zero-padded number such as 010 or 05 as text, so the recipes reject it as missing or not a number, and what to do about it; the skill's rule 'change only col=, out= and the input file' (and the page's 'change only those two and the file names') also allows, for the constant-column recipe, its column name and value; the page's figure for Miller's stddev on six 7.2s says about 1e-7 (1.07e-7 on Miller 6.22), not about 1.2e-7
  - on a header-only sheet the z-score and min-max recipes exit 1 with a message of their own saying the column has no values (not Miller's 'conditional expression did not evaluate to boolean'), and write no output and no module JSON; a tests/recipes case for every recipe on a header-only sheet asserts exit 1, no output file and, for z-score and min-max, the message; DETK-0070's skill test passes; CHANGELOG under Fixed
scope: [+de_toolkit/util.py, +tests/util/test_record.py, docs/recipes/covariates.md, skills/detk/references/covariates.md, tests/recipes/, +CHANGELOG]
prev: [release/record-help, release/report-paths]
issue: 140
visited: d201819
---

# Recipe page notes and record's failure line

## Implementation plan

- [ ] @developer Show a failed command on one line in detk-util record's messages (multi-line arguments elided), give the z-score and min-max recipes their own header-only message, and add the page and skill notes (zero-padded numbers, the constant recipe's rule, the stddev figure); tests in tests/util and tests/recipes; CHANGELOG; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: run the failing recipe on the page through detk-util record and read its last line, run each recipe on a header-only sheet, and read the skill's covariates reference as an agent would <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-21 from the release/miller-recipes review (#121, notes 1
to 5, none blocking):

1. Miller 6 reads a leading-zero integer (`010`, `05`) as a string, so the
   recipes reject it as "missing or not a number". Safe and loud, but
   unexplained.
2. The skill's rule (references/covariates.md, line 16) to change only
   `col=`, `out=` and the input file does not fit the constant-column
   recipe, where the column name and value change too.
3. The page says Miller's stddev gives "about 1.2e-7" for six 7.2s; on
   Miller 6.22 it is 1.07e-7.
4. On a header-only sheet the z-score and min-max recipes stop with
   Miller's "conditional expression did not evaluate to boolean" (exit 1,
   no output): safe, but not a message of their own.
5. When a recorded command fails, the message ends with `shlex.join(argv)`
   and `cli_main` prints only the first line of the error (`one_line`),
   so a multi-line Miller program shows as a stray `'` (the page's
   expected output shows it). The fix belongs in `run_record` (`util.py`,
   about line 1255), which builds the command text for its messages.

Grouped because they land on the same page and its tests. After
release/record-help (in `util.py` and `tests/util/test_record.py`, record's
help) and release/report-paths (`+` entries in the same two files).
Before release/tutorial-covariates, whose page shows a failing recipe
through detk-util record, release/cli-docs and release/cut.
