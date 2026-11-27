---
kind: task
objective: 'skills/detk follows the 1.0.1 errors and corrects the guidance the audit found wrong: tidy, fgsea''s -c, and the Salmon/kallisto route into DESeq2'
acceptance:
  - 'reproduced first as tests in tests/skills: after the skill''s ''detk-util tidy -o counts_tidy.csv -p sample_info_tidy.csv'', the analysis commands still read counts.csv and sample_info.csv on v1.0.0; after, they read the tidy outputs, and the skill tells the agent to report the samples tidy dropped and ask before going on'
  - every detk-enrich fgsea line in the skill passes -c, and the text says detk exits 2 without it on a DE table (DETK-0600); a sample mismatch is an error to resolve with the user, not to tidy away silently
  - quantifier guidance leads with raw gene-level counts (featureCounts, htseq-count); for salmon or kallisto it documents a tximport path to gene-level counts recorded with detk-util record, and labels the gather-only path's assumptions (rounded estimates, no sample-specific effective-length offset); the line saying salmon and kallisto counts 'can go to it as they are' is gone; docs/tutorials/quantifiers.md agrees
  - the skill tests (DETK-0070) pass; docs/agent-skills.md follows; CHANGELOG 1.0.1
from: [DETK-0600]
scope: [skills/detk/, tests/skills/, +docs/agent-skills.md, +docs/tutorials/quantifiers.md, +CHANGELOG]
prev: [release-1-0-1/sample-match, release-1-0-1/fgsea-statcol]
issue: 214
visited: ac8575b
---

# The agent skill uses tidy's outputs, always passes -c, and leads with gene-level counts

## Implementation plan

- [ ] @developer Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR <!-- s1 -->
- [ ] @reviewer Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed <!-- s2 -->
- [ ] @human Accept <!-- s3 -->

## Notes

From the external AI-readiness audit of 1.0.0 (Codex), planned 2026-11-27 on Adam's direction via the driver session. The plan session reproduced the failure on main at 75aacb3 (= v1.0.0 plus release/cut's CITATION change) before planning it; the
text findings hold on main: SKILL.md runs `detk-util tidy` (line 139), then
`detk-filter ... counts.csv` and `detk-de deseq2 ... sample_info.csv`
(lines 164, 228); line 126 says salmon and kallisto estimates "can go to it
as they are". The skill already tells the agent to always pass -c (line
268); this node adds that detk now enforces it. After sample-match and
fgsea-statcol so it describes their errors.
