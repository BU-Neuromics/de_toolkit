---
kind: step
time: 2026-11-28T00:06:25Z
by: DETK/reviewer
node: release-1-0-1/tidy-wrapr-checks
step: s2
branch: node/218-tidy-wrapr-checks
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved at 27d4b01: the reproduction fails on v1.0.0 and main and passes here; both acceptance criteria hold; changes are within scope; all 12 CI checks pass, including test with R (bioconda).

## Artifacts

## Findings

1. Reproduction: tests/util/test_tidy_wrapr_count_checks.py copied onto v1.0.0 and origin/main (bfbc2c1): 9 failed, 4 passed on each (the 9 repeated-header/feature cases for tidy, tidy-counts, tidy-covs and wrapr run; the 4 values=False cases pass, as expected). By hand on v1.0.0 and main, 'detk-util tidy-counts' (and 'tidy') on gene,A,A,B,C with column data A,B,C exits 0 and writes gene,A,B,C. Here it exits 1 with one stderr line: "c.csv: sample 'A' is named more than once in the header (sample columns 1 and 2)". 2. Acceptance 1: tidy/tidy-counts/tidy-covs call check_counts(counts, _source_name(fn), values=False) right after read_id_table, before the column data; wrapr run passes CountMatrixFile(check='ids'), and the test shows the check comes before WrapR is reached. Each case asserts exit 1, no output file, empty stdout and one stderr line naming the duplicate. 3. Acceptance 2: negative counts and a zero-depth sample still pass all four commands (output compared exactly). docs/concepts.md (sentence and table) and CHANGELOG 1.0.1 name the commands, and the 'do not check yet' text from #203 is removed. 4. The tests/common/test_check_counts.py hunk (subset=True) fixes the main-red test: it fails on origin/main and passes here. The comment gives the reason (DETK-0600). 5. Scope: de_toolkit/util.py, de_toolkit/wrapr.py, tests/, docs/concepts.md, CHANGELOG and .cogit records; nothing else changed. 6. Checks: full suite locally 2838 passed, 159 skipped (R not installed); ruff check and format clean; CI 12/12 pass, including test with R (bioconda), 22m44s. 7. Nit, not blocking: CHANGELOG and the test docstring say tidy-covs 'did the same' in 1.0.0. For a repeated header, tidy-covs already exited 1 on v1.0.0 and main, but with a misleading message ('tidy-covs requires that all column IDs in the counts data file exist as rows in the column data file'). It was silent only for a repeated feature ID. The tests are right either way. It could be reworded in passing, or left as is. No decisions needed.

## Questions
