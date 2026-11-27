---
kind: task
objective: docs/quickstart.md says, beside its detk-de deseq2 example, that detk takes the Wald coefficients with no independent filtering and no Cook's cutoff, so padj differs from a default DESeq2 vignette run
acceptance:
  - 'reproduced first as a test in tests/docs: the quickstart names neither independent filtering nor Cook''s distance on v1.0.0; after, it names both by the deseq2 example and links docs/tools/de.md, which states the matched results() settings'
scope: [docs/quickstart.md, tests/docs/, +CHANGELOG, +docs/tools/de.md]
issue: 184
visited: 557da83
prev: [DETK-0770]
---

# The quickstart states how detk's DESeq2 differs from a default results() call

## Implementation plan

- [x] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; docs/quickstart.md names neither
independent filtering nor Cook's distance; docs/tools/de.md does (lines
48-61).
