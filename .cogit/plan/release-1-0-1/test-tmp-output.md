---
kind: task
objective: 'no test writes into the repository or the directory pytest runs from: tests/de/test_de.py::test_R_check_names_nonsense writes R''s output under tmp_path, not ./tmp_output'
acceptance:
  - 'reproduced first: with DESeq2 installed, pytest tests/de on v1.0.0 leaves ./tmp_output/ (counts.csv, script.R, params_*.json, stdout, stderr) in the directory it ran from, from deseq2(..., routput_dir="tmp_output") at tests/de/test_de.py:58; after, it writes under tmp_path and nothing is left'
  - 'a check keeps it so: a session-scoped conftest guard (or a CI step) fails when the suite leaves an untracked file in the repository root, and it is shown to fail on the v1.0.0 test; CHANGELOG 1.0.1 notes it under the tests'
scope: [tests/, +.github/workflows/ci.yml, +CHANGELOG, README.md]
issue: 210
visited: 2bac95c
---

# The test suite leaves the working tree clean

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

README.md added to the scope after review (s2): one sentence in Development on the
guard, as the reviewer suggested; by Adam's delegation via the driver session,
2026-11-20 (DETK-0063), extended to the post-1.0 plan 2026-11-27.

Found by Adam (a `tmp_output/` folder of counts.csv, script.R,
params_*.json, stdout and stderr in the working tree after a test run). The
plan session traced it to `tests/de/test_de.py:58`, unchanged since v1.0.0:
`deseq2(counts_obj, ..., routput_dir="tmp_output")` in
`test_R_check_names_nonsense`, a relative path, so wrapr writes R's files
into the directory pytest runs from. It needs DESeq2, so it only appears
where R and DESeq2 are installed (the R CI job, a developer's machine). The
other `--routput-dir` tests use a temporary directory or a tmp_path cwd. The
guard compares the repository root's untracked files before and after the
session (`git status --porcelain --untracked-files=all`, or the same in
Python), so a future test writing into the root fails in CI.
