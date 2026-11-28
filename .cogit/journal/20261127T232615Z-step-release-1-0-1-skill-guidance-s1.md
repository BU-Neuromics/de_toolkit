---
kind: step
time: 2026-11-27T23:26:15Z
by: DETK/developer
node: release-1-0-1/skill-guidance
step: s1
branch: node/214-skill-guidance
verdict: done
commits: [9bad70a, 116f8ac]
decisions: []
---

# Done: Write the reproduction test(s) of the first acceptance criterion and confirm they fail on v1.0.0 as stated; then fix, with tests, docs and a CHANGELOG entry under 1.0.1; open the PR

## Summary

Skill reads tidy's outputs (counts_tidy.csv, sample_info_tidy.csv) and has the agent report dropped samples and ask; states the 1.0.1 errors (mismatch exit 1, fgsea without -c exit 2); quantifiers lead with featureCounts/htseq-count gene counts, salmon/kallisto via tximport lengthScaledTPM recorded with detk-util record (run end to end with tximport 1.38.2), gather-only assumptions labelled; reproduction tests in tests/skills fail on v1.0.0; quantifiers tutorial, agent-skills.md, CHANGELOG 1.0.1

## Artifacts

## Findings

## Questions
