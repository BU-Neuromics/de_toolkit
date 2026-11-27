---
kind: outcome
objective: 'detk 1.0.1 is released: the audit''s silent wrong answers, malformed-count acceptance and provenance gaps fixed and the skill and docs corrected, with no new interface'
acceptance:
  - every 1.0.1 finding of the external AI-readiness audit of 1.0.0 (Codex, 2026-11) is reproduced as a test that fails on 1.0.0 and passes on 1.0.1
  - no command or option is added and the module JSON schema is unchanged (DETK-0001's promise); each behaviour change is a bug fix with a CHANGELOG note (DETK-0600)
  - pip install de_toolkit installs 1.0.1; the v1.0.1 tag, GitHub Release and Zenodo version DOI exist, and CITATION.cff names 1.0.1
from: [DETK-0600]
issue: 186
visited: 557da83
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
- [ ] [The agent skill uses tidy's outputs, always passes -c, and leads with gene-level counts](release-1-0-1/skill-guidance.md) <!-- s8 -->
- [ ] [The quickstart states how detk's DESeq2 differs from a default results() call](release-1-0-1/quickstart-deseq2.md) <!-- s9 -->
- [ ] [R tests skip when an R package they need is missing](release-1-0-1/r-test-skips.md) <!-- s10 -->
- [ ] [Annotate's mapping file in the provenance](release-1-0-1/crate-inputs.md) <!-- s11 -->
- [ ] [detk-outlier entropy runs without -p](release-1-0-1/outlier-entropy-p.md) <!-- s14 -->
- [ ] [detk-outlier shrink takes integer counts](release-1-0-1/outlier-shrink-int.md) <!-- s15 -->
- [ ] [The test suite leaves the working tree clean](release-1-0-1/test-tmp-output.md) <!-- s16 -->
- [ ] [detk-util tidy and detk-wrapr run check sample headers and feature IDs](release-1-0-1/tidy-wrapr-checks.md) <!-- s17 -->
- [ ] [Cut 1.0.1](release-1-0-1/cut.md) <!-- s12 -->
- [ ] @human Accept: 1.0.1 is out <!-- s13 -->

## Notes

Planned 2026-11-27 by the plan session from the external AI-readiness audit
of 1.0.0 (Codex; the report was handed to the session, not committed) on
Adam's direction via the driver session, 2026-11-27: a 1.0.1 patch of bug
fixes and docs with no new interface; additive features go to `release-1-1`.

Every 1.0.1 finding reproduced on main at 75aacb3 before it was planned,
with R 4 from conda (DESeq2, fgsea, logistf) and a second R lacking DESeq2
and logistf:

| Finding | Node | Reproduced |
|---|---|---|
| DESeq2 fits the intersection when sample sets differ | sample-match | yes: exit 0, 7 of 8 samples |
| fgsea without -c ranks by the last numeric column (padj) | fgsea-statcol | yes: exit 0, NES -2.76 for +2.13 |
| fgsea's results file is not a crate input | fgsea-input | yes |
| same params, different files: one record | run-identity | yes (filter -o, deseq2 sample sheet, fgsea -c) |
| CPM accepts duplicate headers and IDs, negatives, zero depth | count-checks, count-checks-readers | yes: all four exit 0 |
| skill: tidy outputs unused; salmon/kallisto as they are | skill-guidance | yes (SKILL.md lines 126, 139-228) |
| quickstart silent on DESeq2 settings | quickstart-deseq2 | yes |
| six R tests fail with Rscript but no DESeq2/logistf | r-test-skips | yes: exactly six |

crate-inputs (#45) moved here from `features`: the audit's "record every
input and side output" is that bug, widened. The method-aware `detk-wrapr
check` (item 5) is folded into `features/wrapr-check-options` (#164), and
the medium findings (fgsea seed, versions, checksums, preflight) are in
`release-1-1`. Every `@human` step of this outcome and its cut is Adam's.

Added 2026-11-27 by a plan session on Adam's direction: three bug fixes
found while 1.0.1 was in progress, each reproduced on a v1.0.0 install
before it was planned. `outlier-entropy-p` (entropy fails without `-p`;
what it should do is DETK-0860, Proposed) and `outlier-shrink-int` (shrink
fails on integer counts) were found by the count-checks-readers session;
`test-tmp-output` (a test writes `./tmp_output/`) by Adam. Cut waits on
each. `tidy-wrapr-checks` (tidy and wrapr run skip the duplicate checks)
follows DETK-0850, on the driver's direction.
