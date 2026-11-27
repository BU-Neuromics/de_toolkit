---
kind: outcome
objective: 'detk 1.0.1 is released: the audit''s silent wrong answers, malformed-count acceptance and provenance gaps fixed and the skill and docs corrected, with no new interface'
acceptance:
  - every 1.0.1 finding of the external AI-readiness audit of 1.0.0 (Codex, 2026-11) is reproduced as a test that fails on 1.0.0 and passes on 1.0.1
  - no command or option is added and the module JSON schema is unchanged (DETK-0001's promise); each behaviour change is a bug fix with a CHANGELOG note (DETK-0600)
  - pip install de_toolkit installs 1.0.1; the v1.0.1 tag, GitHub Release and Zenodo version DOI exist, and CITATION.cff names 1.0.1
from: [DETK-0600]
---

# Release 1.0.1: fixes from the AI-readiness audit

## Implementation plan

- [ ] [Counts and sample information with different samples are an error](release-1-0-1/sample-match.md) <!-- s1 -->
- [ ] [fgsea needs -c when more than one column could rank](release-1-0-1/fgsea-statcol.md) <!-- s2 -->
- [ ] [fgsea records the results file it ranked as an input](release-1-0-1/fgsea-input.md) <!-- s3 -->
- [ ] [Runs that differ only in their files keep separate records](release-1-0-1/run-identity.md) <!-- s4 -->
- [ ] [Test that an enrichment table traces back to its counts and sample information](release-1-0-1/lineage-test.md) <!-- s5 -->
- [ ] [detk-norm cpm rejects malformed counts](release-1-0-1/count-checks.md) <!-- s6 -->
- [ ] [Every command that reads counts runs the count checks](release-1-0-1/count-checks-readers.md) <!-- s7 -->

## Notes
