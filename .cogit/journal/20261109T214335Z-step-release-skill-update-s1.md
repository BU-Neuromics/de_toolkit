---
kind: step
time: 2026-11-09T21:43:35Z
by: DETK/developer
node: release/skill-update
step: s1
branch: node/62-skill-update
verdict: done
commits: [8b464e6]
decisions: []
---

# Done: Add the new commands to the skill and its references, restore `detk-norm library`; open the PR

## Summary

Skill updated for 1.0 (8b464e6): SKILL.md starts from salmon/kallisto/htseq/featureCounts outputs with detk-util gather (airway keeps its Bioconductor counts matrix, which gather cannot apply to; airway.md says so and points to the gather section), recommends detk-norm deseq2, cpm, library, tpm and fpkm with when each fits (no more warning against library; still 'do not pass normalized counts to detk-de deseq2'), notes the FPKM correction, zero-padded IDs kept by the Python commands only, and detk-util annotate for gene symbols after DE (also in airway.md). references/commands.md gains gather, annotate, library, cpm, tpm usage from --help. docs/agent-skills.md and the CHANGELOG skill line updated. tests/skills 19 passed; 9/9 mutations in the new text caught on a copy; full pytest 306 passed, ruff check/format clean, mkdocs --strict builds; npx skills add from the worktree installs an identical copy. Verdict done: all three acceptance points met.

## Artifacts

## Findings

## Questions
