---
kind: step
time: 2026-11-20T18:50:23Z
by: DETK/reviewer
node: release/tutorial-quant
step: s2
branch: review/tutorial-quant
verdict: approve
commits: []
decisions: []
---

# Approved: Follow the page as a new user would, run it locally, and check its outputs and the data script

## Summary

Approved at f6f1a02: page reproduces by hand from simulate.py in an empty dir; every shown output checked and mutation-tested; TPM tests and byte-for-byte data test sound; CI green incl. R; tidy workaround honest. 4 wording nits, non-blocking; tidy bugs need a follow-up node (none filed).

## Artifacts

## Findings

Review of s2, at f6f1a02. Approved.

Checked: diff origin/main...f6f1a02 (page, simulate.py and data, test_quantifiers.py, index, nav, CHANGELOG). PR #103 CI is green on f6f1a02, including "test with R (bioconda)" (2143 passed / 21 skipped) and test (python 3.11/3.12/3.13) (2086 passed / 78 skipped on 3.11). In every test job the log shows test_quantifiers.py (3 tests) and test_tutorials.py (1 test, this page) passing, not skipped. docs build (strict) and ruff pass. Locally (3.13): `uv run pytest tests/tutorials` gives 35 passed and 1 skipped. The skip is the runner's own markdown-render test, not this page.

As a new user: I copied only simulate.py into an empty scratch directory, ran `python simulate.py .`, then ran every command on the page by hand. Each output matches the page: the ls listing, the quant.sf head, the gathered matrix's first lines (IDs with version suffixes, fractional NumReads as written), the tidied header without P1, S1's CPM at 1000000.000 (S2 and S6 too), the TPM row equal to salmon's 2320.779735, the summary's basestats, `ls detk_report`, and the crate's ten steps.

As an integration test: I changed `num_rows,300` to 301 on the page, and the page test failed with a clear diff (restored afterwards; the tree is clean). The TPM `...` truncation keeps the float tails out of the comparison. test_quantifiers checks TPM against a direct computation at rtol 1e-12, against salmon's column at atol 5e-6, and checks that simulate.py rewrites the committed tree byte for byte with no extra files. `requires cut awk grep sort` is satisfied on ubuntu runners, so the page can't skip in a plain job.

Claims I checked against the code: gather `--on-mismatch` fill/drop exists. tpm skips the lengths file's header only when the second field isn't a number, so `cut -f 1,3` works. plog's default pseudocount is 1, so `-b 2` is log2(CPM+1). `--color-col=condition` reaches the PCA module JSON (column condition, values ctrl x3, treat x3).

simulate.py: stdlib only. Every draw comes from random.Random(SEED).random(), which is stable across Python versions, with Box-Muller normals and Poisson by inversion or rounded normal. Its docstring says the bytes are checked on Linux and that libm's exp/log/cos come from the platform. The simulation is sensible: lognormal abundance with about 8% unexpressed, 5% up and 5% down at 4x, replicate noise, and about 30% fractional NumReads. It uses one fragment length, so effective lengths are shared and detk's TPM equals salmon's, and the page says so and explains how real data differ.

The workaround is honest. I reproduced both bugs. `tidy -p` writes `,condition,counts` with a zero counts column and no `sample` header. tidy writes no module JSON. The page uses tidy only for the counts, then uses the original sheet, whose samples are all in the counts, so nothing is wrong. It also says outright that tidy is not listed in the crate because it writes no report. It makes no claim that -p works.

DoD: all four bullets are met (page under the harness in every job without R; seeded, committed, byte-for-byte data with 7 x 300 transcripts; checked outputs for gather head, CPM sum and crate steps, plus test_quantifiers TPM; index row, nav, mkdocs strict, CHANGELOG under Added).

Not blocking (wording nits; take them here or in a later pass):
1. "Salmon's EffectiveLength, the length less the fragments that could not fit at its ends" is hard to parse. Something like "the number of positions a fragment could start from: roughly the length less the mean fragment length" would be clearer.
2. "(the column header is skipped as a header)" repeats itself. Suggest "(tpm skips the `Name EffectiveLength` header line)".
3. The page says simulate.py "writes the same files byte for byte each time it runs". The script's own docstring limits that to Linux, so "on Linux" or "on the same platform" would match it.
4. Optional: one sentence in the tidy section saying the sheet needs no tidying here because every sample in it is in the counts. That would make the avoided `-p` visible without naming the bug.

Follow-up for Adam (outside this node; I filed nothing): no issue or node exists yet for the two tidy bugs (`tidy -p` / `tidy-covs` stray zero `counts` column and dropped index header; tidy writes no module JSON, so it is missing from report and crate). tidy's help also lists --report-dir/--no-report although it writes no report, which fits #101 "Options do what their help says". Recommend a 1.0 follow-up node covering all three. When it lands, this page could switch to `-p` and list tidy in the crate.

## Questions
