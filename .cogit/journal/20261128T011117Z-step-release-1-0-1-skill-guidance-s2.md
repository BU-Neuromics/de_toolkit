---
kind: step
time: 2026-11-28T01:11:17Z
by: DETK/reviewer
node: release-1-0-1/skill-guidance
step: s2
branch: review/skill-guidance
verdict: approve
commits: []
decisions: []
---

# Approved: Review the PR: the reproduction test fails on v1.0.0 and passes here, each acceptance criterion holds, and nothing outside the node's scope changed

## Summary

Approved: reproduction tests fail on v1.0.0 and pass here; every acceptance criterion holds against 1.0.1 behaviour on main; scope respected; CI green incl. test with R (bioconda)

## Artifacts

## Findings

Reproduction: the five new tests in tests/skills/test_skills.py, run against v1.0.0's skill and docs (current test file copied into a v1.0.0 worktree), fail as stated: test_skill_analysis_reads_the_tidy_outputs names SKILL.md:156/164/228/255 reading counts.csv and sample_info.csv after tidy; test_skill_reports_what_tidy_dropped_and_asks, test_skill_states_the_1_0_1_errors and test_quantifier_guidance_leads_with_gene_counts (SKILL.md and quantifiers.md) fail; test_skill_fgsea_names_its_ranking already held on 1.0.0, as the developer said. On this branch tests/skills: 31 passed.
Checked against main's behaviour (local runs of the CLI on this branch, which includes main): a counts/sample-info mismatch exits 1 in detk-stats and names the samples in only one file; detk-util tidy logs 'counts columns lost: N' and 'column data rows lost: N' as the skill quotes and keeps the shared samples in counts order; detk-enrich fgsea without -c on a 3-numeric-column DE table exits 2 and names the candidates; detk-norm cpm exits 1 on a repeated sample header; the skill's list of counts readers that reject repeated headers/IDs matches the CHANGELOG entries for #201 and #218; detk-de deseq2 rounds counts (de.py:341), so 'tximport counts are still fractional; detk-de deseq2 rounds them' is right; a write.csv output with an empty first header reads in detk-stats/filter/tidy.
Statistics: tximport with countsFromAbundance='lengthScaledTPM' is one of the vignette's two bias-corrected count options for use without an offset; the gather-only assumptions (rounding, no sample-specific effective-length offset) are stated in both SKILL.md and docs/tutorials/quantifiers.md; 'can go to it as they are' is gone; featureCounts/htseq-count lead. detk-util record's --tool/--tool-version/-i/-o/-- usage matches its --help.
Scope: changes only in skills/detk, tests/skills, docs/agent-skills.md, docs/tutorials/quantifiers.md, CHANGELOG (1.0.1) and the node's own .cogit records. CI on 2668350: all green, including test with R (bioconda) and docs build (strict).
Nits, not blocking: the tutorial calls lengthScaledTPM 'the form of its output that can be used as a plain counts matrix' (scaledTPM is the other); one long unwrapped line in SKILL.md ('a CSV with a header line: transcript ID, gene ID, as written'). No decisions needed.

## Questions
