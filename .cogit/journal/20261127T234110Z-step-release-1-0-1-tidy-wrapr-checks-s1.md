---
kind: step
time: 2026-11-27T23:41:10Z
by: DETK/developer
node: release-1-0-1/tidy-wrapr-checks
step: s1
branch: node/218-tidy-wrapr-checks
verdict: done
commits: [7e5e626, 3f85668]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

detk-util tidy/tidy-counts/tidy-covs and detk-wrapr run now run check_counts with values=False on the counts as read (DETK-0850): _tidy_main calls check_counts(..., values=False) after read_id_table; wrapr run passes CountMatrixFile(check='ids'). Reproduction tests/util/test_tidy_wrapr_count_checks.py: on v1.0.0, tidy-counts given gene,A,A,B,C with column data A,B,C exits 0 and writes gene,A,B,C; the 9 repeated-header/feature cases (tidy, tidy-counts, tidy-covs, wrapr run) fail there and on main, and pass here; negative counts and zero-depth samples are still accepted by all four. docs/concepts.md (sentence and table) and CHANGELOG 1.0.1 updated. Also fixed tests/common/test_check_counts.py::test_count_matrix_file_finds_a_repeat_the_column_data_drops (subset=True), which fails on main since #198 and #203 merged separately. Full suite 2837 passed (the one failure fixed after), ruff and mkdocs --strict clean.

## Artifacts

## Findings

## Questions
