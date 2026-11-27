---
kind: task
objective: detk-enrich fgsea without -c/--statcol is a usage error when the results table has more than one numeric column besides the ID column, and the ranking it used is recorded (DETK-0600)
acceptance:
  - 'reproduced first as a test: on a DESeq2 results table (11 numeric columns) v1.0.0 ''detk-enrich fgsea -o out.csv gene_sets.gmt de.csv'' exits 0 and ranks by condition__treated__padj (the audit''s planted ''up'' set: NES -2.76, padj 0.5; with -c condition__treated__stat NES +2.13, padj 0.0003). After: exit 2, the usage and one line naming the candidate columns and -c, checked before R runs (the test needs no R)'
  - a table with one numeric column besides the ID column ranks by it without -c, as before
  - the module JSON params record the resolved statistic column, ID column and direction (statcol, idcol, ascending; absent in 1.0.0); the schema is unchanged (params is an open object)
  - help's -c line, docs/tools/enrich.md and the skill's commands reference follow; CHANGELOG 1.0.1 notes the behaviour change (DETK-0600)
from: [DETK-0600]
scope: [de_toolkit/enrich.py, tests/enrich/, tests/cli/, +docs/tools/enrich.md, skills/detk/references/commands.md, +CHANGELOG]
issue: 180
visited: 557da83
---

# fgsea needs -c when more than one column could rank

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; it reproduced (exit 0; the log line
"using condition__treated__padj as statistic column"; planted set NES -2.76,
padj 0.5 against +2.13, padj 0.00033 with -c condition__treated__stat). The
numbers come from the audit's synthetic table (8 samples x 180 features, in
/tmp/detk-agent-audit on the driver's machine, not kept); the test should use
a small fixture and assert the exit status and message, not those numbers.

"More than one numeric column could be the ranking" (DETK-0600): numeric
columns other than the ID column, counted after `-i`. Missing `-c` there is a
usage error (exit 2: the command line lacks an argument this input needs,
DETK-0031). In 1.0.0 the module JSON params hold minSize, maxSize, nperm,
multilevel, nproc and rda_fn only; statcol, idcol and ascending are added.
