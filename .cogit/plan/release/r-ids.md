---
kind: task
objective: Zero-padded IDs and sample names survive the R-backed commands, detk-enrich fgsea and detk-util tidy-counts/tidy-covs (DETK-0015)
acceptance:
  - detk-de deseq2 and firth, detk-transform vst and rlog keep 007 in their output and accept 001-style sample names, shown by an R-gated test that round-trips them
  - detk-enrich fgsea and detk-util tidy-counts/tidy-covs keep 007 and 001, with tests
from: [DETK-0015]
scope: [skills/detk/SKILL.md, de_toolkit/de.py, de_toolkit/transform.py, de_toolkit/wrapr.py, de_toolkit/enrich.py, de_toolkit/util.py, tests/de/, tests/transform/, tests/wrapr/, tests/enrich/, tests/util/, +CHANGELOG]
prev: [release/padded-ids]
issue: 67
visited: 194bd2a
---

# Keep IDs as written through R and the other readers

## Implementation plan

- [x] @developer Read IDs and sample names as text at the R boundary (the R scripts in de.py and transform.py, wrapr's read-back) and in enrich and the tidy commands; R-gated round-trip tests; CHANGELOG; open the PR <!-- s1 -->
- [x] @reviewer Review the PR, including the R-gated tests in CI <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

Planned 2026-11-09 on Adam's answer to DETK-0015 (option 2), from the
reviews of de_toolkit#56. R, like pandas, turns `007` into `7` only when
the whole ID column looks numeric; all-numeric versioned IDs (`1.10`,
`1.1`) collapse to duplicate row names in R.
