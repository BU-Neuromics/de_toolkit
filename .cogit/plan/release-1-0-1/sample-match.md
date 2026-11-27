---
kind: task
objective: every command that matches a counts file to a sample information file exits 1 naming the samples found in only one of them, where 1.0.0 fitted the intersection silently; a pure reorder stays allowed (DETK-0600)
acceptance:
  - 'reproduced first as a test: counts with samples 001-008 and a sample sheet where 008 is replaced by 999 (the audit''s case); on v1.0.0 detk-de deseq2 ''counts ~ batch + condition'' exits 0, fits 7 samples and writes results with no warning. After: exit 1, no output file, stderr one line ''detk-de: error: ...'' naming 008 (counts only) and 999 (sample information only)'
  - the same samples in another order exit 0 with results equal to the ordered input's; --strict still requires the same order
  - the check is in the shared matching (CountMatrix), and a test pins it for each command that takes a sample information file (detk-de deseq2 and firth, detk-transform with a design, detk-filter, detk-stats, detk-outlier where they take one); the tutorials and docs examples still run
  - docs/concepts.md says the sample sets must match and detk-util tidy is the explicit way to subset; CHANGELOG 1.0.1 notes the behaviour change (DETK-0600)
from: [DETK-0600]
scope: [de_toolkit/common.py, tests/, +docs/concepts.md, +CHANGELOG]
issue: 178
visited: 557da83
---

# Counts and sample information with different samples are an error

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; it reproduced (exit 0, 7 of 8 samples fitted, baseMean of
feature 000 1261.85 against 1439.35 with all 8, nothing on stderr above INFO).

Today `CountMatrix` (de_toolkit/common.py, about line 600) takes the
intersection of the two sample sets unless `--strict`, and errors only when
fewer than two are shared. DETK-0600 makes a difference in the sets an error
(exit 1, a bad input under DETK-0031) and keeps reordering. `--strict` keeps
its meaning (same order too). Expect tutorials or docs examples whose sample
sheet lists more samples than the counts to need `detk-util tidy` first; fix
them in this node. A sample sheet with extra samples is an error too: Adam's
rule is that the sets match, and subsetting is done explicitly.
