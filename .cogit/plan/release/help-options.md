---
kind: task
objective: detk-transform vst|rlog --rda, detk-stats summary --color-col and detk-transform rlog --blind do what their help says (DETK-0081 Option A)
acceptance:
  - detk-transform vst and rlog with --rda FILE write FILE with saveRDS() of the R result objects, through the same wrapr rda= argument detk-de uses; an R-gated test runs each command end to end and reads FILE back in R (readRDS) to find the DESeq2 object; without --rda nothing extra is written
  - 'detk-stats summary --color-col COL colors the summary''s output plots by COL of the column data: a test runs the command end to end on counts and column data with a two-level column and checks the plot data in the report (module JSON) carries COL''s value per sample and the coloring encoding, and that the CSV output is unchanged; a COL not in the column data is a usage error (exit 2) naming it; if the summary turns out to have no plot it can color, the developer stops and raises a new decision (DETK-0100 or later) for Option B on this option alone'
  - detk-transform rlog --blind takes True or False, case-insensitive, parsed to a bool at parse time; any other value is a usage error (exit 2); --blind False without <design> and <cov_fn> is a usage error (exit 2) naming them; not given, blind stays True; cli-pin pins each case
  - in the R job (test with R (bioconda)), an end-to-end test runs detk-transform rlog on the same counts and column data with --blind True and with --blind False and a design, and the two outputs differ; the module JSON's params record blind and the design used (~ 1 when blind)
  - examples/airway/run.sh, detk-stats summary's help example and the skill keep their usage, now describing what happens; DETK-0010's skill test passes; the CHANGELOG lists the three under Fixed
from: [DETK-0081]
scope: [de_toolkit/transform.py, de_toolkit/stats.py, +de_toolkit/report.py, tests/transform/, tests/stats/, tests/cli/, +CHANGELOG]
prev: [DETK-0081, release/cli-migrate, release/cli-gaps]
issue: 101
visited: f3a014f
status: done
done: a951264
---

# Options do what their help says

## Implementation plan

- [x] @developer Make `--rda` (vst, rlog), `--color-col` (summary) and `--blind` (rlog) do what their help says, each with an end-to-end test, the blind vs non-blind rlog comparison in the R job, cli-pin rows; CHANGELOG under Fixed; open the PR <!-- s1 -->
- [x] @reviewer Review the PR: each option tested end to end, the R job ran the rlog comparison <!-- s2 -->
- [x] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-20 from DETK-0081 (Option A, accepted under Adam's
delegation via the driver session), which the reviewer of
release/cli-migrate raised in step s4. None of the three worked under
docopt either; the argparse migration only made their help explicit.
`--blind False` is a correctness bug: the string reaches `RlogCounts`,
where it is truthy, so the blind design `~ 1` is kept while R reads it as
FALSE. Comes after release/cli-gaps as well as release/cli-migrate: both
rewrite `transform.py`, `stats.py` and tests/cli/, and cli-gaps' exit-code
handler is what the usage errors here go through. Before release/cli-docs,
so the 1.0 docs describe options that work.
